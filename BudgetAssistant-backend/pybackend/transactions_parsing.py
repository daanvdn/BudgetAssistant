import csv
import dataclasses
import logging
import traceback
from abc import ABC, abstractmethod
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.exceptions import ObjectDoesNotExist
from django.utils.dateparse import parse_date
from silk.profiling.profiler import silk_profile

from pybackend.models import BankAccount, Counterparty, CustomUser, Transaction
from pybackend.serializers import CounterpartySerializer, TransactionSerializer

logger = logging.getLogger(__name__)



def get_or_create_counterparty(data: Dict, user: CustomUser) -> Counterparty:
    try:
        counterparty = Counterparty.objects.get(name=data['name'])
        serializer = CounterpartySerializer(counterparty, data=data)
        if serializer.is_valid(raise_exception=True):
            save = serializer.save()
            save.users.add(user)
            return save
    except ObjectDoesNotExist:
        logger.info(f"Counterparty with name {data['name']} does not exist. Creating it")
        serializer = CounterpartySerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            save = serializer.save()
            save.users.add(user)
            return save



def get_or_create_transaction(data: Dict) -> tuple[Transaction, bool]:
    def handle_counterparty_data(transaction_data:dict) -> dict:
        counterparty = transaction_data.pop('counterparty', None)
        if counterparty:
            if isinstance(counterparty, dict):
                transaction_data['counterparty_id'] = counterparty['name']
            elif isinstance(counterparty, Counterparty):
                transaction_data['counterparty_id'] = counterparty.name
        if 'counterparty_id' not in transaction_data:
            raise ValueError("counterparty_id is required")
        return transaction_data

    try:
        transaction = Transaction.objects.get(transaction_id=data['transaction_id'])
        data = handle_counterparty_data(data)
        serializer = TransactionSerializer(transaction, data=data)
        if serializer.is_valid(raise_exception=True):
            return serializer.save(), False
    except ObjectDoesNotExist:
        logger.info(f"Transaction with id  {data['transaction_id']} does not exist. Creating it")
        data = handle_counterparty_data(data)
        serializer = TransactionSerializer(data=data)
        try:
            if serializer.is_valid(raise_exception=True):
                return serializer.save(), True
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error creating transaction with id {data['transaction_id']}")
            logger.error(serializer.errors)
            raise ValueError(f"Error creating transaction with id {data['transaction_id']}: {str(serializer.errors)}")


@dataclasses.dataclass(frozen=True)
class ParseResult:
    transactions: List[Transaction]
    created: int
    ignored: int

class AbstractTransactionParser(ABC):
    @abstractmethod
    def parse(self, lines:  List[str], user: CustomUser) -> ParseResult:
        ...

    @abstractmethod
    def get_type(self) -> str:
        ...


