from unittest.mock import patch

from django.db.utils import IntegrityError
from django.test import TestCase

from pybackend.commons import TransactionTypeEnum
from pybackend.models import BankAccount, BudgetTree, BudgetTreeNode, Category, CategoryTree, Counterparty, CustomUser, \
    Transaction, TreeNode
from model_bakery import baker

class TestCustomUser(TestCase):

    # Creating a CustomUser instance with valid data
    def test_create_custom_user_with_valid_data(self):
        user = CustomUser.objects.create(
            username='testuser',
            first_name='Test',
            last_name='User',
            password='securepassword123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.password, 'securepassword123')

    # Attempting to create a CustomUser with a duplicate username
    def test_create_custom_user_with_duplicate_username(self):
        CustomUser.objects.create(
            username='duplicateuser',
            first_name='First',
            last_name='User',
            password='password123'
        )
        with self.assertRaises(Exception):
            CustomUser.objects.create(
                username='duplicateuser',
                first_name='Second',
                last_name='User',
                password='password456'
            )

    # Retrieving a CustomUser by username should return the correct user
    def test_retrieve_custom_user_by_username(self):
        # Setup
        username = 'testuser'
        user = CustomUser.objects.create(
            username=username,
            first_name='Test',
            last_name='User',
            password='securepassword123'
        )

        # Execution
        retrieved_user = CustomUser.objects.find_user_by_username(username)

        # Assertion
        self.assertEqual(retrieved_user, user)

    # Converting a CustomUser to JSON should include all fields
    def test_custom_user_to_json_includes_all_fields(self):
        # Create a CustomUser instance
        user = CustomUser(
            username='testuser',
            first_name='Test',
            last_name='User',
            password='securepassword123'
        )

        # Convert CustomUser to JSON
        user_json = user.to_json() # ok

        # Check if all fields are included
        self.assertEqual(user_json['username'], 'testuser')
        self.assertEqual(user_json['first_name'], 'Test')
        self.assertEqual(user_json['last_name'], 'User')
        self.assertEqual(user_json['password'], 'securepassword123')

    # The __str__ method should return the username of the CustomUser
    def test_custom_user_to_string(self):
        user = CustomUser(username='testuser', first_name='Test', last_name='User', password='securepassword123')
        self.assertEqual(str(user), 'testuser')

    # Associating a BankAccount with a CustomUser should be successful
    def test_associate_bank_account_success(self):
        # Create a BankAccount
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')

        # Create a CustomUser
        custom_user = CustomUser.objects.create(username='testuser', first_name='Test', last_name='User',
                                                password='securepassword123')

        # Associate the BankAccount with the CustomUser
        custom_user.bank_accounts.add(bank_account)

        # Check if the association is successful
        self.assertIn(bank_account, custom_user.bank_accounts.all())

    # Creating a CustomUser with missing required fields should raise an error
    def test_create_custom_user_with_missing_fields(self):
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create(
                username='testuser',
                first_name='Test',
                last_name='User'
            )

    # Retrieving a non-existent CustomUser should return None
    def test_retrieve_non_existent_custom_user(self):
        result = CustomUser.objects.find_user_by_username('nonexistent_user')
        self.assertIsNone(result)

    # Updating a CustomUser's password should reflect in subsequent retrievals
    def test_update_custom_user_password_reflects(self):
        user = CustomUser.objects.create(
            username='testuser',
            first_name='Test',
            last_name='User',
            password='securepassword123'
        )
        new_password = 'newsecurepassword456'
        user.password = new_password
        self.assertEqual(user.password, new_password)

    # Associating a non-existent BankAccount with a CustomUser should fail
    def test_associating_non_existent_bank_account_should_fail(self):
        # Create a CustomUser
        user = CustomUser.objects.create(
            username='testuser',
            first_name='Test',
            last_name='User',
            password='securepassword123'
        )

        # Attempt to associate a non-existent BankAccount
        with self.assertRaises(BankAccount.DoesNotExist):
            user.bank_accounts.add(BankAccount.objects.get(account_number='non_existent_account'))

    # The UserManager should correctly validate user credentials
    def test_validate_user_credentials(self):
        # Setup
        username = 'testuser'
        password = 'securepassword123'
        user = CustomUser.objects.create(
            username=username,
            first_name='Test',
            last_name='User',
            password=password
        )

        # Mocking
        with patch('pybackend.models.UserManager.find_user_by_username_and_password') as mock_find_user:
            mock_find_user.return_value = user

            # Exercise
            validated_user = CustomUser.objects.find_user_if_valid(username, password)

            # Verify
            self.assertEqual(validated_user, user)

    # Removing a BankAccount from a CustomUser should not affect other users
    def test_remove_bank_account_no_affect_other_users(self):
        # Create a CustomUser
        user = CustomUser.objects.create(
            username='testuser',
            first_name='Test',
            last_name='User',
            password='securepassword123'
        )

        # Create a BankAccount
        bank_account = BankAccount.objects.create(
            account_number='123456789',
            alias='Savings Account'
        )

        # Add the BankAccount to the CustomUser
        user.bank_accounts.add(bank_account)

        # Create another CustomUser
        other_user = CustomUser.objects.create(
            username='otheruser',
            first_name='Other',
            last_name='User',
            password='anotherpassword123'
        )

        # Check if the BankAccount is associated with the first CustomUser
        self.assertIn(bank_account, user.bank_accounts.all())

        # Check if the BankAccount is not associated with the other CustomUser
        self.assertNotIn(bank_account, other_user.bank_accounts.all())

        # Remove the BankAccount from the first CustomUser
        user.bank_accounts.remove(bank_account)

        # Check if the BankAccount is not associated with the first CustomUser after removal
        self.assertNotIn(bank_account, user.bank_accounts.all())

        # Check if the BankAccount is still not associated with the other CustomUser after removal
        self.assertNotIn(bank_account, other_user.bank_accounts.all())

    # The related_name 'custom_users' should correctly link BankAccounts to CustomUsers
    def test_related_name_custom_users(self):
        # Create a BankAccount
        bank_account = BankAccount.objects.create(account_number='12345')

        # Create a CustomUser
        custom_user = CustomUser.objects.create(
            username='testuser',
            first_name='Test',
            last_name='User',
            password='securepassword123'
        )

        # Link the BankAccount to the CustomUser
        custom_user.bank_accounts.add(bank_account)

        # Check if the related_name 'custom_users' correctly links BankAccounts to CustomUsers
        self.assertEqual(bank_account.custom_users.first(), custom_user)


class TestBankAccount(TestCase):

    def test_create_bank_account_with_valid_data(self):
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')
        self.assertEqual(bank_account.account_number, '123456')
        self.assertEqual(bank_account.alias, 'Savings')

    def test_create_bank_account_with_duplicate_account_number(self):
        BankAccount.objects.create(account_number='123456', alias='Savings')
        with self.assertRaises(IntegrityError):
            BankAccount.objects.create(account_number='123456', alias='Savings')

    def test_to_json_includes_all_fields(self):
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')
        bank_account_json = bank_account.to_json()
        self.assertEqual(bank_account_json['account_number'], '123456')
        self.assertEqual(bank_account_json['alias'], 'Savings')

    def test_normalize_account_number_removes_spaces_and_lowercases(self):
        normalized_account_number = BankAccount.normalize_account_number(' 123 456 ')
        self.assertEqual(normalized_account_number, '123456')

    def test_str_method_returns_account_number(self):
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')
        self.assertEqual(str(bank_account), '123456')

    def test_add_multiple_users_to_bank_account(self):
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')

        user1 = CustomUser.objects.create(username='user1', first_name='Test1', last_name='User1', password='password1')
        user2 = CustomUser.objects.create(username='user2', first_name='Test2', last_name='User2', password='password2')
        user3 = CustomUser.objects.create(username='user3', first_name='Test3', last_name='User3', password='password3')

        bank_account.users.add(user1, user2, user3)

        self.assertIn(user1, bank_account.users.all())
        self.assertIn(user2, bank_account.users.all())
        self.assertIn(user3, bank_account.users.all())


class TestTransaction(TestCase):

    def test_create_transaction_with_valid_data(self):
        bank_account = baker.make(BankAccount, account_number='123456', alias='Savings')
        counterparty = baker.make(Counterparty, name='Counterparty1')
        category = baker.make(Category, name='Category1', type='EXPENSES')
        transaction = Transaction.objects.create(
            transaction_id='txn001',
            bank_account=bank_account,
            booking_date='2023-10-01',
            statement_number='stmt_001',
            counterparty=counterparty,
            transaction_number='txn_num_001',
            transaction='Test Transaction',
            currency_date='2023-10-01',
            amount=100.0,
            currency='USD',
            bic='BIC123',
            country_code='US',
            communications='Test communication',
            category=category
        )
        self.assertEqual(transaction.transaction_id,
                         f'{transaction.transaction_number}_{hash(bank_account.account_number)}')
        # check if the transaction is associated with the bank account
        self.assertEqual(transaction.bank_account, bank_account)
        # check if the transaction is associated with the counterparty
        self.assertEqual(transaction.counterparty, counterparty)
        # check if the transaction is associated with the category
        self.assertEqual(transaction.category, category)

    def test_create_transaction_with_duplicate_transaction_id(self):
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')
        counterparty = Counterparty.objects.create(name='Counterparty1')
        category = Category.objects.create(name='Category1', type='EXPENSES')
        transaction = Transaction.objects.create(transaction_id=None, bank_account=bank_account,
                                                 booking_date='2023-10-01',
                                                 statement_number='stmt_001', counterparty=counterparty,
                                                 transaction_number='txn_num_001', transaction='Test Transaction',
                                                 currency_date='2023-10-01', amount=100.0, currency='USD', bic='BIC123',
                                                 country_code='US', communications='Test communication',
                                                 category=category)
        self.assertIsNotNone(transaction.transaction_id)
        with self.assertRaises(IntegrityError):
            Transaction.objects.create(transaction_id=None, bank_account=bank_account,
                                       booking_date='2023-10-01',
                                       statement_number='stmt_001', counterparty=counterparty,
                                       transaction_number='txn_num_001', transaction='Test Transaction',
                                       currency_date='2023-10-01', amount=100.0, currency='USD', bic='BIC123',
                                       country_code='US', communications='Test communication',
                                       category=category)

    def test_get_transaction_type_returns_revenue_for_positive_amount(self):
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')
        counterparty = Counterparty.objects.create(name='Counterparty1')
        category = Category.objects.create(name='Category1', type='REVENUE')
        transaction = Transaction.objects.create(
            transaction_id='txn_001',
            bank_account=bank_account,
            booking_date='2023-10-01',
            statement_number='stmt_001',
            counterparty=counterparty,
            transaction_number='txn_num_001',
            transaction='Test Transaction',
            currency_date='2023-10-01',
            amount=100.0,
            currency='USD',
            bic='BIC123',
            country_code='US',
            communications='Test communication',
            category=category
        )
        self.assertEqual(transaction.get_transaction_type(), 'REVENUE')

    def test_get_transaction_type_returns_expenses_for_negative_amount(self):
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')
        counterparty = Counterparty.objects.create(name='Counterparty1')
        category = Category.objects.create(name='Category1', type='EXPENSES')
        transaction = Transaction.objects.create(
            transaction_id='txn_001',
            bank_account=bank_account,
            booking_date='2023-10-01',
            statement_number='stmt_001',
            counterparty=counterparty,
            transaction_number='txn_num_001',
            transaction='Test Transaction',
            currency_date='2023-10-01',
            amount=-100.0,
            currency='USD',
            bic='BIC123',
            country_code='US',
            communications='Test communication',
            category=category
        )
        self.assertEqual(transaction.get_transaction_type(), 'EXPENSES')

    # add a test to filter on an amount greater than or equal to a value
    def test_filter_on_amount_greater_than_or_equal_to(self):
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')
        counterparty = Counterparty.objects.create(name='Counterparty1')
        category = Category.objects.create(name='Category1', type='EXPENSES')
        transaction = Transaction.objects.create(
            transaction_id='txn_001',
            bank_account=bank_account,
            booking_date='2023-10-01',
            statement_number='stmt_001',
            counterparty=counterparty,
            transaction_number='txn_num_001',
            transaction='Test Transaction',
            currency_date='2023-10-01',
            amount=100.0,
            currency='USD',
            bic='BIC123',
            country_code='US',
            communications='Test communication',
            category=category
        )
        # add another transaction with another bank account
        bank_account2 = BankAccount.objects.create(account_number='123457', alias='Checking')
        counterparty2 = Counterparty.objects.create(name='Counterparty2')
        category2 = Category.objects.create(name='Category2', type='EXPENSES')
        transaction2 = Transaction.objects.create(
            transaction_id='txn_002',
            bank_account=bank_account2,
            booking_date='2023-10-01',
            statement_number='stmt_002',
            counterparty=counterparty2,
            transaction_number='txn_num_002',
            transaction='Test Transaction 2',
            currency_date='2023-10-01',
            amount=50.0,
            currency='USD',
            bic='BIC124',
            country_code='US',
            communications='Test communication 2',
            category=category2
        )

        transactions = Transaction.objects.filter(amount__gte=100.0, bank_account=bank_account)
        self.assertIn(transaction, transactions)
        self.assertNotIn(transaction2, transactions)


class TestCounterparty(TestCase):

    def test_create_counterparty_with_valid_data(self):
        counterparty = Counterparty.objects.create(name=' Counterparty   1 2  ')
        self.assertEqual(counterparty.name, 'counterparty 1 2')

    def test_create_counterparty_with_duplicate_name(self):
        Counterparty.objects.create(name=' Counterparty   1 2  ')
        with self.assertRaises(IntegrityError):
            Counterparty.objects.create(name='counterparty 1 2')

    def test_normalize_counterparty_name(self):
        counterparty = Counterparty.objects.create(name=' Counterparty   1 2  ')
        self.assertEqual(counterparty.name, 'counterparty 1 2')

    def test_to_string_returns_name(self):
        counterparty = Counterparty.objects.create(name=' Counterparty   1 2  ')
        self.assertEqual(str(counterparty), 'counterparty 1 2')

    def test_add_users_to_counterparty(self):
        counterparty = Counterparty.objects.create(name=' Counterparty   1 2  ')
        user1 = CustomUser.objects.create(username='user1', first_name='Test1', last_name='User1', password='password1',
                                          email='user1@example.com', is_active=True)
        user2 = CustomUser.objects.create(username='user2', first_name='Test2', last_name='User2', password='password2',
                                          email='user2@example.com', is_active=True)
        counterparty.users.add(user1, user2)
        self.assertIn(user1, counterparty.users.all())
        self.assertIn(user2, counterparty.users.all())


class TestCategory(TestCase):

    def test_create_category_with_valid_data(self):
        category = Category.objects.create(name='Test Category', type='EXPENSES')
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.type, 'EXPENSES')
        self.assertFalse(category.is_root)

    def test_get_qualified_name_returns_correct_hierarchy(self):
        root_category = Category.objects.create(name='Root', type='EXPENSES', is_root=True, qualified_name='root')
        child_category = Category.objects.create(name='Child', type='EXPENSES', parent=root_category, qualified_name='root#child')
        self.assertEqual(child_category.qualified_name, 'root#child')

    def test_add_child_category(self):
        root_category = baker.make(Category, name='Root', type='EXPENSES', is_root=True)
        child_category = baker.make(Category, name='Child', type='EXPENSES')
        root_category.add_child(child_category)
        self.assertEqual(child_category.parent, root_category)

    def test_no_category_object_returns_correct_instance(self):
        no_category = Category.no_category_object()
        self.assertEqual(no_category.name, Category.NO_CATEGORY_NAME)
        self.assertFalse(no_category.is_root)

    def test_category_equality_based_on_qualified_name(self):
        root_category = baker.make(Category, name='Root', type='EXPENSES', is_root=True)
        child_category1 = baker.make(Category, name='Child', type='EXPENSES', qualified_name='Child', parent=root_category)
        child_category2 = baker.make(Category, name='Child', type='EXPENSES', qualified_name='Child', parent=root_category)
        self.assertEqual(child_category1, child_category2)

    def test_category_hash_based_on_qualified_name(self):
        root_category = Category.objects.create(name='Root', type='EXPENSES', is_root=True, qualified_name='root')
        child_category = Category.objects.create(name='Child', type='EXPENSES', parent=root_category, qualified_name='root#child')
        self.assertEqual(hash(child_category), hash('root#child'))


