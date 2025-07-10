import importlib.resources as pkg_resources
import json
import unittest
from datetime import datetime, timezone

from django.db.models import QuerySet
from django.test import TestCase
from model_bakery import baker
from rest_framework import serializers

from pybackend.commons import TransactionTypeEnum
from pybackend.dto import FailedOperationResponse, PageTransactionsRequest, PageTransactionsRequestSerializer, \
    SuccessfulOperationResponse, \
    TransactionsPage
from pybackend.models import BankAccount, BudgetTree, Category, Counterparty, CustomUser, \
    Transaction
from pybackend.providers import BudgetTreeProvider
from pybackend.serializers import TransactionSerializer
from pybackend.services import BankAccountsService, BudgetTreeService, TransactionsService
from pybackend.transactions_parsing import BelfiusTransactionParser


class BankAccountsServiceTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(username='testuser', password='password123')
        self.service = BankAccountsService()

    def test_get_or_create_bank_account_creates_new_account(self):
        account_number = '123456789'
        bank_account = self.service.get_or_create_bank_account(account_number, self.user)
        self.assertEqual(bank_account.account_number, account_number)
        self.assertIn(self.user, bank_account.users.all())

    def test_get_or_create_bank_account_adds_user_to_existing_account(self):
        account_number = '123456789'
        existing_account = BankAccount.objects.create(account_number=account_number)
        bank_account = self.service.get_or_create_bank_account(account_number, self.user)
        self.assertEqual(bank_account, existing_account)
        self.assertIn(self.user, bank_account.users.all())

    def test_find_distinct_by_users_contains_returns_accounts(self):
        account_number = '123456789'
        bank_account = BankAccount.objects.create(account_number=account_number)
        bank_account.users.add(self.user)
        accounts = self.service.find_distinct_by_users_contains(self.user)
        self.assertIn(bank_account, accounts)

    def test_get_bank_account_returns_account(self):
        account_number = '123456789'
        bank_account = BankAccount.objects.create(account_number=account_number)
        retrieved_account = self.service.get_bank_account(account_number)
        self.assertEqual(retrieved_account, bank_account)

    def test_get_bank_account_raises_error_if_not_exist(self):
        with self.assertRaises(ValueError) as context:
            self.service.get_bank_account('nonexistent')
        self.assertEqual(str(context.exception), 'Bank account with account number nonexistent does not exist')


class TransactionsServiceTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(username='testuser', password='password123')
        self.bank_account = BankAccount.objects.create(account_number='123456789')
        self.category = Category.objects.create(name='Test Category', type=TransactionTypeEnum.EXPENSES)
        self.counterparty = Counterparty.objects.create(name='Test Counterparty', account_number='987654321')
        self.service = TransactionsService()

    def test_page_transactions_to_manually_review_returns_transactions(self):
        account_number='123456789'
        bank_account = baker.make(BankAccount, account_number=account_number)
        transaction1 = baker.make(Transaction, bank_account=bank_account, amount=-10.0, manually_assigned_category=False, category=None)
        transaction2 = baker.make(Transaction, bank_account=bank_account, amount=-10.0, manually_assigned_category=False, category=None)
        transaction3 = baker.make(Transaction, bank_account=bank_account, amount=-10.0, manually_assigned_category=False, category=None)
        transaction4 = baker.make(Transaction, bank_account=bank_account, amount=10.0, manually_assigned_category=False, category=None)
        response: TransactionsPage= self.service.page_transactions_to_manually_review(
            bank_account=bank_account.account_number, page=1, size=10, sort_order='asc', sort_property='amount',
            transaction_type=TransactionTypeEnum.EXPENSES
        )

        self.assertEqual(response.total_elements, 3)
        self.assertEqual(response.number, 1)
        self.assertEqual(response.size, 3)
        self.assertIn(transaction1, response.content)
        self.assertIn(transaction2, response.content)
        self.assertIn(transaction3, response.content)
        self.assertNotIn(transaction4, response.content)

    def test_page_transactions_to_manually_review_returns_empty_if_no_transactions(self):
        response: TransactionsPage = self.service.page_transactions_to_manually_review(
            bank_account='123456789', page=1, size=10, sort_order='asc', sort_property='transaction_id',
            transaction_type=TransactionTypeEnum.EXPENSES
        )
        #response.content should be an empty QuerySet
        self.assertIsInstance(response.content, QuerySet)
        self.assertFalse(response.content.exists())
        self.assertEqual(response.number, 1)
        self.assertEqual(response.total_elements, 0)
        self.assertEqual(response.size, 0)

    def test_count_transactions_to_manually_review_returns_count(self):
        account_number='123456789'
        bank_account = baker.make(BankAccount, account_number=account_number)
        baker.make(Transaction, bank_account=bank_account, amount=-10.0, manually_assigned_category=False, category=None)
        baker.make(Transaction, bank_account=bank_account, amount=-10.0, manually_assigned_category=False, category=None)
        baker.make(Transaction, bank_account=bank_account, amount=-10.0, manually_assigned_category=False, category=None)
        baker.make(Transaction, bank_account=bank_account, amount=10.0, manually_assigned_category=False, category=None)
        count = self.service.count_transactions_to_manually_review(bank_account=bank_account.account_number)
        self.assertEqual(count, 4)

    def test_count_transactions_to_manually_review_returns_zero_if_no_transactions(self):
        count = self.service.count_transactions_to_manually_review(bank_account='123456789')
        self.assertEqual(count, 0)

    def test_save_transaction_updates_existing_transaction(self):
        #create transaction and save
        transaction = baker.make(Transaction, manually_assigned_category=False)
        #modify transaction, without saving
        transaction.manually_assigned_category = True
        #save transaction
        response: SuccessfulOperationResponse = self.service.save_transaction(TransactionSerializer(transaction).data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.message, f"Transaction with id '{transaction.transaction_id}' updated successfully")

    def test_save_transaction_returns_error_if_transaction_not_exist(self):
        transaction_json = {
            'transaction_id': 'nonexistent', 'bank_account': '123456789', 'booking_date': '2023-01-01',
            'statement_number': '1', 'counterparty': 'Test', 'transaction_number': '1', 'transaction': 'Test',
            'currency_date': '2023-01-01', 'amount': 100.0, 'currency': 'USD', 'bic': 'BIC', 'country_code': 'US',
            'communications': 'Test', 'category': None, 'manually_assigned_category': False
        }
        response: FailedOperationResponse = self.service.save_transaction(transaction_json)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.error, "Transaction with id 'nonexistent' does not exist in db!")

    def test_upload_transactions(self):
        file_name = "belfius_transactions.csv"
        with pkg_resources.path('pybackend.tests.resources',
                                file_name) as file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                parse_result = TransactionsService().upload_transactions(lines, self.user, datetime.now(),
                                                                         BelfiusTransactionParser(), file_name)
                self.assertIsNotNone(parse_result)
                self.assertEqual(parse_result.created, 10)
                self.assertEqual(parse_result.ignored, 0)
                #check if transactions are saved in db
                transactions = Transaction.objects.all()
                self.assertEqual(len(transactions), 10)

    def test_page_transactions_pagination(self):
        # Create a bank account and associate it with the user
        bank_account = baker.make(BankAccount, account_number='test_account')
        bank_account.users.add(self.user)

        # Create 99 transactions using baker and store them in a list
        transactions = []
        for i in range(99):
            transaction = baker.make(
                Transaction, 
                bank_account=bank_account, 
                amount=-10.0, 
                manually_assigned_category=False, 
                category=None
            )
            transactions.append(transaction)

        # Sort transactions by transaction_id to match the sorting in the service
        transactions.sort(key=lambda t: t.transaction_id)

        # Check all pages from 1 to 10
        for page_num in range(1, 11):
            # Call page_transactions with the current page number
            response_page = self.service.page_transactions(
                query=None, 
                page=page_num, 
                size=10, 
                sort_order='asc', 
                sort_property='transaction_id',
                user=self.user
            )

            # Verify total_elements is always 99
            self.assertEqual(response_page.total_elements, 99)

            # Verify page number matches the requested page
            self.assertEqual(response_page.number, page_num)

            # Calculate expected content size (10 for pages 1-9, 9 for page 10)
            expected_size = 9 if page_num == 10 else 10
            self.assertEqual(len(response_page.content), expected_size)

            # Calculate the start and end indices for the expected transactions
            start_idx = (page_num - 1) * 10
            end_idx = min(start_idx + 10, 99)
            expected_transactions = transactions[start_idx:end_idx]

            # Verify that the content matches the expected transactions
            for i, transaction in enumerate(response_page.content):
                self.assertEqual(transaction, expected_transactions[i], 
                                f"Transaction mismatch on page {page_num}, position {i}")

        # Additional verification for first and last page
        # Get the first page
        response_page1 = self.service.page_transactions(
            query=None, 
            page=1, 
            size=10, 
            sort_order='asc', 
            sort_property='transaction_id',
            user=self.user
        )

        # Verify first page has 10 transactions
        self.assertEqual(len(response_page1.content), 10)

        # Get the last page (page 10)
        response_page10 = self.service.page_transactions(
            query=None, 
            page=10, 
            size=10, 
            sort_order='asc', 
            sort_property='transaction_id',
            user=self.user
        )

        # Verify last page has 9 transactions
        self.assertEqual(len(response_page10.content), 9)

    def test_page_transactions_upload_timestamp(self):
        # Create a bank account and associate it with the user
        bank_account = baker.make(BankAccount, account_number='test_account')
        bank_account.users.add(self.user)
        d = datetime(2025, 5, 1, 15, 53, 37, 170434, tzinfo=timezone.utc)

        def serialize_deserialize_datetime(dt: datetime) -> datetime:
            data = serializers.DateTimeField().to_representation(dt)
            #convert data back to datetime
            return serializers.DateTimeField().to_internal_value(data)
        serialized_d = serialize_deserialize_datetime(d)
        # Create 10 transactions with a first upload timestamp
        upload_timestamp_1 = serialize_deserialize_datetime(datetime.now())

        transactions_1 = baker.make(
                Transaction,
                _quantity=10,
                bank_account=bank_account,
                amount=-10.0,
                manually_assigned_category=False,
                category=None,
                upload_timestamp=upload_timestamp_1


            )
        # Create 10 transactions with a second upload timestamp
        upload_timestamp_2 = serialize_deserialize_datetime(datetime.now())
        transaction_2 = baker.make(
                Transaction,
                _quantity=10,
                bank_account=bank_account,
                amount=-10.0,
                manually_assigned_category=False,
                category=None,
                upload_timestamp=upload_timestamp_2


            )
        page_transactions_request_json = {
            'page': 0,
            'query': {
                'transaction_type': 'BOTH',
                'upload_timestamp': serializers.DateTimeField().to_representation(upload_timestamp_1)
            },
            'size': 10,
            'sort_order': 'desc',
            'sort_property': 'booking_date'
        }
        serializer = PageTransactionsRequestSerializer(data=page_transactions_request_json)
        serializer.is_valid(raise_exception=True)

        page_transactions_request= PageTransactionsRequest(**serializer.validated_data)
        # Call page_transactions with the current page number
        response_page = self.service.page_transactions(
            query=page_transactions_request.query,
            page=page_transactions_request.page,
            size=page_transactions_request.size,
            sort_order=page_transactions_request.sort_order,
            sort_property=page_transactions_request.sort_property,
            user=self.user
        )

        # Verify total_elements is always 10
        self.assertEqual(response_page.total_elements, 10)

        # Verify page number matches the requested page
        self.assertEqual(response_page.number, 1)

        # Verify that the content matches the expected transactions
        for i, transaction in enumerate(response_page.content):
            self.assertEqual(transaction.upload_timestamp, upload_timestamp_1,
                            f"Transaction mismatch on page {1}, position {i}")
        #assert that response_page.content is equal to transactions_1, regardless of the order
        self.assertEqual(set(response_page.content), set(transactions_1))


class BudgetTreeServiceTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(username='testuser', password='password')
        self.bank_account = BankAccount.objects.create(account_number='1234567890')
        self.service = BudgetTreeService()

    @unittest.skip("Test is not implemented")
    def test_find_or_create_budget_creates_new_budget_tree(self):
        response = self.service.find_or_create_budget(self.bank_account.account_number)
        self.assertEqual(response.status_code, 200)
        actual_budget_tree = BudgetTree.objects.get(bank_account=self.bank_account)
        expected_budget_tree = BudgetTreeProvider().provide(self.bank_account)
        self.assertIsNotNone(expected_budget_tree)
        self.assertIsNotNone(actual_budget_tree)
        self.assertEqual(actual_budget_tree, expected_budget_tree)
        self.assertEqual(actual_budget_tree.bank_account, self.bank_account)

    @unittest.skip("Test is not implemented")
    def test_find_or_create_budget_returns_existing_budget_tree(self):
        expected = BudgetTreeProvider().provide(self.bank_account)
        response = self.service.find_or_create_budget(self.bank_account.account_number)
        self.assertEqual(response.status_code, 200)
        actual = BudgetTree.objects.filter(bank_account=self.bank_account)
        self.assertIsNotNone(actual)
        self.assertEqual(len(actual), 1)
        actual = actual.first()
        self.assertEqual(expected.bank_account, self.bank_account)
        self.assertEqual(actual, expected)

    @unittest.skip("Test is not implemented")
    def test_find_or_create_budget_handles_nonexistent_bank_account(self):
        response = self.service.find_or_create_budget('nonexistent_account')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', json.loads(response.content))
