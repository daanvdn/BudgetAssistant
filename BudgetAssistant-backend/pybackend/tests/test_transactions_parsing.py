import csv
# set up all loggers to use the console
import logging
from tempfile import NamedTemporaryFile

from django.db import models
from django.test import TestCase
from faker import Faker
from model_bakery import baker

from pybackend.commons import normalize_counterparty_name_or_account
from pybackend.models import BankAccount, Counterparty, CustomUser, Transaction
from pybackend.transactions_parsing import BelfiusTransactionParser, get_or_create_counterparty

logging.basicConfig(level=logging.INFO)


class CommonFunctionsTest(TestCase):

    def test_get_or_create_counterparty_creates_new(self):
        user = CustomUser.objects.create(username="testuser", password="password")
        counterparty_name = "newcounterparty"
        counterparty_account_number = "123456"
        data = {
            'name': counterparty_name,
            'account_number': counterparty_account_number,
        }

        result  = get_or_create_counterparty(data, user)
        self.assertEqual(result.name, counterparty_name)
        self.assertEqual(result.account_number, counterparty_account_number)
        self.assertIn(user, result.users.all())

    def test_get_or_create_counterparty_existing(self):
        user = CustomUser.objects.create(username="testuser", password="password")
        counterparty_name = "existingcounterparty"
        counterparty_account_number = "123456"
        existing_counterparty = Counterparty.objects.create(name=counterparty_name,
                                                            account_number=counterparty_account_number)
        existing_counterparty.users.add(user)
        data = {
            'name': counterparty_name,
            'account_number': counterparty_account_number,
        }

        result = get_or_create_counterparty(data, user)
        self.assertEqual(result, existing_counterparty)
        self.assertIn(user, result.users.all())





