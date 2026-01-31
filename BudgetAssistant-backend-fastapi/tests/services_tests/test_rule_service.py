"""Tests for RuleSetWrappersPostOrderTraverser."""

import json
from datetime import date

import pytest

from common.enums import TransactionTypeEnum
from models import Category, RuleSetWrapper, Transaction
from models.category import CategoryTree
from models.rules import (
    ANY_OF,
    CONTAINS_STRING_OP,
    Rule,
    RuleSet,
)
from services.rule_service import RuleSetWrappersPostOrderTraverser


@pytest.fixture
def sample_expenses_category_tree() -> CategoryTree:
    """Create a sample expenses category tree for testing."""
    # Root category
    root = Category(
        id=1,
        name="Expenses",
        qualified_name="Expenses",
        is_root=True,
        type=TransactionTypeEnum.EXPENSES,
    )

    # Child categories
    groceries = Category(
        id=2,
        name="Groceries",
        qualified_name="Expenses > Groceries",
        is_root=False,
        type=TransactionTypeEnum.EXPENSES,
        parent_id=1,
    )
    groceries.parent = root

    transport = Category(
        id=3,
        name="Transport",
        qualified_name="Expenses > Transport",
        is_root=False,
        type=TransactionTypeEnum.EXPENSES,
        parent_id=1,
    )
    transport.parent = root

    # Grandchild category
    fuel = Category(
        id=4,
        name="Fuel",
        qualified_name="Expenses > Transport > Fuel",
        is_root=False,
        type=TransactionTypeEnum.EXPENSES,
        parent_id=3,
    )
    fuel.parent = transport

    # Set up children relationships
    root.children = [groceries, transport]
    groceries.children = []
    transport.children = [fuel]
    fuel.children = []

    # Create category tree
    tree = CategoryTree(
        id=1,
        type=TransactionTypeEnum.EXPENSES,
        root_id=1,
    )
    tree.root = root

    return tree


@pytest.fixture
def sample_revenue_category_tree() -> CategoryTree:
    """Create a sample revenue category tree for testing."""
    root = Category(
        id=10,
        name="Revenue",
        qualified_name="Revenue",
        is_root=True,
        type=TransactionTypeEnum.REVENUE,
    )

    salary = Category(
        id=11,
        name="Salary",
        qualified_name="Revenue > Salary",
        is_root=False,
        type=TransactionTypeEnum.REVENUE,
        parent_id=10,
    )
    salary.parent = root

    root.children = [salary]
    salary.children = []

    tree = CategoryTree(
        id=2,
        type=TransactionTypeEnum.REVENUE,
        root_id=10,
    )
    tree.root = root

    return tree


@pytest.fixture
def sample_transaction() -> Transaction:
    """Create a sample transaction for testing."""
    from models import BankAccount, Counterparty

    bank_account = BankAccount(
        account_number="BE123456789",
        alias="Test Account",
    )
    counterparty = Counterparty(
        name="Supermarket ABC",
        account_number="BE987654321",
    )

    return Transaction(
        transaction_id="test123",
        booking_date=date.today(),
        statement_number="001",
        transaction_number="TXN001",
        transaction="Purchase",
        currency_date=date.today(),
        amount=-50.00,  # Negative = expense
        currency="EUR",
        country_code="BE",
        communications="Groceries purchase at Supermarket ABC",
        bank_account_id="BE123456789",
        counterparty_id="Supermarket ABC",
        bank_account=bank_account,
        counterparty=counterparty,
    )


def create_rule_set_wrapper_with_rule(
    category: Category, rule_values: list[str]
) -> RuleSetWrapper:
    """Helper to create a RuleSetWrapper with a simple rule."""
    rule = Rule(
        field=["communications"],
        field_type="string",
        value=rule_values,
        value_match_type=ANY_OF,
        operator=CONTAINS_STRING_OP,
        clazz="Rule",
        type=category.type,
    )
    rule_set = RuleSet(
        condition="OR",
        rules=[rule],
        is_child=False,
        clazz="RuleSet",
        type=category.type,
    )
    wrapper = RuleSetWrapper(
        id=category.id,
        category_id=category.id,
        rule_set_json=json.dumps(rule_set.model_dump()),
    )
    wrapper.category = category
    return wrapper