class TestCategoryTree(TestCase):

    def test_create_category_tree_with_valid_data(self):
        root_category = baker.make(Category, name='Root', type='EXPENSES', is_root=True)
        category_tree = baker.make(CategoryTree, root=root_category, type='EXPENSES')
        self.assertEqual(category_tree.root, root_category)
        self.assertEqual(category_tree.type, 'EXPENSES')

    def test_create_category_tree_with_duplicate_root(self):
        root_category = Category.objects.create(name='Root', type='EXPENSES', is_root=True)
        CategoryTree.objects.create(root=root_category, type='EXPENSES')
        with self.assertRaises(IntegrityError):
            CategoryTree.objects.create(root=root_category, type='EXPENSES')

    def test_str_method_returns_correct_format(self):
        root_category = Category.objects.create(name='Root', type=TransactionTypeEnum.EXPENSES, is_root=True)
        category_tree = CategoryTree.objects.create(root=root_category, type=TransactionTypeEnum.EXPENSES)
        self.assertEqual('EXPENSES - Root', str(category_tree))

    def test_get_children_returns_correct_children(self):
        root_category = baker.make(Category, name='Root', type='EXPENSES', is_root=True)
        category_tree = baker.make(CategoryTree, root=root_category, type='EXPENSES')
        child_category = baker.make(Category, name='Child', type='EXPENSES', parent=root_category)
        root_category.add_child(child_category)
        self.assertIn(child_category, category_tree.root.cached_children)


