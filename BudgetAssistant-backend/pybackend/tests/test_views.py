import importlib.resources as pkg_resources
import json
import random
import unittest
from datetime import UTC, datetime
from typing import Any, Callable, Dict, List, Tuple
from unittest.mock import MagicMock, patch

from dateutil.relativedelta import relativedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import JsonResponse
from django.test import override_settings
from django.urls import reverse
from faker import Faker
from model_bakery import baker
from polyfactory.factories import DataclassFactory
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APIClient, APITestCase
from rest_framework.utils.serializer_helpers import ReturnDict

from pybackend.analysis import BudgetTrackerResult, CategoryAndAmount, CategoryDetailsForPeriodHandlerResult, \
    CategoryDetailsForPeriodHandlerResultSerializer, ExpensesAndRevenueForPeriod, \
    PeriodAndAmount, RevenueAndExpensesPerPeriodAndCategory, RevenueAndExpensesPerPeriodAndCategorySerializer
from pybackend.commons import RevenueExpensesQuery, RevenueExpensesQuerySerializer, RevenueExpensesQueryWithCategory, \
    RevenueExpensesQueryWithCategorySerializer, TransactionInContextQuery, \
    TransactionQuery, \
    TransactionTypeEnum
from pybackend.dto import CategorizeTransactionsResponse, \
    CategorizeTransactionsResponseSerializer, FailedOperationResponse, \
    FailedOperationResponseSerializer, PageTransactionsInContextRequest, \
    PageTransactionsInContextRequestSerializer, PageTransactionsRequest, \
    PageTransactionsRequestSerializer, PageTransactionsToManuallyReviewRequest, \
    PageTransactionsToManuallyReviewRequestSerializer, RevenueAndExpensesPerPeriodResponse, \
    RevenueAndExpensesPerPeriodResponseSerializer, SaveAlias, \
    SaveAliasSerializer, SuccessfulOperationResponse, SuccessfulOperationResponseSerializer, \
    TransactionsPage, TransactionsPageSerializer
from pybackend.models import BankAccount, BudgetTree, BudgetTreeNode, Category, Counterparty, CustomUser, Transaction
from pybackend.period import ResolvedStartEndDateShortcut, ResolvedStartEndDateShortcutSerializer, Year
from pybackend.providers import BudgetTreeProvider, CategoryTreeProvider
from pybackend.rules import RuleSetWrapper, RuleSetWrapperSerializer
from pybackend.serializers import BankAccountSerializer, BudgetTreeNodeSerializer, BudgetTreeSerializer, \
    CategoryTreeSerializer, \
    TransactionSerializer
from utils import RevenueAndExpensesPerPeriodAndCategoryFactory, create_random_rule_set, generate_random_period


def deserialize_succesful_operation_response(data: Dict) -> SuccessfulOperationResponse:
    serializer = SuccessfulOperationResponseSerializer(data=data)
    if serializer.is_valid(raise_exception=True):
        return SuccessfulOperationResponse(**serializer.validated_data)


def deserialize_failed_operation_response(data: Dict) -> FailedOperationResponse:
    serializer = FailedOperationResponseSerializer(data=data)
    if serializer.is_valid(raise_exception=True):
        return FailedOperationResponse(**serializer.validated_data)


def to_dict(data: ReturnDict):
    # convert
    json_str = JSONRenderer().render(data)
    # convert byte string to plain string
    json_str = json_str.decode('utf-8')
    json_dict = json.loads(json_str)
    return json_dict



@override_settings(
    REST_FRAMEWORK={
        'DEFAULT_RENDERER_CLASSES': (
                'rest_framework.renderers.JSONRenderer',
        ),
        'DEFAULT_PARSER_CLASSES': (
                'rest_framework.parsers.JSONParser',
        ),
    }
)
class ProtectedApiTestCase(APITestCase):
    def setUp(self):
        self.client : APIClient = APIClient(enforce_csrf_checks=False)
        #check if test_user exists. If not create it
        self.password="test_password"
        if not CustomUser.objects.filter(username="test_user").exists():

            self.user = CustomUser.objects.create_user(username="test_user", password=self.password)
        self.login()

    def login(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/token/", {"username": "test_user", "password": self.password}, format="json")
        #print(f"Auth response: {response.json()}" )  # Debugging
        self.access_token = response.json().get("access")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def logout(self):
        self.client.logout()

    def deserialize_instance(self, item_dict: Dict, pk_name:str, serializer_class: Any) -> Any:
        return serializer_class().deserialize_instance(item_dict, item_dict[pk_name])

    def do_test_fail_if_logged_out(self, fn:Callable):
        self.logout()
        response = fn()
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])





