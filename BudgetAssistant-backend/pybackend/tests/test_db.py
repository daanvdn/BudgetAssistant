from datetime import datetime

from django.db import connection
from django.test import TestCase
from model_bakery import baker

from tests.utils import create_random_rule_set
from pybackend.commons import normalize_counterparty_name_or_account
from pybackend.models import BankAccount, BudgetTree, BudgetTreeNode, Category, CategoryTree, Counterparty, CustomUser, \
    Transaction
from pybackend.rules import RuleSet, RuleSetWrapper


class TestBankAccountManager(TestCase):

    def test_get_or_create_bank_account_creates_new_account(self):
        user = CustomUser.objects.create(username='testuser', password='password')
        account_number = '1234567890'
        bank_account = BankAccount.objects.get_or_create_bank_account(account_number, user)
        self.assertEqual(bank_account.account_number, account_number)
        self.assertIn(user, bank_account.users.all())

    def test_get_or_create_bank_account_adds_user_to_existing_account(self):
        user1 = CustomUser.objects.create(username='testuser1', password='password')
        user2 = CustomUser.objects.create(username='testuser2', password='password')
        account_number = '1234567890'
        bank_account = BankAccount.objects.create(account_number=account_number)
        bank_account.users.add(user1)
        bank_account = BankAccount.objects.get_or_create_bank_account(account_number, user2)
        self.assertIn(user2, bank_account.users.all())

    def test_normalize_account_number_removes_spaces_and_lowercases(self):
        account_number = ' 123 456 7890 '
        normalized = normalize_counterparty_name_or_account(account_number)
        self.assertEqual(normalized, '1234567890')

    def test_find_distinct_by_users_contains_returns_correct_accounts(self):
        user = CustomUser.objects.create(username='testuser', password='password')
        account1 = BankAccount.objects.create(account_number='1234567890')
        account2 = BankAccount.objects.create(account_number='0987654321')
        account1.users.add(user)
        accounts = BankAccount.objects.find_distinct_by_users_contains(user)
        self.assertEqual(list(accounts), [account1])


class BudgetTreeNodeManagerTests(TestCase):

    def test_get_budget_entry_with_children(self):
        root_category = baker.make(Category, name="root", is_root=True, type="EXPENSES")
        root_node = baker.make(BudgetTreeNode, category=root_category)
        child_category1 = baker.make(Category, name="child", type="EXPENSES")
        child_node1 =  baker.make(BudgetTreeNode, category=child_category1, parent=root_node)
        child_category2 = baker.make(Category, name="child2", type="EXPENSES")
        child_node2 = baker.make(BudgetTreeNode, category=child_category2, parent=root_node)
        root_node.add_child(child_node1)
        root_node.add_child(child_node2)
        result = BudgetTreeNode.objects.get_budget_entry_with_children(root_node.id)
        self.assertEqual(result, root_node)
        self.assertIn(child_node1, result.cached_children)
        self.assertIn(child_node2, result.cached_children)


class CategoryManagerTests(TestCase):

    def test_find_by_id_with_children(self):
        root_category = baker.make(Category, name="root", is_root=True, type="EXPENSES")
        child_category = baker.make(Category, name="child", type="EXPENSES", parent=root_category)
        root_category.add_child(child_category)

        result = Category.objects.find_by_id_with_children(root_category.id)
        self.assertEqual(result, root_category)
        self.assertIn(child_category, result.cached_children)

    def test_find_by_id_with_children_no_children(self):
        root_category = baker.make(Category, name="root", is_root=True, type="EXPENSES")

        result = Category.objects.find_by_id_with_children(root_category.id)
        self.assertEqual(result, root_category)
        self.assertEqual(len(result.cached_children), 0)

    def test_find_by_id_with_children_invalid_id_returns_none(self):
        result = Category.objects.find_by_id_with_children(-1)
        self.assertIsNone(result)


class CategoryTreeManagerTests(TestCase):

    def test_find_category_tree_by_type(self):
        root_category = Category.objects.create(name="root", is_root=True, type="EXPENSES")
        category_tree = CategoryTree.objects.create(root=root_category, type="EXPENSES")

        result = CategoryTree.objects.find_category_tree_by_type("EXPENSES")
        self.assertEqual(result, category_tree)

    def test_find_category_tree_by_type_no_result(self):
        result = CategoryTree.objects.find_category_tree_by_type("REVENUE")
        self.assertIsNone(result)

    def test_find_category_tree_by_type_invalid_type(self):
        with self.assertRaises(ValueError):
            CategoryTree.objects.find_category_tree_by_type("INVALID_TYPE")


