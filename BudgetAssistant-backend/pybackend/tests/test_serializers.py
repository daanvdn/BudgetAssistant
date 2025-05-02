import importlib.resources as pkg_resources
import json
from datetime import datetime
from typing import Dict

from django.test import TestCase
from model_bakery import baker
from rest_framework.renderers import JSONRenderer
from rest_framework.utils.serializer_helpers import ReturnDict

from pybackend.commons import TransactionTypeEnum
from pybackend.models import BankAccount, Category, Counterparty, CustomUser, Transaction
from pybackend.providers import BudgetTreeProvider, CategoryTreeProvider
from pybackend.serializers import BankAccountSerializer, BudgetTreeSerializer, CategorySerializer, \
    CounterpartySerializer, \
    CustomUserSerializer, SimplifiedCategorySerializer, TransactionSerializer


def to_dict(data: ReturnDict):
    # convert
    json_str = JSONRenderer().render(data)
    # convert byte string to plain string
    json_str = json_str.decode('utf-8')
    json_dict = json.loads(json_str)
    return json_dict

def load_expected_as_dict(resource_file_name:str):
    # use importlib-resources to load the expected json file
    with pkg_resources.open_text('pybackend.tests.resources', resource_file_name) as file:
        s = file.read()
        return json.loads(s)