class BankAccountsForUserTests(ProtectedApiTestCase):

    def test_bank_accounts_for_user(self):
        expected_bank_accounts = []
        expected_bank_accounts.append(baker.make(BankAccount, account_number="a", users=[self.user]))
        expected_bank_accounts.append(baker.make(BankAccount, account_number="b", users=[self.user]))
        url = reverse('bank_accounts_for_user')
        response: JsonResponse = self.client.get(url, {'username': self.user.username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response: List = json.loads(response.content.decode('utf-8'))
        actual_bank_accounts = []
        for item in response:
            actual = self.deserialize_instance(item, 'account_number', BankAccountSerializer )
            actual_bank_accounts.append(actual)

        self.assertEqual(actual_bank_accounts, expected_bank_accounts)

    def test_fail_if_logged_out(self):
        fn = lambda: self.client.get(reverse('bank_accounts_for_user'), {'username': self.user.username})
        self.do_test_fail_if_logged_out(fn)


class RevenueExpensesQueryFactory(DataclassFactory[RevenueExpensesQuery]):
    __allow_none_optionals__ = False
    ...


class RevenueExpensesQueryWithCategoryFactory(DataclassFactory[RevenueExpensesQueryWithCategory]):
    __allow_none_optionals__ = False
    ...


class ExpensesAndRevenueForPeriodFactory(DataclassFactory[ExpensesAndRevenueForPeriod]):
    ...

    @classmethod
    def period(cls):
        start: datetime = datetime.now()
        end: datetime = datetime.now()
        return Year(start=start, end=end)


class RevenueAndExpensesPerPeriodTests(ProtectedApiTestCase):

    @patch('pybackend.views.get_analysis_service')
    def test_revenue_and_expenses_per_period(self, mock_get_analysis_service):
        # Create a mock AnalysisService object
        mock_analysis_service = MagicMock()
        mock_get_analysis_service.return_value = mock_analysis_service
        query = RevenueExpensesQueryFactory.build()

        service_response = ExpensesAndRevenueForPeriodFactory.batch(5)
        mock_analysis_service.get_revenue_and_expenses_per_period.return_value = service_response



        expected = RevenueAndExpensesPerPeriodResponse(content=service_response, number=1,
                                                       total_elements=len(service_response), size=len(service_response))
        url = reverse('revenue_and_expenses_per_period')

        payload = RevenueExpensesQuerySerializer(query).data
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = RevenueAndExpensesPerPeriodResponseSerializer(data=response.json())
        if serializer.is_valid(raise_exception=True):
            actual = RevenueAndExpensesPerPeriodResponse(**serializer.validated_data)
            self.assertEqual(expected, actual)

    def test_fail_if_logged_out(self):
        url = reverse('revenue_and_expenses_per_period')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)

class TransactionQuery2Factory(DataclassFactory[TransactionQuery]):
    __allow_none_optionals__ = False
    ...


class TransactionInContextQueryFactory(DataclassFactory[TransactionInContextQuery]):
    __allow_none_optionals__ = False


class PageTransactionsRequestFactory(DataclassFactory[PageTransactionsRequest]):
    __allow_none_optionals__ = False
    ...

    @classmethod
    def query(cls):
        return TransactionQuery2Factory.build()

    @classmethod
    def sort_property(cls):
        options = ['transaction_id', 'booking_date', 'amount', 'counterparty',
                   'category', 'manually_assigned_category', 'is_recurring',
                   'is_advance_shared_account', 'upload_timestamp',
                   'is_manually_reviewed']
        return random.choice(options)

    @classmethod
    def sort_order(cls):
        return random.choice(['asc', 'desc'])


class PageTransactionsToManuallyReviewRequestFactory(DataclassFactory[PageTransactionsToManuallyReviewRequest]):
    __allow_none_optionals__ = False
    ...

    @classmethod
    def sort_property(cls):
        options = ['transaction_id', 'booking_date', 'amount', 'counterparty',
                   'category', 'manually_assigned_category', 'is_recurring',
                   'is_advance_shared_account', 'upload_timestamp',
                   'is_manually_reviewed']
        return random.choice(options)

    @classmethod
    def sort_order(cls):
        return random.choice(['asc', 'desc'])



class PageTransactionsTests(ProtectedApiTestCase):

    @patch('pybackend.views.get_transactions_service')
    def test_page_transactions(self, get_transactions_service):
        mock_service = MagicMock()
        get_transactions_service.return_value = mock_service
        request = PageTransactionsRequestFactory.build()
        transactions = baker.make('Transaction', _quantity=10)
        transactions_page = TransactionsPage(content=transactions, number=1, total_elements=100, size=10)
        expected_response = TransactionsPageSerializer(transactions_page).data
        mock_service.page_transactions.return_value = transactions_page
        url = reverse('page_transactions')
        actual_response = self.client.post(url, data=PageTransactionsRequestSerializer(request).data, format='json')
        self.assertEqual(actual_response.status_code, status.HTTP_200_OK)
        self.assertEqual(actual_response.json(), expected_response)


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

        url = reverse('page_transactions')

        # Check all pages from 1 to 10
        for page_num in range(1, 11):
            # Create request data for the current page
            request_data = {
                'page': page_num,
                'size': 10,
                'sort_order': 'asc',
                'sort_property': 'transaction_id'
            }

            # Make POST request to the view
            response = self.client.post(url, data=request_data, format='json')

            # Verify response status code
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Parse response data
            response_data = response.json()

            # Verify total_elements is always 99
            self.assertEqual(response_data['total_elements'], 99)

            # Verify page number matches the requested page
            self.assertEqual(response_data['number'], page_num)

            # Calculate expected content size (10 for pages 1-9, 9 for page 10)
            expected_size = 9 if page_num == 10 else 10
            self.assertEqual(len(response_data['content']), expected_size)

            # Calculate the start and end indices for the expected transactions
            start_idx = (page_num - 1) * 10
            end_idx = min(start_idx + 10, 99)
            expected_transactions = transactions[start_idx:end_idx]

            # Verify that the content matches the expected transactions
            for i, transaction_data in enumerate(response_data['content']):
                # Get the transaction_id from the response
                response_transaction_id = transaction_data['transaction_id']
                # Get the expected transaction_id
                expected_transaction_id = expected_transactions[i].transaction_id
                # Verify they match
                self.assertEqual(response_transaction_id, expected_transaction_id, 
                                f"Transaction mismatch on page {page_num}, position {i}")

    def test_fail_if_logged_out(self):
        url = reverse('page_transactions')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)