class TestRuleSetWrappersPostOrderTraverser:
    """Tests for RuleSetWrappersPostOrderTraverser."""

    def test_init_creates_graphs(
        self,
        sample_expenses_category_tree: CategoryTree,
        sample_revenue_category_tree: CategoryTree,
    ):
        """Test that initialization creates NetworkX graphs."""
        traverser = RuleSetWrappersPostOrderTraverser(
            expenses_category_tree=sample_expenses_category_tree,
            revenue_category_tree=sample_revenue_category_tree,
            rule_set_wrappers=[],
        )

        assert traverser.expenses_category_tree is not None
        assert traverser.revenue_category_tree is not None
        # Expenses tree has 4 nodes (root, groceries, transport, fuel)
        assert len(traverser.expenses_category_tree.nodes()) == 4
        # Revenue tree has 2 nodes (root, salary)
        assert len(traverser.revenue_category_tree.nodes()) == 2

    def test_traverse_without_transaction_raises_error(
        self,
        sample_expenses_category_tree: CategoryTree,
        sample_revenue_category_tree: CategoryTree,
    ):
        """Test that traversing without setting transaction raises ValueError."""
        traverser = RuleSetWrappersPostOrderTraverser(
            expenses_category_tree=sample_expenses_category_tree,
            revenue_category_tree=sample_revenue_category_tree,
            rule_set_wrappers=[],
        )

        with pytest.raises(ValueError, match="Transaction must be set"):
            traverser.traverse()

    def test_traverse_with_no_matching_rules(
        self,
        sample_expenses_category_tree: CategoryTree,
        sample_revenue_category_tree: CategoryTree,
        sample_transaction: Transaction,
    ):
        """Test traversal when no rules match."""
        traverser = RuleSetWrappersPostOrderTraverser(
            expenses_category_tree=sample_expenses_category_tree,
            revenue_category_tree=sample_revenue_category_tree,
            rule_set_wrappers=[],
        )
        traverser.set_current_transaction(sample_transaction)

        result = traverser.traverse()
        assert result is None

    def test_traverse_matches_leaf_category(
        self,
        sample_expenses_category_tree: CategoryTree,
        sample_revenue_category_tree: CategoryTree,
        sample_transaction: Transaction,
    ):
        """Test that post-order traversal matches leaf categories first."""
        # Create a rule for groceries that should match
        groceries = sample_expenses_category_tree.root.children[0]  # Groceries
        wrapper = create_rule_set_wrapper_with_rule(groceries, ["Groceries"])

        traverser = RuleSetWrappersPostOrderTraverser(
            expenses_category_tree=sample_expenses_category_tree,
            revenue_category_tree=sample_revenue_category_tree,
            rule_set_wrappers=[wrapper],
        )
        traverser.set_current_transaction(sample_transaction)

        result = traverser.traverse()

        assert result is not None
        assert result.name == "Groceries"
        assert sample_transaction.category == groceries

    def test_traverse_uses_correct_tree_for_expense(
        self,
        sample_expenses_category_tree: CategoryTree,
        sample_revenue_category_tree: CategoryTree,
        sample_transaction: Transaction,
    ):
        """Test that expense transactions use expense tree."""
        # Transaction has negative amount, so it's an expense
        assert sample_transaction.get_transaction_type() == TransactionTypeEnum.EXPENSES

        traverser = RuleSetWrappersPostOrderTraverser(
            expenses_category_tree=sample_expenses_category_tree,
            revenue_category_tree=sample_revenue_category_tree,
            rule_set_wrappers=[],
        )
        traverser.set_current_transaction(sample_transaction)

        tree = traverser.get_category_tree()
        root = traverser.get_root_category()

        assert tree == traverser.expenses_category_tree
        assert root.name == "Expenses"

    def test_traverse_uses_correct_tree_for_revenue(
        self,
        sample_expenses_category_tree: CategoryTree,
        sample_revenue_category_tree: CategoryTree,
        sample_transaction: Transaction,
    ):
        """Test that revenue transactions use revenue tree."""
        # Change to positive amount for revenue
        sample_transaction.amount = 1000.00
        assert sample_transaction.get_transaction_type() == TransactionTypeEnum.REVENUE

        traverser = RuleSetWrappersPostOrderTraverser(
            expenses_category_tree=sample_expenses_category_tree,
            revenue_category_tree=sample_revenue_category_tree,
            rule_set_wrappers=[],
        )
        traverser.set_current_transaction(sample_transaction)

        tree = traverser.get_category_tree()
        root = traverser.get_root_category()

        assert tree == traverser.revenue_category_tree
        assert root.name == "Revenue"

    def test_post_order_traversal_checks_children_before_parent(
        self,
        sample_expenses_category_tree: CategoryTree,
        sample_revenue_category_tree: CategoryTree,
        sample_transaction: Transaction,
    ):
        """Test that post-order traversal evaluates children before parents."""
        # Both transport and fuel could match, but fuel (child) should be checked first
        transport = sample_expenses_category_tree.root.children[1]  # Transport
        fuel = transport.children[0]  # Fuel

        # Create rules for both
        transport_wrapper = create_rule_set_wrapper_with_rule(transport, ["fuel"])
        fuel_wrapper = create_rule_set_wrapper_with_rule(fuel, ["fuel"])

        # Modify transaction to match fuel
        sample_transaction.communications = "Fuel station purchase"

        traverser = RuleSetWrappersPostOrderTraverser(
            expenses_category_tree=sample_expenses_category_tree,
            revenue_category_tree=sample_revenue_category_tree,
            rule_set_wrappers=[transport_wrapper, fuel_wrapper],
        )
        traverser.set_current_transaction(sample_transaction)

        result = traverser.traverse()

        # Should match Fuel (more specific) because it's checked first in post-order
        assert result is not None
        assert result.name == "Fuel"