class TestBudgetTreeNode(TestCase):

    def test_create_budget_tree_node_with_valid_data(self):
        category = baker.make(Category, name='Test Category', type='EXPENSES')
        budget_tree_node = baker.make(BudgetTreeNode, category=category, amount=100)
        self.assertEqual(budget_tree_node.category, category)
        self.assertEqual(budget_tree_node.amount, 100)

    def test_add_child_to_budget_tree_node(self):
        parent_category = baker.make(Category, name='Parent Category', type='EXPENSES')
        child_category = baker.make(Category, name='Child Category', type='EXPENSES')
        parent_node = baker.make(BudgetTreeNode, category=parent_category, amount=200)
        child_node = baker.make(BudgetTreeNode, category=child_category, amount=50)
        parent_node.add_child(child_node)
        self.assertIn(child_node, parent_node.cached_children)

    def test_get_children_returns_correct_children(self):
        parent_category = baker.make(Category, name='Parent Category', type='EXPENSES')
        child_category1 = baker.make(Category, name='Child Category 1', type='EXPENSES')
        child_category2 = baker.make(Category, name='Child Category 2', type='EXPENSES')
        parent_node = baker.make(BudgetTreeNode, category=parent_category, amount=200)
        child_node1 = baker.make(BudgetTreeNode, category=child_category1, amount=50,parent=parent_node)
        child_node2 = baker.make(BudgetTreeNode, category=child_category2, amount=75,parent=parent_node)
        self.assertIn(child_node1, parent_node.cached_children)
        self.assertIn(child_node2, parent_node.cached_children)

    def test_is_root_category_returns_true_for_root_node(self):
        root_category = Category.objects.create(name=Category.ROOT_NAME, type='EXPENSES')
        root_node = BudgetTreeNode.objects.create(category=root_category, amount=300)
        self.assertTrue(root_node.is_root_category())

    def test_is_root_category_returns_false_for_non_root_node(self):
        root_category = Category.objects.create(name=Category.ROOT_NAME, type='EXPENSES')
        child_category = Category.objects.create(name='Child Category', type='EXPENSES')
        root_node = BudgetTreeNode.objects.create(category=root_category, amount=300)
        child_node = BudgetTreeNode.objects.create(category=child_category, amount=100,
                                                   parent=root_node)
        self.assertFalse(child_node.is_root_category())

    def test_parent_node_is_root_returns_true_for_direct_child_of_root(self):
        root_category = Category.objects.create(name=Category.ROOT_NAME, type='EXPENSES')
        child_category = Category.objects.create(name='Child Category', type='EXPENSES')
        root_node = BudgetTreeNode.objects.create(category=root_category, amount=300)
        child_node = BudgetTreeNode.objects.create(category=child_category, amount=100,
                                                   parent=root_node)
        self.assertTrue(child_node.parent_node_is_root())

    def test_parent_node_is_root_returns_false_for_non_direct_child_of_root(self):
        root_category = Category.objects.create(name=Category.ROOT_NAME, type='EXPENSES')
        child_category = Category.objects.create(name='Child Category', type='EXPENSES')
        grandchild_category = Category.objects.create(name='Grandchild Category', type='EXPENSES')
        root_node = BudgetTreeNode.objects.create(category=root_category, amount=300)
        child_node = BudgetTreeNode.objects.create(category=child_category, amount=100,
                                                   parent=root_node)
        grandchild_node = BudgetTreeNode.objects.create(category=grandchild_category, amount=50,
                                                        parent=child_node)
        self.assertFalse(grandchild_node.parent_node_is_root())