class PageTransactionsInContextTests(ProtectedApiTestCase):

    @patch('pybackend.views.get_transactions_service')
    def test_page_transactions_in_context(self, get_transactions_service):
        mock_service = MagicMock()
        get_transactions_service.return_value = mock_service
        transaction_query = TransactionInContextQueryFactory.build()
        transactions = baker.make(Transaction, _quantity=10)
        response = {
            'content': transactions,
            'number': 1,
            'total_elements': 100,
            'size': 10
        }
        request = PageTransactionsInContextRequest(page=1, size=10, sort_order='asc', sort_property='transaction_id',
                                                   query=transaction_query)
        mock_service.page_transactions_in_context.return_value = response
        url = reverse('page_transactions_in_context')
        response = self.client.post(url, PageTransactionsInContextRequestSerializer(request).data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    def test_fail_if_logged_out(self):
        url = reverse('page_transactions_in_context')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)


class TransactionsPageFactory(DataclassFactory[TransactionsPage]):
    __allow_none_optionals__ = False
    ...

    @classmethod
    def content(cls):
        fake = Faker()

        upload_timestamp = fake.date_time(tzinfo=UTC)
        return baker.make(Transaction, _quantity=10, upload_timestamp=upload_timestamp)

class PageTransactionsToManuallyReviewTests(ProtectedApiTestCase):
    maxDiff = None
    @patch('pybackend.views.get_transactions_service')
    def test_page_transactions_to_manually_review(self, get_transactions_service):
        mock_service = MagicMock()
        get_transactions_service.return_value = mock_service

        # transactions = baker.make('Transaction', _quantity=10)
        service_response = TransactionsPageFactory.build()
        mock_service.page_transactions_to_manually_review.return_value = service_response
        url = reverse('page_transactions_to_manually_review')
        request = PageTransactionsToManuallyReviewRequestFactory.build()
        response = self.client.post(url, data=PageTransactionsToManuallyReviewRequestSerializer(request).data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        def handle_counterparty(data: dict) -> dict:
            content  = data['content']
            for item in content:
                if 'counterparty' in item:
                    counterparty = item.pop('counterparty')
                    item['counterparty_id'] = counterparty['name']
            data['content'] = content
            return data
        response_json = handle_counterparty(response_json)
        serializer = TransactionsPageSerializer(data=response_json)
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            actual = TransactionsPage(**validated_data)
            self.assertEqual(actual, service_response)
    def test_fail_if_logged_out(self):
        url = reverse('page_transactions_to_manually_review')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)