class BankAccountSerializerTests(TestCase):

    def test_create_bank_account(self):
        user = CustomUser.objects.create(username='testuser', password='password')
        data = {
            'account_number': '1234567890',
            'alias': 'Test Account',
            'users': [user.id]
        }
        serializer = BankAccountSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        bank_account = serializer.save()
        self.assertEqual(bank_account.account_number, '1234567890')
        self.assertEqual(bank_account.alias, 'Test Account')
        self.assertIn(user, bank_account.users.all())
        # ensure that we don't have duplicate users or bank accounts when calling save again
        serializer.save()
        self.assertEqual(bank_account.users.count(), 1)
        self.assertEqual(BankAccount.objects.count(), 1)

    def test_update_bank_account(self):
        user = CustomUser.objects.create(username='testuser', password='password')
        bank_account = BankAccount.objects.create(account_number='1234567890', alias='Old Alias')
        data = {
            'account_number': '1234567890',
            'alias': 'New Alias',
            'users': [user.id]
        }
        serializer = BankAccountSerializer(bank_account, data=data)
        self.assertTrue(serializer.is_valid())
        updated_bank_account = serializer.save()
        self.assertEqual(updated_bank_account.alias, 'New Alias')
        self.assertIn(user, updated_bank_account.users.all())
        self.assertIn(updated_bank_account, user.bank_accounts.all())
        # ensure that we don't have duplicate users or bank accounts when calling save again
        serializer.save()
        self.assertEqual(updated_bank_account.users.count(), 1)
        self.assertEqual(BankAccount.objects.count(), 1)
        self.assertEqual(CustomUser.objects.count(), 1)
        # add a new user to the bank account
        new_user = CustomUser.objects.create(username='newuser', password='password')
        data['users'] = [user.id, new_user.id]
        serializer = BankAccountSerializer(updated_bank_account, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertIn(new_user, updated_bank_account.users.all())
        self.assertEqual(updated_bank_account.users.count(), 2)

    def test_create_invalid_data(self):
        data = {
            'account_number': '',
            'alias': 'Test Account',
            'users': []
        }
        serializer = BankAccountSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('account_number', serializer.errors)

    def test_update_invalid_data(self):
        bank_account = BankAccount.objects.create(account_number='1234567890', alias='Old Alias')
        data = {
            'account_number': '',
            'alias': 'New Alias',
            'users': []
        }
        serializer = BankAccountSerializer(bank_account, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('account_number', serializer.errors)


class CustomUserSerializerTests(TestCase):

    def test_create_custom_user(self):
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'password123'
        }
        serializer = CustomUserSerializer(data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        custom_user = serializer.save()
        self.assertEqual(custom_user.username, 'testuser')
        self.assertEqual(custom_user.first_name, 'Test')
        self.assertEqual(custom_user.last_name, 'User')
        # check we don't have any duplicates when calling save again
        serializer.save()
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_update_custom_user(self):
        # create bank account
        bank_account = BankAccount.objects.create(account_number='1234567890')
        user = CustomUser.objects.create(username='testuser', password='password123')
        bank_account.users.add(user)
        data = {
            'username': 'testuser',
            'first_name': 'Updated',
            'last_name': 'User',
            'password': 'newpassword123',
            'bank_accounts': [bank_account.account_number]
        }
        serializer = CustomUserSerializer(user, data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        updated_user = serializer.save()
        self.assertEqual(updated_user.username, 'testuser')
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'User')
        # check the amount of bank accounts associated with the user
        self.assertEqual(updated_user.bank_accounts.count(), 1)
        # check that the bank account is associated with the user
        self.assertIn(bank_account, updated_user.bank_accounts.all())
        # check the amount of users associated with the bank account
        self.assertEqual(bank_account.users.count(), 1)
        # check that the user is associated with the bank account
        self.assertIn(updated_user, bank_account.users.all())
        # check we don't have any duplicate users or bank accounts when calling save again
        serializer.save()
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(BankAccount.objects.count(), 1)

    def test_create_invalid_custom_user(self):
        data = {
            'username': '',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'password123',
            'bank_accounts': []
        }
        serializer = CustomUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)


class CategorySerializerTest(TestCase):

    # Serializes a Category instance with all fields correctly
    def test_serialize_category_with_all_fields(self):
        category = Category.objects.create(name="Test Category", type=TransactionTypeEnum.EXPENSES,
                                           qualified_name="Test Category")
        serializer = CategorySerializer(category)
        expected_data = {
            'name': "Test Category",
            'qualified_name': "Test Category",
            'type': "EXPENSES",
            'children': []
        }
        self.assertEqual(serializer.data.keys(), expected_data.keys())
        self.assertEqual(serializer.data['name'], expected_data['name'])
        self.assertEqual(serializer.data['qualified_name'], expected_data['qualified_name'])
        self.assertEqual(serializer.data['type'], expected_data['type'])
        self.assertEqual(serializer.data['children'], expected_data['children'])

    # Retrieves and serializes the qualified name of a Category
    def test_serialize_qualified_name(self):
        parent_category = Category.objects.create(name="Parent", type=TransactionTypeEnum.EXPENSES, qualified_name="parent")
        child_category = Category.objects.create(name="Child", parent=parent_category, type=TransactionTypeEnum.EXPENSES,
                                                 qualified_name="parent#child")
        serializer = CategorySerializer(child_category)
        self.assertEqual(serializer.data['qualified_name'], "parent#child")

    # Serializes the type of a Category using the display name
    def test_serialize_type_display_name(self):
        category = Category.objects.create(name="Test Category", type=TransactionTypeEnum.REVENUE)
        serializer = CategorySerializer(category)
        self.assertEqual(serializer.data['type'], "REVENUE")

    # Serializes a Category with no children
    def test_serialize_category_no_children(self):
        category = Category.objects.create(name="No Children", type=TransactionTypeEnum.EXPENSES)
        serializer = CategorySerializer(category)
        self.assertEqual(serializer.data['children'], [])

    # Serializes a Category with a deeply nested hierarchy
    def test_serialize_deeply_nested_hierarchy(self):
        root = Category.objects.create(name="Root", type=TransactionTypeEnum.EXPENSES)
        level1 = Category.objects.create(name="Level 1", parent=root, type=TransactionTypeEnum.EXPENSES)
        root.add_child(level1)
        level2 = Category.objects.create(name="Level 2", parent=level1, type=TransactionTypeEnum.EXPENSES)
        level1.add_child(level2)
        serializer = CategorySerializer(root)
        self.assertEqual(len(serializer.data['children']), 1)
        self.assertEqual(serializer.data['children'][0]['name'], "Level 1")

    # Handles a Category with special characters in its name
    def test_serialize_category_special_characters(self):
        category = Category.objects.create(name="Special & Characters!", type=TransactionTypeEnum.REVENUE)
        serializer = CategorySerializer(category)
        self.assertEqual(serializer.data['name'], "Special & Characters!")

    # add a test for the create method of the serializer
    def test_create_category(self):
        data = {
            'name': 'Test Category',
            'type': TransactionTypeEnum.EXPENSES,
            'qualified_name': 'Test Category'
        }
        serializer = CategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.type, TransactionTypeEnum.EXPENSES)

    def test_serialize_root(self):
        category_tree = CategoryTreeProvider().provide(TransactionTypeEnum.EXPENSES)
        serializer = CategorySerializer(category_tree.root)
        serialized_data = serializer.data
        actual_json_dict = to_dict(serialized_data)
        expected_json_dict = load_expected_as_dict('expenses_categories.json')
        self.assertDictEqual(expected_json_dict, actual_json_dict)