class TestBudgetTree(TestCase):

    def test_create_budget_tree_with_valid_data(self):
        bank_account =  baker.make(BankAccount, account_number='123456', alias='Savings')
        root_node = baker.make(BudgetTreeNode, category=baker.make(Category, name='Root', type='EXPENSES'),
                                                  amount=100)
        budget_tree = baker.make(BudgetTree, bank_account=bank_account, root=root_node)
        self.assertEqual(budget_tree.bank_account, bank_account)
        self.assertEqual(budget_tree.root, root_node)

    def test_create_budget_tree_with_duplicate_id(self):
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')
        root_node = BudgetTreeNode.objects.create(category=Category.objects.create(name='Root', type='EXPENSES'),
                                                  amount=100)
        BudgetTree.objects.create(bank_account=bank_account, root=root_node)
        with self.assertRaises(IntegrityError):
            BudgetTree.objects.create(bank_account=bank_account, root=root_node)

    def test_str_method_returns_correct_format(self):
        bank_account = BankAccount.objects.create(account_number='123456', alias='Savings')
        root_node = BudgetTreeNode.objects.create(category=Category.objects.create(name='Root', type='EXPENSES'),
                                                  amount=100)
        budget_tree = BudgetTree.objects.create(bank_account=bank_account, root=root_node)
        self.assertEqual(str(budget_tree), bank_account.account_number)

    def test_get_children_returns_correct_children(self):
        bank_account = baker.make(BankAccount, account_number='123456', alias='Savings')
        root_node = baker.make(BudgetTreeNode, category=baker.make(Category,name='Root', type='EXPENSES'),amount=100)
        budget_tree = baker.make(BudgetTree, bank_account=bank_account, root=root_node)
        child_node = baker.make(BudgetTreeNode, category=baker.make(Category, name='Child', type='EXPENSES'),amount=50, parent=root_node)
        root_node.add_child(child_node)
        self.assertIn(child_node, budget_tree.cached_children)