class CountTransactionsToManuallyReviewTests(ProtectedApiTestCase):

    @patch('pybackend.views.get_transactions_service')
    def test_count_transactions_to_manually_review(self, get_transactions_service):
        url = reverse('count_transactions_to_manually_review')
        mock_service = MagicMock()
        get_transactions_service.return_value = mock_service
        mock_service.count_transactions_to_manually_review.return_value = 10
        response = self.client.get(url, {'bank_account': 'my_account'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 10)

    def test_fail_if_logged_out(self):
        url = reverse('count_transactions_to_manually_review')
        fn = lambda : self.client.get(url, {}, format='json')
        self.do_test_fail_if_logged_out(fn)

class SaveTransactionTests(ProtectedApiTestCase):

    @patch('pybackend.views.get_transactions_service')
    def test_save_transaction(self, get_transactions_service):
        mock_service = MagicMock()
        transaction = baker.make(Transaction)
        data = TransactionSerializer(transaction).data
        if 'counterparty' in data:
            data['counterparty_id'] = data.pop('counterparty')['name']
        dto_serializer = TransactionSerializer(data=data)
        if dto_serializer.is_valid(raise_exception=True):
            dto = Transaction(**dto_serializer.validated_data)
            get_transactions_service.return_value = mock_service
            service_response = SuccessfulOperationResponse(
                message=f"Transaction with id '{dto.transaction_id}' was updated successfully")
            mock_service.save_transaction.return_value = service_response
            url = reverse('save_transaction')
            response = self.client.post(url, data=TransactionSerializer(dto).data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json(), SuccessfulOperationResponseSerializer(service_response).data)
    def test_fail_if_logged_out(self):
        url = reverse('save_transaction')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)

class CategoryTreeTests(ProtectedApiTestCase):

    def test_category_tree_expenses(self):
        url = reverse('category_tree')
        category_tree = CategoryTreeProvider().provide(TransactionTypeEnum.EXPENSES)
        json = CategoryTreeSerializer(category_tree).data
        delattr(json, 'serializer')
        response = self.client.get(url, query_params={'transaction_type': 'EXPENSES'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), json)
    def test_category_tree_revenue(self):
        url = reverse('category_tree')
        category_tree = CategoryTreeProvider().provide(TransactionTypeEnum.REVENUE)
        json = CategoryTreeSerializer(category_tree).data
        delattr(json, 'serializer')
        response = self.client.get(url, query_params={'transaction_type': 'REVENUE'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), json)
    def test_fail_if_logged_out(self):
        url = reverse('category_tree')
        fn = lambda : self.client.get(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)


class DistinctCounterpartyNamesTests(ProtectedApiTestCase):

    def test_distinct_counterparty_names(self):
        bank_account = baker.make(BankAccount, account_number='my_account')
        counterparties = baker.make(Counterparty, _quantity=5)
        transactions = []
        for cp in counterparties:
            transactions.extend(baker.make(Transaction, bank_account= bank_account, counterparty=cp, _quantity=2))
        url = reverse('distinct_counterparty_names')
        data = {'account': bank_account.account_number}
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual = response.json()
        self.assertEqual(len(actual), len(counterparties))
        self.assertSetEqual(set(actual), {cp.name for cp in counterparties})

    def test_fail_if_logged_out(self):
        url = reverse('distinct_counterparty_names')
        fn = lambda : self.client.get(url, {})

        self.do_test_fail_if_logged_out(fn)


