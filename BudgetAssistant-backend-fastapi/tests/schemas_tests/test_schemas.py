"""Tests for Pydantic schemas."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from common.enums import TransactionTypeEnum
from schemas import (
    BankAccountCreate,
    BankAccountRead,
    BudgetTreeNodeCreate,
    BudgetTreeNodeRead,
    CategoryRead,
    CounterpartyRead,
    RuleSetWrapperCreate,
    RuleSetWrapperRead,
    TransactionCreate,
    TransactionRead,
    UserCreate,
    UserRead,
    UserUpdate,
)


class TestUserSchemas:
    """Test cases for User schemas."""

    def test_user_create_valid(self):
        """Test creating a valid UserCreate schema."""
        user = UserCreate(
            email="test@example.com",
            password="securepassword",
            first_name="Test",
            last_name="User",
        )
        assert user.email == "test@example.com"
        assert user.password == "securepassword"

    def test_user_create_invalid_email(self):
        """Test that invalid email raises validation error."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="securepassword",
            )

    def test_user_create_defaults(self):
        """Test UserCreate default values."""
        user = UserCreate(
            email="test@example.com",
            password="password",
        )
        assert user.first_name == ""
        assert user.last_name == ""

    def test_user_read_from_attributes(self):
        """Test UserRead with from_attributes config."""

        # Simulate ORM-like object
        class MockUser:
            id = 1
            email = "test@example.com"
            first_name = "Test"
            last_name = "User"
            is_active = True

        user_read = UserRead.model_validate(MockUser())
        assert user_read.id == 1
        assert user_read.email == "test@example.com"
        assert user_read.is_active is True

    def test_user_update_all_optional(self):
        """Test that all UserUpdate fields are optional."""
        user_update = UserUpdate()
        assert user_update.email is None
        assert user_update.first_name is None
        assert user_update.last_name is None
        assert user_update.is_active is None
        assert user_update.password is None

    def test_user_update_partial(self):
        """Test partial update with UserUpdate."""
        user_update = UserUpdate(email="new@example.com")
        assert user_update.email == "new@example.com"
        assert user_update.first_name is None


class TestBankAccountSchemas:
    """Test cases for BankAccount schemas."""

    def test_bank_account_create_valid(self):
        """Test creating a valid BankAccountCreate schema."""
        account = BankAccountCreate(
            account_number="123456789",
            alias="Savings",
        )
        assert account.account_number == "123456789"
        assert account.alias == "Savings"

    def test_bank_account_create_without_alias(self):
        """Test BankAccountCreate without alias."""
        account = BankAccountCreate(account_number="123456789")
        assert account.alias is None

    def test_bank_account_read_from_attributes(self):
        """Test BankAccountRead with from_attributes config."""

        class MockBankAccount:
            account_number = "123456789"
            alias = "Checking"

        account_read = BankAccountRead.model_validate(MockBankAccount())
        assert account_read.account_number == "123456789"
        assert account_read.alias == "Checking"


class TestTransactionSchemas:
    """Test cases for Transaction schemas."""

    def test_transaction_create_valid(self):
        """Test creating a valid TransactionCreate schema."""
        transaction = TransactionCreate(
            bank_account_id="123456",
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty_id="counterparty1",
            transaction_number="txn_001",
            currency_date=date(2023, 10, 1),
            amount=100.0,
            currency="USD",
            country_code="US",
        )
        assert transaction.bank_account_id == "123456"
        assert transaction.amount == 100.0
        assert transaction.currency == "USD"

    def test_transaction_create_with_optional_fields(self):
        """Test TransactionCreate with optional fields."""
        transaction = TransactionCreate(
            bank_account_id="123456",
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty_id="counterparty1",
            transaction_number="txn_001",
            currency_date=date(2023, 10, 1),
            amount=-50.0,
            currency="EUR",
            country_code="DE",
            transaction="Payment for services",
            bic="DEUTDEFF",
            communications="Invoice #12345",
            category_id=1,
        )
        assert transaction.transaction == "Payment for services"
        assert transaction.bic == "DEUTDEFF"
        assert transaction.category_id == 1

    def test_transaction_read_get_transaction_type_revenue(self):
        """Test TransactionRead get_transaction_type for revenue."""
        transaction_read = TransactionRead(
            transaction_id="txn_001",
            bank_account=BankAccountRead(account_number="123456", alias=None),
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty=CounterpartyRead(name="counterparty1", account_number="CP123"),
            transaction_number="txn_001",
            currency_date=date(2023, 10, 1),
            amount=100.0,
            currency="USD",
            country_code="US",
            manually_assigned_category=False,
            is_recurring=False,
            is_advance_shared_account=False,
            upload_timestamp=datetime.now(),
            is_manually_reviewed=False,
        )
        assert transaction_read.get_transaction_type() == TransactionTypeEnum.REVENUE

    def test_transaction_read_get_transaction_type_expenses(self):
        """Test TransactionRead get_transaction_type for expenses."""
        transaction_read = TransactionRead(
            transaction_id="txn_001",
            bank_account=BankAccountRead(account_number="123456", alias=None),
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty=CounterpartyRead(name="counterparty1", account_number="CP123"),
            transaction_number="txn_001",
            currency_date=date(2023, 10, 1),
            amount=-100.0,
            currency="USD",
            country_code="US",
            manually_assigned_category=False,
            is_recurring=False,
            is_advance_shared_account=False,
            upload_timestamp=datetime.now(),
            is_manually_reviewed=False,
        )
        assert transaction_read.get_transaction_type() == TransactionTypeEnum.EXPENSES