class CounterpartyManagerTests(TestCase):

    def test_find_distinct_by_users_contains(self):
        user = CustomUser.objects.create(username="testuser", password="password")
        counterparty1 = Counterparty.objects.create(name="counterparty1")
        counterparty2 = Counterparty.objects.create(name="counterparty2")
        counterparty1.users.add(user)

        result = Counterparty.objects.find_distinct_by_users_contains(user)
        self.assertIn(counterparty1, result)
        self.assertNotIn(counterparty2, result)


class TransactionManagerTests(TestCase):

    def setUp(self):
        # Enable foreign key constraints in SQLite for this test
        #check if we are using sqlite
        if 'sqlite' in connection.settings_dict['ENGINE']:
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = ON;')

    def tearDown(self):
        # Delete all rows in all tables
        from django.core.management import call_command
        call_command('flush', '--noinput')

    def test_find_distinct_counterparty_names(self):
        counterparty1 = baker.make(Counterparty, name="counterparty1")
        counterparty2 = baker.make(Counterparty, name="counterparty2")
        bank_account = BankAccount.objects.create(account_number="123456")
        category = baker.make(Category, name="category", qualified_name="category")
        baker.make(Transaction, transaction_number="unique_number_1", category=category,
                                  counterparty=counterparty1, bank_account=bank_account)
        baker.make(Transaction, transaction_number="unique_number_2", category=category,
                                  counterparty=counterparty2, bank_account=bank_account)
        result = Transaction.objects.find_distinct_counterparty_names()
        self.assertIn("counterparty1", result)
        self.assertIn("counterparty2", result)

    def test_find_distinct_category_entities(self):
        category1 = baker.make(Category, name="category1", qualified_name="category1")
        category2 = baker.make(Category, name="category2", qualified_name="category2")
        bank_account = BankAccount.objects.create(account_number="123456")
        baker.make(Transaction, category=category1, bank_account=bank_account)
        baker.make(Transaction, category=category2, bank_account=bank_account)
        result = Transaction.objects.find_distinct_category_entities()
        self.assertIn("category1", result)
        self.assertIn("category2", result)

    def test_find_all_by_upload_timestamp(self):
        counterparty = Counterparty.objects.create(name="counterparty1", account_number="123")
        timestamp = datetime.now()
        # use baker prepare to create a transaction with a specific upload timestamp. The other values can be random
        transaction = baker.prepare(Transaction, counterparty=counterparty)
        transaction.upload_timestamp = timestamp
        transaction.save()
        transaction2 = baker.prepare(Transaction, counterparty=counterparty)
        transaction2.upload_timestamp = datetime.now()
        transaction2.save()
        result = Transaction.objects.find_all_by_upload_timestamp(timestamp)
        self.assertEqual(len(result), 1)
        actual = result[0]
        self.assertEqual(actual, transaction)

    def test_find_distinct_counterparty_account_numbers(self):
        counterparty1 = Counterparty.objects.create(name="counterparty1", account_number="123")
        counterparty2 = Counterparty.objects.create(name="counterparty2", account_number="456")
        bank_account = BankAccount.objects.create(account_number="123456")
        baker.make(Transaction, counterparty=counterparty1, bank_account=bank_account)
        baker.make(Transaction, counterparty=counterparty2, bank_account=bank_account)

        result = Transaction.objects.find_distinct_counterparty_account_numbers()
        self.assertIn("123", result)
        self.assertIn("456", result)

    def test_find_all_to_manually_review(self):
        bank_account = BankAccount.objects.create(account_number="123456")
        transaction1 = baker.prepare(Transaction, bank_account=bank_account, is_manually_reviewed=True)
        transaction1.save()

        transaction2 = baker.prepare(Transaction, bank_account=bank_account, is_manually_reviewed=False)
        transaction2.save()
        result = Transaction.objects.find_all_to_manually_review()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], transaction2)

class UserManagerTests(TestCase):

    def test_find_user_if_valid_valid_credentials(self):
        user = CustomUser.objects.create(username='testuser', password='password')
        user.set_password('password')
        user.save()
        found_user = CustomUser.objects.find_user_if_valid('testuser', 'password')
        self.assertEqual(found_user, user)

    def test_find_user_if_valid_invalid_credentials(self):
        user = CustomUser.objects.create(username='testuser', password='password')
        user.set_password('password')
        user.save()
        found_user = CustomUser.objects.find_user_if_valid('testuser', 'wrongpassword')
        self.assertIsNone(found_user)

    def test_find_user_by_username_existing_user(self):
        user = CustomUser.objects.create(username='testuser', password='password')
        found_user = CustomUser.objects.find_user_by_username('testuser')
        self.assertEqual(found_user, user)

    def test_find_user_by_username_nonexistent_user(self):
        found_user = CustomUser.objects.find_user_by_username('nonexistent')
        self.assertIsNone(found_user)