class DistinctCounterpartyAccountsTests(ProtectedApiTestCase):


    def test_distinct_counterparty_accounts(self):
        counterparties = baker.make(Counterparty, _quantity=5)
        expected = {cp.account_number for cp in counterparties}
        self.assertEqual(len(expected), 5)
        transactions = []
        for cp in counterparties:
            transactions.extend(baker.make(Transaction, counterparty=cp, _quantity=2))
        url = reverse('distinct_counterparty_accounts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual = response.json()
        self.assertEqual(len(actual), len(expected))
        self.assertSetEqual(set(actual), expected)

    def test_fail_if_logged_out(self):
        url = reverse('distinct_counterparty_accounts')
        fn = lambda : self.client.get(url)
        self.do_test_fail_if_logged_out(fn)

class UploadTransactionsTests(ProtectedApiTestCase):

    def _to_simple_uploaded_file(self, filename:str) -> Tuple[Any, SimpleUploadedFile]:
        with pkg_resources.path('pybackend.tests.resources',
                                filename) as file_path:
            with open(file_path, 'r') as file:
                csv_file = SimpleUploadedFile(filename, file.read().encode('utf-8'), content_type='text/csv')
                return file, csv_file

    def test_upload_transactions_all_new(self):
        print(f"Request headers: {self.client.headers}")

        url = reverse('upload_transactions')

        file_handle1, simple_uploaded_file1 = self._to_simple_uploaded_file("belfius_transactions.csv")
        file_handle2, simple_uploaded_file2 = self._to_simple_uploaded_file("belfius_transactions_2.csv")
        print(f"Request content type: {simple_uploaded_file1.content_type}")
        print(f"Request content type: {simple_uploaded_file2.content_type}")
        response = self.client.post(url, {'files': [simple_uploaded_file1, simple_uploaded_file2]},  format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict =response.json()
        self.assertEqual(response_dict['created'], 20)
        self.assertEqual(response_dict['updated'], 0)
        file_handle1.close()
        file_handle2.close()

    def test_upload_transactions_duplicates(self):
        url = reverse('upload_transactions')
        file_handle1, simple_uploaded_file1 = self._to_simple_uploaded_file("belfius_transactions.csv")
        response = self.client.post(url, {'files': [simple_uploaded_file1]},  format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict =response.json()
        self.assertEqual(response_dict['created'], 10)
        self.assertEqual(response_dict['updated'], 0)
        file_handle1.close()
        file_handle1, simple_uploaded_file1 = self._to_simple_uploaded_file("belfius_transactions.csv")
        response = self.client.post(url, {'files': [simple_uploaded_file1]},  format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict =response.json()
        self.assertEqual(response_dict['created'], 0)
        self.assertEqual(response_dict['updated'], 10)
        file_handle1.close()

    def test_fail_if_logged_out(self):
        url = reverse('upload_transactions')
        fn = lambda : self.client.post(url, {}, format='multipart')

        self.do_test_fail_if_logged_out(fn)


class PeriodAndAmountFactory(DataclassFactory[PeriodAndAmount]):
    __set_as_default_factory_for_type__ = True
    __model__ = PeriodAndAmount

    @classmethod
    def period(cls):
        return generate_random_period()


class CategoryAndAmountFactory(DataclassFactory[CategoryAndAmount]):
    __set_as_default_factory_for_type__ = True
    __model__ = CategoryAndAmount

    @classmethod
    def category(cls):
        return baker.make('Category')


class RevenueExpensesPerPeriodAndCategoryTests(ProtectedApiTestCase):
    @patch('pybackend.views.get_analysis_service')
    def test_revenue_expenses_per_period_and_category(self, get_analysis_service):
        mock_service = MagicMock()
        get_analysis_service.return_value = mock_service
        expected = RevenueAndExpensesPerPeriodAndCategoryFactory.build()
        mock_service.get_revenue_and_expenses_per_period_and_category.return_value = expected
        data = RevenueExpensesQuerySerializer(RevenueExpensesQueryFactory.build()).data
        self.url = reverse('revenue_expenses_per_period_and_category')
        actual = self.client.post(self.url, data=data, format='json')
        self.assertEqual(actual.status_code, status.HTTP_200_OK)
        actual = actual.json()

        def deserialize(item: Dict) -> RevenueAndExpensesPerPeriodAndCategory:
            serializer = RevenueAndExpensesPerPeriodAndCategorySerializer(data=item)
            if serializer.is_valid():
                return RevenueAndExpensesPerPeriodAndCategorySerializer().create(serializer.validated_data)
            else:
                raise ValueError(serializer.error_messages)

        actual = deserialize(actual)
        self.assertEqual(expected, actual)

    def test_fail_if_logged_out(self):
        url = reverse('revenue_expenses_per_period_and_category')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)


class BudgetTrackerResultFactory(DataclassFactory[BudgetTrackerResult]):
    __allow_none_optionals__ = False
    ...


class TrackBudgetTests(ProtectedApiTestCase):

    @patch('pybackend.views.get_analysis_service')
    def test_track_budget(self, get_analysis_service):
        mock_service = MagicMock()
        service_response = BudgetTrackerResultFactory.build()
        get_analysis_service.return_value = mock_service
        mock_service.track_budget.return_value = service_response
        self.url = reverse('track_budget')
        response = self.client.post(self.url,
                                    data=RevenueExpensesQuerySerializer(RevenueExpensesQueryFactory.build()).data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fail_if_logged_out(self):
        url = reverse('track_budget')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)




class ResolveStartEndDateShortcutTests(ProtectedApiTestCase):

    def test_resolve_start_end_date_shortcut(self):
        self.url = reverse('resolve_start_end_date_shortcut')
        response = self.client.get(self.url, data={'query': 'current month'}, format='json')
        # python code to get the current month

        now = datetime.now()
        start = now.replace(day=1)
        end = start + relativedelta(months=1, days=-1)
        expected = ResolvedStartEndDateShortcut(start=start, end=end)

        def deserialize(item: Dict) -> ResolvedStartEndDateShortcut:
            serializer = ResolvedStartEndDateShortcutSerializer(data=item)
            if serializer.is_valid(raise_exception=True):
                return ResolvedStartEndDateShortcut(**serializer.validated_data)

        actual = deserialize(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(actual.start.year, expected.start.year)
        self.assertEqual(actual.start.month, expected.start.month)
        self.assertEqual(actual.start.day, expected.start.day)
        self.assertEqual(actual.end.year, expected.end.year)
        self.assertEqual(actual.end.month, expected.end.month)
        self.assertEqual(actual.end.day, expected.end.day)

    def test_fail_if_logged_out(self):
        url = reverse('resolve_start_end_date_shortcut')
        fn = lambda : self.client.get(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)


class RegisterViewTestCase(APITestCase):
    def setUp(self):
        # Common setup for test cases (if needed)
        self.url = reverse('register')


    def test_register_user_success(self):
        valid_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!"
        }
        """Test successful registration of a new user."""
        response = self.client.post(self.url, valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_obj = deserialize_succesful_operation_response(response.json())
        self.assertEqual("User 'testuser' created successfully", response_obj.message)
        # Check if the user is created in the database
        self.assertTrue(CustomUser.objects.filter(username=valid_data['username']).exists())

    def test_register_user_invalid_data(self):
        self.invalid_data = {
            "username": "",  # Empty username to trigger validation error
            "email": "invalidemail",  # Invalid email format
            "password": "short"  # Weak password
        }

        """Test registration with invalid data."""
        response = self.client.post(self.url, self.invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_obj = deserialize_failed_operation_response(response.json())
        self.assertEqual('username:\nThis field may not be blank.\nemail:\nEnter a valid email address.',
                         response_obj.error)

    def test_register_user_duplicate_username(self):
        """Test registration with a duplicate username."""
        # Create a user with the same username
        valid_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!"
        }
        url = reverse('register')
        CustomUser.objects.create_user(username=valid_data['username'], email='existing@example.com',
                                       password='AnotherPassword123!')
        response = self.client.post(url, valid_data, format='json')
        response_obj = deserialize_failed_operation_response(response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Username already exists', response_obj.error)


# Replace with your custom user model if applicable

class LoginViewTestCase(APITestCase):
    def setUp(self):
        # URL for the login endpoint
        self.login_url = '/api/token/'  # Update this to your actual login URL (e.g., JWT login)

        # Create a test user
        self.user_credentials = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        self.user = CustomUser.objects.create_user(**self.user_credentials)

    def test_login_success(self):
        """Test successful login with valid credentials."""
        response = self.client.post(self.login_url, self.user_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)  # JWT response contains access token
        self.assertIn('refresh', response.data)  # JWT response contains refresh token

    def test_login_invalid_credentials(self):
        """Test login attempt with invalid credentials."""
        invalid_credentials = {
            "username": "testuser",
            "password": "WrongPassword123!"
        }
        response = self.client.post(self.login_url, invalid_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)  # Check if an error message is returned

    def test_login_nonexistent_user(self):
        """Test login attempt with a nonexistent user."""
        nonexistent_user_credentials = {
            "username": "nonexistentuser",
            "password": "DoesNotMatter123!"
        }
        response = self.client.post(self.login_url, nonexistent_user_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)


class TokenRefreshTestCase(APITestCase):
    def setUp(self):
        # URL for the login and refresh token endpoints
        self.token_url = '/api/token/'  # JWT login endpoint
        self.refresh_url = '/api/token/refresh/'  # JWT token refresh endpoint

        # Create a test user
        self.user_credentials = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        self.user = CustomUser.objects.create_user(**self.user_credentials)

    def test_refresh_token_success(self):
        """Test refreshing the token with a valid refresh token."""
        # Step 1: Log in to get the refresh token
        response = self.client.post(self.token_url, self.user_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data['refresh']

        # Step 2: Use the refresh token to get a new access token
        refresh_response = self.client.post(self.refresh_url, {"refresh": refresh_token}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_refresh_token_invalid(self):
        """Test refreshing the token with an invalid refresh token."""
        invalid_refresh_token = "invalid.refresh.token"
        response = self.client.post(self.refresh_url, {"refresh": invalid_refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_refresh_token_expired(self):
        """Test refreshing the token after the refresh token has expired."""
        # Step 1: Log in to get the refresh token
        response = self.client.post(self.token_url, self.user_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data['refresh']

        # Simulate token expiration by using an expired token (for demonstration, assume one is generated manually)
        expired_refresh_token = "expired.refresh.token"  # Replace with a way to simulate an expired token in tests
        response = self.client.post(self.refresh_url, {"refresh": expired_refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)



class UpdateUserViewTestCase(ProtectedApiTestCase):
    def setUp(self):
        super().setUp()
        self.update_url = reverse("update_user")

    def test_update_password_success(self):
        """Test successfully updating the user's password."""
        response = self.client.put(
            self.update_url,
            {"password": "NewSecurePassword123!"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_obj = deserialize_succesful_operation_response(response.json())
        self.assertEqual(response_obj.message, "Password updated successfully.")

        # Ensure the old password no longer works
        self.client.credentials()  # Clear the token
        login_response = self.client.post("/api/token/", {"username": "test_user", "password": self.password},
                                          format="json")
        self.assertEqual(login_response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Ensure the new password works
        login_response = self.client.post("/api/token/", {"username": "test_user", "password": "NewSecurePassword123!"},
                                          format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_update_email_success(self):
        """Test successfully updating the user's email address."""
        response = self.client.put(
            self.update_url,
            {"email": "newemail@example.com"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_obj = deserialize_succesful_operation_response(response.json())
        self.assertEqual(response_obj.message, "Email updated successfully.")

        # Verify the email was updated in the database
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "newemail@example.com")

    def test_update_password_invalid(self):
        """Test updating the password with an invalid value."""
        response = self.client.put(
            self.update_url,
            {"password": "short"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_obj = deserialize_failed_operation_response(response.json())
        self.assertEqual(response_obj.error, 'This password is too short. It must contain at least 8 characters.')

    def test_update_email_invalid(self):
        """Test updating the email with an invalid value."""
        response = self.client.put(
            self.update_url,
            {"email": "not-an-email"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_obj = deserialize_failed_operation_response(response.json())
        self.assertEqual(response_obj.error, 'Enter a valid email address.')

    def test_unauthorized_access(self):
        """Test accessing the update view without authentication."""

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION='')
        response = self.client.put(
            self.update_url,
            {"password": "NewSecurePassword123!"},
            format="json"
        )
        #log the response message
        print(f"Response message: {response.json()}")  # Debugging
        self.assertEqual(response.json()['detail'], 'Authentication credentials were not provided.')
        self.assertTrue(response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class UpdateBudgetEntryAmountTests(ProtectedApiTestCase):

    def test_update_budget_entry_amount(self):
        bank_account = baker.make(BankAccount)
        budget_tree = BudgetTreeProvider().provide(bank_account)
        first_child: BudgetTreeNode = budget_tree.root.children.first()
        original_amount = 100
        first_child.amount = original_amount
        first_child.save()
        first_child.amount = 200
        update = BudgetTreeNodeSerializer(first_child).data
        delattr(update, 'serializer')
        update = json.dumps(update)
        url = reverse('update_budget_entry_amount')
        response = self.client.post(url, data=update, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_budget_entry_amount_no_db_entry(self):
        bank_account = baker.make(BankAccount)
        budget_tree = BudgetTreeProvider().provide(bank_account)
        first_child: BudgetTreeNode = budget_tree.root.children.first()
        update = BudgetTreeNodeSerializer(first_child).data
        delattr(update, 'serializer')
        update = json.dumps(update)
        # we delete not_in_db from db before calling the api
        first_child.delete()
        url = reverse('update_budget_entry_amount')
        response = self.client.post(url, data=update, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_fail_if_logged_out(self):
        url = reverse('update_budget_entry_amount')
        fn = lambda : self.client.post(url, {}, content_type='application/json')

        self.do_test_fail_if_logged_out(fn)

class FindOrCreateBudgetTests(ProtectedApiTestCase):
    def test_with_non_existing_tree(self):
        url = reverse('find_or_create_budget')
        account_number = 'abc'
        bank_account = baker.make(BankAccount, account_number=account_number)
        request = {'bank_account_number': bank_account.account_number}
        self.assertEqual(BudgetTree.objects.count(), 0)
        response = self.client.post(url, data=json.dumps(request), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BudgetTree.objects.count(), 1)
        # deserialize the response
        actual = json.loads(response.content.decode('utf-8'))
        expected = BudgetTree.objects.first()
        serializer = BudgetTreeSerializer(data=actual)
        if serializer.is_valid(raise_exception=False):
            self.assertEqual(BudgetTree(**serializer.validated_data), BudgetTree(**expected))
    def test_fail_if_logged_out(self):
        url = reverse('find_or_create_budget')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)


class SaveRuleSetWrapperTests(ProtectedApiTestCase):

    def test_save_rule_set_wrapper(self):
        self.url = reverse('save_rule_set_wrapper')
        rule_set = create_random_rule_set()
        categories = baker.make(Category, type='EXPENSES', _quantity=5)
        category = categories[0]
        original = baker.make(RuleSetWrapper, rule_set=rule_set, users=[self.user], category=category)
        # create a copy of the original
        new_rule_set = create_random_rule_set()
        self.assertNotEqual(rule_set, new_rule_set)
        changed = RuleSetWrapper(id=original.id, rule_set=new_rule_set, category=category)
        changed.users.set([self.user])
        response = self.client.post(self.url, data=RuleSetWrapperSerializer(changed).data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RuleSetWrapper.objects.count(), 1)
        actual = RuleSetWrapper.objects.first()
        self.assertEqual(actual, changed)
        self.assertNotEqual(actual.rule_set, original.rule_set)
    def test_fail_if_logged_out(self):
        url = reverse('save_rule_set_wrapper')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)


class GetOrCreateRuleSetWrapperTests(ProtectedApiTestCase):

    @patch('pybackend.views.get_rule_sets_service')
    def test_empty_db(self, get_rule_sets_service):
        self.url = reverse('get_or_create_rule_set_wrapper')
        categories = baker.make(Category, type='EXPENSES', _quantity=5)
        mock_service = MagicMock()
        get_rule_sets_service.return_value = mock_service
        rule_set = create_random_rule_set()
        expected = baker.make(RuleSetWrapper, rule_set=rule_set, users=[self.user])
        mock_service.get_or_create_rule_set_wrapper.return_value = expected
        request = {
            'category_qualified_name': categories[0].qualified_name,
            'type': 'EXPENSES'
        }
        response = self.client.post(self.url, data=json.dumps(request), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))

        def deserialize(data: Dict) -> RuleSetWrapper:
            serializer = RuleSetWrapperSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                validated_data = serializer.validated_data
                users = validated_data.pop('users')
                wrapper = RuleSetWrapper(**validated_data)
                wrapper.users.set(users)
                return wrapper

        rule_set_wrapper = deserialize(data)
        self.assertEqual(RuleSetWrapper.objects.count(), 1)
        self.assertEqual(rule_set_wrapper, expected)
        self.assertEqual(rule_set_wrapper, expected)

    def test_fail_if_logged_out(self):
        url = reverse('get_or_create_rule_set_wrapper')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)


class CategorizeTransactionsTests(ProtectedApiTestCase):

    @patch('pybackend.views.get_transactions_service')
    def test_categorize_transactions(self, get_transactions_service):
        self.url = reverse('categorize_transactions')
        mock_service = MagicMock()
        get_transactions_service.return_value = mock_service
        expected_response = CategorizeTransactionsResponse(
            message="Categorized 10 transactions; 8 transactions have no category",
            with_category_count=10, without_category_count=8)
        mock_service.categorise_transactions.return_value = expected_response
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_response = response.json()
        serializer = CategorizeTransactionsResponseSerializer(data=actual_response)
        if serializer.is_valid(raise_exception=True):
            actual_response = CategorizeTransactionsResponse(**serializer.validated_data)
            self.assertEqual(actual_response, expected_response)
    def test_fail_if_logged_out(self):
        url = reverse('categorize_transactions')
        fn = lambda : self.client.post(url)

        self.do_test_fail_if_logged_out(fn)


class SaveAliasTests(ProtectedApiTestCase):

    def test_save_alias(self):
        self.url = reverse('save_alias')
        account_number = 'abc'
        bank_account = baker.make(BankAccount, account_number=account_number, alias=None)
        self.assertIsNone(bank_account.alias)
        alias = 'test_alias'
        dto = SaveAlias(bank_account=bank_account.account_number, alias=alias)
        response = self.client.post(self.url, data=SaveAliasSerializer(dto).data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bank_account.refresh_from_db()
        self.assertEqual(bank_account.alias, alias)
    def test_fail_if_logged_out(self):
        url = reverse('save_alias')
        fn = lambda : self.client.post(url, {}, format='json')

        self.do_test_fail_if_logged_out(fn)


class CategoryDetailsForPeriodHandlerResultFactory(DataclassFactory[CategoryDetailsForPeriodHandlerResult]):
    ...


class CategoryDetailsForPeriodTests(ProtectedApiTestCase):
    @patch('pybackend.views.get_analysis_service')
    def test_category_details_for_period(self, get_analysis_service):
        mock_service = MagicMock()
        get_analysis_service.return_value = mock_service
        expected_response = CategoryDetailsForPeriodHandlerResultFactory.build()
        mock_service.get_category_details_for_period.return_value = expected_response

        serializer = RevenueExpensesQueryWithCategorySerializer(
            instance=RevenueExpensesQueryWithCategoryFactory.build())
        self.url = reverse('category_details_for_period')
        response = self.client.post(self.url, data=serializer.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()

        def deserialize(data: Dict) -> CategoryDetailsForPeriodHandlerResult:
            serializer = CategoryDetailsForPeriodHandlerResultSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                return CategoryDetailsForPeriodHandlerResult(**serializer.validated_data)

        response_obj = deserialize(response)
        self.assertEqual(response_obj, expected_response)
    def test_fail_if_logged_out(self):
        url = reverse('category_details_for_period')
        fn = lambda : self.client.get(url, {})

        self.do_test_fail_if_logged_out(fn)


class CategoriesForAccountAndTransactionTypeTests(ProtectedApiTestCase):

    def test_categories_for_account_and_transaction_type(self):
        bank_account = baker.make(BankAccount, account_number='a')
        expenses_categories = baker.make('Category', _quantity=5)
        for category in expenses_categories:
            baker.make('Transaction', bank_account=bank_account, category=category, amount=-10)
        revenue_categories = baker.make('Category', _quantity=5)
        for category in revenue_categories:
            baker.make('Transaction', bank_account=bank_account, category=category, amount=10)
        self.url = reverse('categories_for_account_and_transaction_type')
        response = self.client.get(self.url,
                                   data={'bank_account': bank_account.account_number, 'transaction_type': 'REVENUE'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        self.assertIsInstance(response, list)
        self.assertEqual(len(response), len(revenue_categories))
        self.assertEqual(sorted(response), sorted([category.name for category in revenue_categories]))

    def test_fail_if_logged_out(self):
        url = reverse('categories_for_account_and_transaction_type')
        fn = lambda : self.client.get(url, {})

        self.do_test_fail_if_logged_out(fn)