class BelfiusTransactionParser(AbstractTransactionParser):
    HEADERS = [
        "Rekening", "Boekingsdatum", "Rekeninguittrekselnummer", "Transactienummer",
        "Rekening tegenpartij", "Naam tegenpartij bevat", "Straat en nummer",
        "Postcode en plaats", "Transactie", "Valutadatum", "Bedrag", "Devies",
        "BIC", "Landcode", "Mededelingen"
    ]
    COLUMN_COUNT = len(HEADERS)
    SKIP_LINES = 12

    def __init__(self):
        ...

    def parse(self, lines: List[str], user: CustomUser) -> ParseResult:
        bank_account_numbers, counterparty_data, rows_data = self.read_csv_step1(lines)

        bank_accounts = self.handle_bankaccounts(bank_account_numbers, user)

        counterparties = self.handle_counterparties(counterparty_data, user)

        # Second pass: prepare transaction objects
        all_created, all_ignored, new_transaction_objects, transactions = self.prepare_transaction_objects(
            bank_accounts, counterparties, rows_data)

        # Bulk create new transactions
        self.bulk_create_transactions(new_transaction_objects)

        logger.info(f"Parsed {len(transactions)} transactions")
        return ParseResult(transactions, all_created, all_ignored)

    @silk_profile(name='BelfiusTransactionParser.bulk_create_transactions')
    def bulk_create_transactions(self, new_transaction_objects):
        if new_transaction_objects:
            Transaction.objects.bulk_create(new_transaction_objects)
        # Bulk update existing transactions
        # for transaction, serializer in transactions_to_update:
        #     serializer.save()

    @silk_profile(name='BelfiusTransactionParser.prepare_transaction_objects')
    def prepare_transaction_objects(self, bank_accounts, counterparties, rows_data):
        transactions = []
        # Prepare raw transaction data in parallel
        transaction_data_list = []
        def _build_transaction_data(row):
            acct = bank_accounts[row["Rekening"]]
            cp = counterparties[row["Naam tegenpartij bevat"]]
            txn_num = row["Transactienummer"]
            txn_id = Transaction._create_transaction_id(txn_num, acct)
            return {
                'transaction_id': txn_id,
                'bank_account': acct,
                'booking_date': row["Boekingsdatum"],
                'statement_number': row["Rekeninguittrekselnummer"],
                'transaction_number': txn_num,
                'counterparty': cp,
                'transaction': row.get("Transactie", ''),
                'currency_date': parse_date(row["Valutadatum"]),
                'amount': float(row["Bedrag"]),
                'currency': row["Devies"],
                'bic': row.get("BIC", ''),
                'country_code': row.get("Landcode", ''),
                'communications': row.get("Mededelingen", '')
            }
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(_build_transaction_data, r) for r in rows_data]
            for f in as_completed(futures):
                transaction_data_list.append(f.result())
        # Check which transactions already exist
        transaction_ids = [data['transaction_id'] for data in transaction_data_list]
        existing_transactions = {
            t.transaction_id: t for t in Transaction.objects.filter(transaction_id__in=transaction_ids)
        }
        existing_transaction_ids = set(existing_transactions.keys())
        # Prepare transactions for bulk operations
        # transactions_to_update = []
        new_transaction_objects = []
        all_created = 0
        all_ignored = 0
        # Process transactions in parallel
        def _process_data(data_item):
            txn_id = data_item['transaction_id']
            orig = self.handle_counterparty_data(data_item.copy())
            if txn_id in existing_transaction_ids:
                logger.info(f"Transaction with id {txn_id} already exists. It will be ignored.")
                return None, False
            # Directly build transaction instance without serializer
            txn = Transaction(
                transaction_id=orig['transaction_id'],
                bank_account=orig['bank_account'],
                booking_date=orig['booking_date'],
                statement_number=orig['statement_number'],
                transaction_number=orig['transaction_number'],
                counterparty=orig['counterparty_id'],
                transaction=orig.get('transaction', ''),
                currency_date=orig['currency_date'],
                amount=orig['amount'],
                currency=orig['currency'],
                bic=orig.get('bic', ''),
                country_code=orig['country_code'],
                communications=orig.get('communications', '')
            )
            return txn, True

        with ThreadPoolExecutor() as executor:
            future_to_data = {executor.submit(_process_data, data): data for data in transaction_data_list}
            for future in as_completed(future_to_data):
                txn_obj, created = future.result()
                if txn_obj:
                    new_transaction_objects.append(txn_obj)
                    transactions.append(txn_obj)
                if created:
                    all_created += 1
                else:
                    all_ignored += 1

        return all_created, all_ignored, new_transaction_objects, transactions

    @silk_profile(name='BelfiusTransactionParser.handle_counterparties')
    def handle_counterparties(self, counterparty_data, user):
        # Batch process counterparties - fetch existing counterparties first
        normalized_counterparty_names = [Counterparty.normalize_counterparty(name) for name in counterparty_data.keys()]
        existing_counterparties = {
            cp.name: cp for cp in Counterparty.objects.filter(name__in=normalized_counterparty_names)
        }
        # Create any missing counterparties and build the complete mapping
        counterparties = {}  # name -> Counterparty object
        new_counterparties = []
        for name, (account_number, street_and_number, zip_code_and_city) in counterparty_data.items():
            normalized_name = Counterparty.normalize_counterparty(name)
            if normalized_name in existing_counterparties:
                counterparty = existing_counterparties[normalized_name]
                # Ensure user is associated with this counterparty
                if user not in counterparty.users.all():
                    counterparty.users.add(user)
            else:
                # Create new counterparty
                counterparty = Counterparty(
                    name=normalized_name,
                    account_number=account_number,
                    street_and_number=street_and_number,
                    zip_code_and_city=zip_code_and_city
                )
                new_counterparties.append(counterparty)

            counterparties[name] = counterparty
        # Bulk create new counterparties
        if new_counterparties:
            Counterparty.objects.bulk_create(new_counterparties)
            # Add user to all new counterparties
            for counterparty in new_counterparties:
                counterparty.users.add(user)
        return counterparties

    @silk_profile(name='BelfiusTransactionParser.handle_bankaccounts')
    def handle_bankaccounts(self, bank_account_numbers, user):
        # Batch process bank accounts - fetch existing accounts first
        normalized_account_numbers = [BankAccount.normalize_account_number(acc) for acc in bank_account_numbers]
        existing_bank_accounts = {
            acc.account_number: acc for acc in BankAccount.objects.filter(account_number__in=normalized_account_numbers)
        }
        # Create any missing bank accounts and build the complete mapping
        bank_accounts = {}  # account_number -> BankAccount object
        new_bank_accounts = []
        for account_number in bank_account_numbers:
            normalized = BankAccount.normalize_account_number(account_number)
            if normalized in existing_bank_accounts:
                bank_account = existing_bank_accounts[normalized]
                # Ensure user is associated with this account
                if user not in bank_account.users.all():
                    bank_account.users.add(user)
            else:
                # Create new bank account
                bank_account = BankAccount(account_number=normalized)
                new_bank_accounts.append(bank_account)

            bank_accounts[account_number] = bank_account
        # Bulk create new bank accounts
        if new_bank_accounts:
            BankAccount.objects.bulk_create(new_bank_accounts)
            # Add user to all new accounts
            for bank_account in new_bank_accounts:
                bank_account.users.add(user)
        return bank_accounts

    @silk_profile(name='BelfiusTransactionParser.read_csv_step1')
    def read_csv_step1(self, lines):
        # skip the first 12 lines
        lines = lines[self.SKIP_LINES:]
        # skip one more line
        reader = csv.DictReader(f=lines, delimiter=';')
        actual_field_names = reader.fieldnames
        # check actual field names and expected field names are the same
        if len(actual_field_names) != len(self.HEADERS) and set(actual_field_names) != set(self.HEADERS):
            raise ValueError(f"Expected headers: {self.HEADERS}, but got: {actual_field_names}")
        # First pass: collect all data from CSV
        rows_data = []
        bank_account_numbers = set()
        counterparty_data = {}  # name -> (account_number, street_and_number, zip_code_and_city)
        for row in reader:
            bank_account_number = row["Rekening"]
            bank_account_numbers.add(bank_account_number)

            counterparty_str = row["Naam tegenpartij bevat"]
            counterparty_account = row["Rekening tegenpartij"]
            street_and_number = row["Straat en nummer"]
            zip_code_and_city = row["Postcode en plaats"]

            # Store counterparty data for batch processing
            counterparty_data[counterparty_str] = (counterparty_account, street_and_number, zip_code_and_city)

            # Store row data for later processing
            rows_data.append(row)
        return bank_account_numbers, counterparty_data, rows_data

    def get_type(self):
        return "BELFIUS"

    def handle_counterparty_data(self, transaction_data: dict) -> dict:
        # If counterparty is already an object, convert it to counterparty_id for the serializer
        if 'counterparty' in transaction_data and isinstance(transaction_data['counterparty'], Counterparty):
            counterparty = transaction_data.pop('counterparty')
            transaction_data['counterparty_id'] = counterparty
            return transaction_data

        # If counterparty_id is provided but not counterparty, keep it as is
        if 'counterparty_id' in transaction_data:
            return transaction_data

        # If neither counterparty nor counterparty_id is provided, raise an error
        if 'counterparty' not in transaction_data:
            raise ValueError("counterparty or counterparty_id is required")

        # If counterparty is not a Counterparty object, try to convert it
        counterparty = transaction_data.pop('counterparty')
        if isinstance(counterparty, dict) and 'name' in counterparty:
            try:
                counterparty_obj = Counterparty.objects.get(name=counterparty['name'])
                transaction_data['counterparty_id'] = counterparty_obj
            except Counterparty.DoesNotExist:
                raise ValueError(f"Counterparty with name {counterparty['name']} does not exist")
        else:
            try:
                counterparty_obj = Counterparty.objects.get(name=counterparty)
                transaction_data['counterparty_id'] = counterparty_obj
            except Counterparty.DoesNotExist:
                raise ValueError(f"Counterparty with name {counterparty} does not exist")

        return transaction_data