class BudgetTreeManagerTests(TestCase):

    def test_get_by_bank_account_existing_account(self):
        bank_account = BankAccount.objects.create(account_number='123456')
        budget_tree = BudgetTree.objects.create(bank_account=bank_account, root=BudgetTreeNode.objects.create())
        result = BudgetTree.objects.get_by_bank_account(bank_account)
        self.assertEqual(result, budget_tree)

    def test_get_by_bank_account_nonexistent_account(self):
        bank_account = BankAccount.objects.create(account_number='123456')
        with self.assertRaises(BudgetTree.DoesNotExist):
            BudgetTree.objects.get_by_bank_account(bank_account)

    def test_get_by_bank_account_null_account(self):
        with self.assertRaises(ValueError):
            BudgetTree.objects.get_by_bank_account(None)


class RuleSetWrapperManagerTests(TestCase):

    def test_exists_by_category_and_user_existing(self):
        rule_set: RuleSet = create_random_rule_set()
        user = CustomUser.objects.create(username='testuser', password='password')
        category = baker.make(Category, name='category', type='EXPENSES')
        expected = baker.make(RuleSetWrapper, category=category, users=[user], rule_set=rule_set)
        result = RuleSetWrapper.objects.exists_by_category_and_user(category, user)
        self.assertTrue(result)
        actual = RuleSetWrapper.objects.get(category=category, users=user)
        self.assertIsNotNone(actual)
        self.assertIsNotNone(actual.rule_set)
        self.assertIsInstance(actual.rule_set, RuleSet)
        #self.assertEqual(expected.rule_set, rule_set)
        self.assertEqual(actual.rule_set, rule_set)
        self.assertEqual(actual.category, category)
        self.assertEqual(actual.users.first(), user)
        self.assertEqual(actual, expected)

    def test_exists_by_category_and_user_nonexistent(self):
        user = CustomUser.objects.create(username='testuser', password='password')
        category = Category.objects.create(name='category', type='EXPENSES')
        result = RuleSetWrapper.objects.exists_by_category_and_user(category, user)
        self.assertFalse(result)


    def test_find_by_type_and_category_and_user_existing(self):
        rule_set = create_random_rule_set()
        user = baker.make(CustomUser, username='testuser', password='password')
        category = baker.make(Category, name='category', type='EXPENSES')
        expected = baker.make(RuleSetWrapper, category=category, users=[user], rule_set=rule_set)
        actual = RuleSetWrapper.objects.find_by_type_and_category_and_user('EXPENSES', user, category)
        self.assertEqual(actual, expected)
        self.assertIsNotNone(actual)
        self.assertIsNotNone(actual.rule_set)
        self.assertIsInstance(actual.rule_set, RuleSet)
        self.assertEqual(actual.rule_set, rule_set)
        self.assertEqual(actual.category, category)
        self.assertEqual(actual.users.first(), user)
        self.assertEqual(actual, expected)


    def test_find_by_type_and_category_and_user_nonexistent(self):
        user = CustomUser.objects.create(username='testuser', password='password')
        category = Category.objects.create(name='category', type='EXPENSES')
        result = RuleSetWrapper.objects.find_by_type_and_category_and_user('EXPENSES', user, category)
        self.assertIsNone(result)

    def test_find_by_user_existing(self):
        rule_set = create_random_rule_set()
        user = baker.make(CustomUser, username='testuser', password='password')
        category = baker.make(Category, name='category', type='EXPENSES')
        expected = baker.make(RuleSetWrapper, category=category, users=[user], rule_set=rule_set)
        actual = RuleSetWrapper.objects.find_by_user(user)
        self.assertIsNotNone(actual)
        self.assertIn(expected, actual)
        #get the first item of actual
        actual = actual[0]
        self.assertIsNotNone(actual.rule_set)
        self.assertIsInstance(actual.rule_set, RuleSet)
        self.assertEqual(actual.rule_set, rule_set)
        self.assertEqual(actual.category, category)
        self.assertEqual(actual.users.first(), user)
        self.assertEqual(actual, expected)


    def test_find_by_user_nonexistent(self):
        user = CustomUser.objects.create(username='testuser', password='password')
        result = RuleSetWrapper.objects.find_by_user(user)
        self.assertEqual(len(result), 0)