class BelfiusTransactionParserTest(TestCase):
    def setUp(self):
        self.parser = BelfiusTransactionParser()
        self.user = baker.prepare(CustomUser, username="bla", _fill_optional=True)
        self.user.save()

    def generate_csv(self, rows) -> str:
        # use TemporaryFile to create a temp file
        with NamedTemporaryFile('w+', newline='', encoding='utf-8', delete=False) as f:
            writer = csv.writer(f, delimiter=';')
            # first add 12 empty lines
            writer.writerows([[] for _ in range(BelfiusTransactionParser.SKIP_LINES)])
            writer.writerow(BelfiusTransactionParser.HEADERS)
            writer.writerows(rows)
            f.seek(0)
            # return the full path of the file
            return f.name

    def do_test_parse_transactions(self, update_mode: bool):
        # generate 2 random counterparties, 10 random transactions with 5 for each counterparty. Use model_bakery to create the objects
        fake = Faker()

        baker.generators.add(models.CharField, lambda: ' '.join(fake.words(nb=5)))
        baker.generators.add(models.TextField, lambda: ' '.join(fake.words(nb=5)))
        baker.generators.add(models.IntegerField, lambda: fake.random_int(min=1, max=10000))
        baker.generators.add(models.FloatField, lambda: fake.random_number(digits=5, fix_len=True) / 100.0)
        baker.generators.add(models.DecimalField, lambda: fake.pydecimal(left_digits=5, right_digits=2, positive=True))
        baker.generators.add(models.DateField, lambda: fake.date())
        baker.generators.add(models.DateTimeField, lambda: fake.date_time())
        baker.generators.add(models.EmailField, lambda: fake.email())
        baker.generators.add(models.URLField, lambda: fake.url())
        baker.generators.add(models.BooleanField, lambda: fake.boolean())

        generated_numbers = set()

        def unique_random_number():
            while True:
                num = fake.random_number()
                if num not in generated_numbers:
                    generated_numbers.add(num)
                    return num

        counterparty1 = baker.prepare(Counterparty, users=[self.user], _fill_optional=True)
        counterparty1.account_number = BankAccount.normalize_account_number(counterparty1.account_number)
        counterparty1.name = Counterparty.normalize_counterparty(counterparty1.name)
        if update_mode:
            counterparty1.category.save()
            counterparty1.save()
        bank_account1 = baker.prepare(BankAccount, users=[self.user], _fill_optional=True)
        bank_account1.account_number = BankAccount.normalize_account_number(bank_account1.account_number)
        if update_mode:
            bank_account1.save()
        counterparty2 = baker.prepare(Counterparty, users=[self.user], _fill_optional=True)
        counterparty2.account_number = normalize_counterparty_name_or_account(counterparty2.account_number)
        counterparty2.name = normalize_counterparty_name_or_account(counterparty2.name)

        if update_mode:
            counterparty2.category.save()
            counterparty2.save()
        bank_account2 = baker.prepare(BankAccount, users=[self.user], _fill_optional=True)
        bank_account2.account_number = normalize_counterparty_name_or_account(bank_account2.account_number)
        if update_mode:
            bank_account2.save()
        transactions1 = [baker.prepare(Transaction, counterparty=counterparty1, statement_number=str(
            unique_random_number()), transaction_number=str(unique_random_number()), bank_account=bank_account1,
                                       booking_date=fake.date_object(), currency_date=fake.date_object(), _fill_optional=True) for _
                         in
                         range(5)]
        transactions2 = [
            baker.prepare(Transaction, counterparty=counterparty2, statement_number=str(unique_random_number()),
                          transaction_number=str(unique_random_number()), bank_account=bank_account2,
                          booking_date=fake.date_object(), currency_date=fake.date_object(),
                          _fill_optional=True)
            for _ in range(5)]
        all_expected = transactions1 + transactions2
        # set the transaction_id of every transaction using the _create_transaction_id method
        for expected in all_expected:
            expected.transaction_id = Transaction._create_transaction_id(expected.transaction_number,
                                                                         expected.bank_account)
            if update_mode:
                expected.category.save()
                expected.save()

        csv_lines = []

        # add a method to the Transaction class, called to_csv, that returns a list of the transaction fields in the correct order

        def to_csv(self):
            return [
                self.bank_account.account_number,
                self.booking_date,
                self.statement_number,
                self.transaction_number,
                self.counterparty.account_number,
                self.counterparty.name,
                self.counterparty.street_and_number,
                self.counterparty.zip_code_and_city,
                self.transaction,
                self.currency_date,
                str(self.amount),
                self.currency,
                self.bic,
                self.country_code,
                self.communications
            ]

        Transaction.to_csv = lambda self: to_csv(self)

        for expected in all_expected:
            csv_lines.append(expected.to_csv())

        csv_file = self.generate_csv(csv_lines)
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            lines = f.readlines()
            parse_result = self.parser.parse(lines, self.user)
            all_actual = parse_result.transactions
            self.assertEqual(len(all_actual), 10)
            for i in range(10):
                expected = all_expected[i]
                actual = all_actual[i]
                self.assertIsNotNone(expected.counterparty)
                self.assertIsNotNone(expected.counterparty.account_number)
                self.assertEqual(actual.counterparty.account_number, expected.counterparty.account_number)
                self.assertIsNotNone(expected.counterparty.name)
                self.assertEqual(actual.counterparty.name, expected.counterparty.name)
                self.assertIsNotNone(expected.counterparty.street_and_number)
                self.assertEqual(actual.counterparty.street_and_number, expected.counterparty.street_and_number)
                self.assertIsNotNone(expected.counterparty.zip_code_and_city)
                self.assertEqual(actual.counterparty.zip_code_and_city, expected.counterparty.zip_code_and_city)
                self.assertIsNotNone(expected.bank_account)
                self.assertIsNotNone(expected.bank_account.account_number)
                self.assertEqual(actual.bank_account.account_number, expected.bank_account.account_number)
                self.assertIsNotNone(expected.booking_date)
                self.assertEqual(actual.booking_date, expected.booking_date)
                self.assertIsNotNone(expected.statement_number)
                self.assertEqual(actual.statement_number, expected.statement_number)
                self.assertIsNotNone(expected.transaction_number)
                self.assertEqual(actual.transaction_number, expected.transaction_number)
                self.assertIsNotNone(expected.transaction)
                self.assertEqual(actual.transaction, expected.transaction)
                self.assertIsNotNone(expected.currency_date)
                self.assertEqual(actual.currency_date, expected.currency_date)
                self.assertIsNotNone(expected.amount)
                self.assertEqual(actual.amount, expected.amount)
                self.assertIsNotNone(expected.currency)
                self.assertEqual(actual.currency, expected.currency)
                self.assertIsNotNone(expected.bic)
                self.assertEqual(actual.bic, expected.bic)
                self.assertIsNotNone(expected.country_code)
                self.assertEqual(actual.country_code, expected.country_code)
                self.assertIsNotNone(expected.communications)
                self.assertEqual(actual.communications, expected.communications)

    def test_parse_transactions_insert_mode(self):
        self.do_test_parse_transactions(False)

    def test_parse_transactions_update_mode(self):
        self.do_test_parse_transactions(True)