class TestRuleSetWrapperGetRuleSet:
    """Tests for RuleSetWrapper.get_rule_set() method."""

    def test_get_rule_set_returns_none_for_empty_json(self):
        """Test that empty JSON returns None."""
        wrapper = RuleSetWrapper(id=1, rule_set_json="{}")
        assert wrapper.get_rule_set() is None

    def test_get_rule_set_returns_none_for_invalid_json(self):
        """Test that invalid JSON returns None."""
        wrapper = RuleSetWrapper(id=1, rule_set_json="not valid json")
        assert wrapper.get_rule_set() is None

    def test_get_rule_set_returns_rule_set_object(self):
        """Test that valid JSON returns a RuleSet object."""
        rule_set = RuleSet(
            condition="OR",
            rules=[
                Rule(
                    field=["communications"],
                    field_type="string",
                    value=["test"],
                    value_match_type=ANY_OF,
                    operator=CONTAINS_STRING_OP,
                    clazz="Rule",
                    type=TransactionTypeEnum.EXPENSES,
                )
            ],
            is_child=False,
            clazz="RuleSet",
            type=TransactionTypeEnum.EXPENSES,
        )
        wrapper = RuleSetWrapper(id=1, rule_set_json=json.dumps(rule_set.model_dump()))

        result = wrapper.get_rule_set()

        assert result is not None
        assert isinstance(result, RuleSet)
        assert result.condition == "OR"
        assert len(result.rules) == 1

    def test_set_rule_set_stores_json(self):
        """Test that set_rule_set stores the rule set as JSON."""
        wrapper = RuleSetWrapper(id=1, rule_set_json="{}")
        rule_set = RuleSet(
            condition="AND",
            rules=[],
            is_child=False,
            clazz="RuleSet",
            type=TransactionTypeEnum.EXPENSES,
        )

        wrapper.set_rule_set(rule_set)

        assert wrapper.rule_set_json != "{}"
        # Verify roundtrip
        result = wrapper.get_rule_set()
        assert result is not None
        assert result.condition == "AND"
