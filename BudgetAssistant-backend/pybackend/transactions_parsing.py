import csv
import dataclasses
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from django.core.exceptions import ObjectDoesNotExist
from django.utils.dateparse import parse_date

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



def get_or_create_transaction(data: Dict) -> Tuple[Transaction, bool]:

    try:
        transaction = Transaction.objects.get(transaction_id=data['transaction_id'])
        serializer = TransactionSerializer(transaction, data=data)
        if serializer.is_valid(raise_exception=True):
            return serializer.save(), False
    except ObjectDoesNotExist:
        logger.info(f"Transaction with id  {data['transaction_id']} does not exist. Creating it")
        serializer = TransactionSerializer(data=data)
        if serializer.is_valid(raise_exception=False):
            return serializer.save(), True
        else:
            logger.error(f"Error creating transaction with id {data['transaction_id']}")
            logger.error(serializer.errors)
            raise ValueError(f"Error creating transaction with id {data['transaction_id']}: {str(serializer.errors)}")


@dataclasses.dataclass(frozen=True)
class ParseResult:
    transactions: List[Transaction]
    created: int
    updated: int

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

        # skip the first 12 lines
        lines = lines[self.SKIP_LINES:]
        # skip one more line
        reader = csv.DictReader(f=lines, delimiter=';')
        actual_field_names = reader.fieldnames
        # check actual field names and expected field names are the same
        if len(actual_field_names) != len(self.HEADERS) and set(actual_field_names) != set(self.HEADERS):
            raise ValueError(f"Expected headers: {self.HEADERS}, but got: {actual_field_names}")
        transactions = []
        all_created = 0
        all_updated = 0
        for row in reader:
            bank_account = row["Rekening"]
            bank_account: BankAccount = BankAccount.objects.get_or_create_bank_account(bank_account, user)
            counterparty_str = row["Naam tegenpartij bevat"]
            counterparty_account = row["Rekening tegenpartij"]
            street_and_number = row["Straat en nummer"]
            zip_code_and_city = row["Postcode en plaats"]

            counterparty = get_or_create_counterparty(
                {'name': counterparty_str, 'account_number': counterparty_account,
                 'street_and_number': street_and_number, 'zip_code_and_city': zip_code_and_city}, user)
            booking_date = row["Boekingsdatum"]
            statement_number = row["Rekeninguittrekselnummer"]
            transaction_number = row["Transactienummer"]
            transaction = row["Transactie"]
            currency_date = row["Valutadatum"]
            amount = row["Bedrag"]
            currency = row["Devies"]
            bic = row["BIC"]
            country_code = row["Landcode"]
            communications = row["Mededelingen"]

            transaction_id = Transaction._create_transaction_id(transaction_number, bank_account)
            data = {
                'transaction_id': transaction_id,
                'bank_account': bank_account,
                'booking_date': booking_date,
                'statement_number': statement_number,
                'transaction_number': transaction_number,
                'counterparty': counterparty,
                'transaction': transaction,
                'currency_date': parse_date(currency_date),
                'amount': float(amount),
                'currency': currency,
                'bic': bic,
                'country_code': country_code,
                'communications': communications,
                'street_and_number': street_and_number,
                'zip_code_and_city': zip_code_and_city
            }
            transaction, created = get_or_create_transaction(data)
            transactions.append(transaction)
            if created:
                all_created += 1
            else:
                all_updated += 1

        logger.info(f"Parsed {len(transactions)} transactions")
        return ParseResult(transactions, all_created, all_updated)



    def get_type(self):
        return "BELFIUS"