class TestCategorySchemas:
    """Test cases for Category schemas."""

    def test_category_read_valid(self):
        """Test creating a valid CategoryRead schema."""
        category = CategoryRead(
            id=1,
            name="Test Category",
            qualified_name="test",
            is_root=False,
            type=TransactionTypeEnum.EXPENSES,
        )
        assert category.id == 1
        assert category.name == "Test Category"
        assert category.type == TransactionTypeEnum.EXPENSES

    def test_category_read_with_children(self):
        """Test CategoryRead with children."""
        child = CategoryRead(
            id=2,
            name="Child Category",
            qualified_name="parent#child",
            is_root=False,
            type=TransactionTypeEnum.EXPENSES,
            parent_id=1,
        )
        parent = CategoryRead(
            id=1,
            name="Parent Category",
            qualified_name="parent",
            is_root=True,
            type=TransactionTypeEnum.EXPENSES,
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].name == "Child Category"


class TestBudgetSchemas:
    """Test cases for Budget schemas."""

    def test_budget_tree_node_create_valid(self):
        """Test creating a valid BudgetTreeNodeCreate schema."""
        node = BudgetTreeNodeCreate(
            amount=100,
            category_id=1,
        )
        assert node.amount == 100
        assert node.category_id == 1

    def test_budget_tree_node_create_defaults(self):
        """Test BudgetTreeNodeCreate default values."""
        node = BudgetTreeNodeCreate()
        assert node.amount == 0
        assert node.category_id is None
        assert node.parent_id is None

    def test_budget_tree_node_read_with_children(self):
        """Test BudgetTreeNodeRead with children."""
        child = BudgetTreeNodeRead(
            id=2,
            amount=50,
            category_id=2,
            parent_id=1,
        )
        parent = BudgetTreeNodeRead(
            id=1,
            amount=100,
            category_id=1,
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].amount == 50


class TestRuleSetWrapperSchemas:
    """Test cases for RuleSetWrapper schemas."""

    def test_rule_set_wrapper_create_valid(self):
        """Test creating a valid RuleSetWrapperCreate schema."""
        wrapper = RuleSetWrapperCreate(
            category_id=1,
            rule_set={"condition": "AND", "rules": []},
        )
        assert wrapper.category_id == 1
        assert wrapper.rule_set["condition"] == "AND"

    def test_rule_set_wrapper_create_with_users(self):
        """Test RuleSetWrapperCreate with user IDs."""
        wrapper = RuleSetWrapperCreate(
            category_id=1,
            rule_set={"condition": "OR", "rules": []},
            user_ids=[1, 2, 3],
        )
        assert len(wrapper.user_ids) == 3

    def test_rule_set_wrapper_read_valid(self):
        """Test creating a valid RuleSetWrapperRead schema."""
        wrapper = RuleSetWrapperRead(
            id=1,
            category_id=1,
            rule_set={"condition": "AND", "rules": [{"field": "test"}]},
        )
        assert wrapper.id == 1
        assert len(wrapper.rule_set["rules"]) == 1