class CounterpartySerializerTests(TestCase):

    def test_create_counterparty(self):
        user = baker.make(CustomUser, username='testuser', password='password')
        category = baker.make(Category, name="Test Category", type=TransactionTypeEnum.EXPENSES)
        data = {
            'name': 'Test Counterparty',
            'account_number': '1234567890',
            'street_and_number': '123 Test St',
            'zip_code_and_city': '12345 Test City',
            'category': category.id,
            'users': [user.id]

        }
        serializer = CounterpartySerializer(data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        counterparty = serializer.save()
        self.assertEqual(counterparty.name, Counterparty.normalize_counterparty('Test Counterparty'))
        self.assertEqual(counterparty.account_number, '1234567890')
        self.assertEqual(counterparty.street_and_number, '123 Test St')
        self.assertEqual(counterparty.zip_code_and_city, '12345 Test City')
        self.assertEqual(counterparty.category, category)
        self.assertIn(user, counterparty.users.all())

    def test_create_invalid_counterparty(self):
        data = {
            'name': '',
            'account_number': '',
            'street_and_number': '123 Test St',
            'zip_code_and_city': '12345 Test City',
            'category': None,
            'users': []
        }
        serializer = CounterpartySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        self.assertIn('account_number', serializer.errors)

    def test_update_counterparty(self):
        user = baker.make(CustomUser, username='testuser', password='password')
        category = baker.make(Category, name="Test Category", type=TransactionTypeEnum.EXPENSES)
        counterparty = baker.make(Counterparty,
            name='Old Counterparty',
            account_number='1234567890',
            street_and_number='123 Old St',
            zip_code_and_city='12345 Old City',
            category=category
        )
        counterparty.users.add(user)
        data = {
            'name': 'Old Counterparty',
            'account_number': '0987654321',
            'street_and_number': '456 New St',
            'zip_code_and_city': '67890 New City',
            'category': category.id,
            'users': [user.id]
        }
        serializer = CounterpartySerializer(counterparty, data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        updated_counterparty = serializer.save()
        self.assertEqual(updated_counterparty.name, Counterparty.normalize_counterparty('Old Counterparty'))
        self.assertEqual(updated_counterparty.account_number, '0987654321')
        self.assertEqual(updated_counterparty.street_and_number, '456 New St')
        self.assertEqual(updated_counterparty.zip_code_and_city, '67890 New City')
        self.assertEqual(updated_counterparty.category, category)
        self.assertIn(user, updated_counterparty.users.all())
        # now add another user to the counterparty
        new_user = baker.make(CustomUser, username='newuser', password='password')
        data['users'] = [user.id, new_user.id]
        serializer = CounterpartySerializer(updated_counterparty, data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        updated_counterparty = serializer.save()
        self.assertIn(new_user, updated_counterparty.users.all())
        self.assertEqual(updated_counterparty.users.count(), 2)
        # now add another category to the counterparty
        new_category = baker.make(Category, name="New Category", type=TransactionTypeEnum.REVENUE)
        data['category'] = new_category.id
        serializer = CounterpartySerializer(updated_counterparty, data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        updated_counterparty = serializer.save()
        self.assertEqual(updated_counterparty.category, new_category)
        self.assertEqual(updated_counterparty.category, new_category)


class TransactionSerializerTests(TestCase):

    def test_create_transaction(self):
        user = baker.make(CustomUser, username='testuser', password='password')
        category = baker.make(Category, name="Test Category", type=TransactionTypeEnum.EXPENSES)
        bank_account = baker.make(BankAccount, account_number='1234567890')
        bank_account.users.add(user)
        counterparty = baker.make(Counterparty, name='Test Counterparty', account_number='1234567890')
        counterparty.users.add(user)
        transaction_number = 'txn_num_001'
        transaction_id = Transaction._create_transaction_id(transaction_number, bank_account)
        transaction = baker.make(Transaction, transaction_number=transaction_number, bank_account=bank_account,
                                 category=category, counterparty=counterparty, transaction_id=transaction_id)
        # After creating the counterparty instance
        data = TransactionSerializer(instance=transaction).data
        data['counterparty_id'] = counterparty.name
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        deserialized = serializer.save()

        self.assertEqual(deserialized.transaction_id, transaction_id)
        self.assertEqual(deserialized.bank_account, bank_account)
        self.assertEqual(deserialized.counterparty, counterparty)
        self.assertEqual(deserialized.category, category)
        self.assertEqual(deserialized, transaction)
        # ensure that we don't have duplicate users, bank accounts or counterparties when calling save again
        self.assertEqual(deserialized.bank_account.users.count(), 1)
        self.assertEqual(deserialized.counterparty.users.count(), 1)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Counterparty.objects.count(), 1)
        self.assertEqual(BankAccount.objects.count(), 1)


    def test_create_transaction_invalid_data(self):
        data = {
            'transaction_id': '',
            'bank_account': None,
            'booking_date': 'invalid_date',
            'statement_number': '',
            'counterparty': None,
            'transaction_number': '',
            'transaction': '',
            'currency_date': 'invalid_date',
            'amount': 'invalid_amount',
            'currency': '',
            'bic': '',
            'country_code': '',
            'communications': '',
            'category': None,
            'manually_assigned_category': False,
            'is_recurring': False,
            'is_advance_shared_account': False,
            'upload_timestamp': 'invalid_timestamp',
            'is_manually_reviewed': False
        }
        serializer = TransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('transaction_id', serializer.errors)
        self.assertIn('bank_account', serializer.errors)
        self.assertIn('booking_date', serializer.errors)
        self.assertIn('counterparty_id', serializer.errors)
        self.assertIn('transaction_number', serializer.errors)
        self.assertIn('currency_date', serializer.errors)
        self.assertIn('amount', serializer.errors)
        self.assertIn('upload_timestamp', serializer.errors)

    def test_update_transaction(self):

        user = baker.make(CustomUser, username='testuser', password='password')
        category = baker.make(Category, name="Test Category", type=TransactionTypeEnum.EXPENSES)
        category2 = baker.make(Category, name="Test Category2", type=TransactionTypeEnum.EXPENSES)
        bank_account = baker.make(BankAccount, account_number='1234567890')
        bank_account.users.add(user)
        counterparty = baker.make(Counterparty, name='Test Counterparty', account_number='1234567890')
        counterparty.users.add(user)
        transaction_number = 'txn_num_001'

        transaction_id = Transaction._create_transaction_id(transaction_number, bank_account)
        transaction = baker.make(Transaction, transaction_number=transaction_number, bank_account=bank_account,
                                 category=category, counterparty=counterparty, transaction_id=transaction_id,
                                 manually_assigned_category=False,
                                 is_recurring=False,
                                 is_advance_shared_account=False,
                                 is_manually_reviewed=False
                                 )

        data = TransactionSerializer(transaction).data
        data['counterparty_id'] = counterparty.name  # Use primary key directly
        #fields that should not be updated
        data['transaction']='Updated Transaction'
        data['communications']='Updated communications'
        data['upload_timestamp']= datetime.now()
        #fields that should not be updated
        data['category'] = {
            'id': category2.id,
            'name': category2.name,
            'qualified_name': category2.qualified_name
        }
        data['manually_assigned_category']= True
        data['is_recurring']= True
        data['is_advance_shared_account']= True
        data['is_manually_reviewed']= True
        serializer = TransactionSerializer(transaction, data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        updated_transaction = serializer.save()
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(BankAccount.objects.count(), 1)
        self.assertEqual(Counterparty.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(updated_transaction.bank_account.users.count(), 1)
        self.assertEqual(updated_transaction.counterparty.users.count(), 1)

        self.assertEqual(updated_transaction.transaction, transaction.transaction)
        self.assertEqual(updated_transaction.amount, transaction.amount)
        self.assertEqual(updated_transaction.currency, transaction.currency)
        self.assertEqual(updated_transaction.bic, transaction.bic)
        self.assertEqual(updated_transaction.country_code, transaction.country_code)
        self.assertEqual(updated_transaction.communications, transaction.communications)
        self.assertEqual(updated_transaction.manually_assigned_category, True)
        self.assertEqual(updated_transaction.is_recurring, True)
        self.assertEqual(updated_transaction.is_advance_shared_account, True)
        self.assertEqual(updated_transaction.is_manually_reviewed, True)
        self.assertEqual(updated_transaction.category, category2)
        # save again to ensure we don't have duplicates
        serializer.save()
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(BankAccount.objects.count(), 1)
        self.assertEqual(Counterparty.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(updated_transaction.bank_account.users.count(), 1)
        self.assertEqual(updated_transaction.counterparty.users.count(), 1)


class SimplifiedCategorySerializerTests(TestCase):

    def test(self):
        category_tree = CategoryTreeProvider().provide(TransactionTypeEnum.EXPENSES)
        serializer = SimplifiedCategorySerializer(category_tree.root)
        actual_dict = to_dict(serializer.data)
        expected_dict = load_expected_as_dict('expenses_categories_simplified.json')
        self.assertDictEqual(expected_dict, actual_dict)


class BudgetTreeSerializerTests(TestCase):
    def setUp(self):
        self.maxDiff = None

    def test(self):

        def set_node_id_to_none(node:Dict):
            node['budget_tree_node_id'] = None
            if node.get('children'):
                for child in node['children']:
                    set_node_id_to_none(child)

        bank_account = baker.make(BankAccount)
        budget_tree = BudgetTreeProvider().provide(bank_account)
        data = BudgetTreeSerializer(budget_tree).data
        actual_data = to_dict(data).pop('root')
        expected_data = load_expected_as_dict('budget_tree.json').pop('root')
        set_node_id_to_none(expected_data)
        set_node_id_to_none(actual_data)
        self.assertDictEqual(expected_data, actual_data)
