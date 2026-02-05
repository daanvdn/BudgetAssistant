"""Tests for budget tracking and category details in AnalysisService.

These tests cover:
- track_budget (with BudgetTree/BudgetTreeNode setup)
- get_category_details_for_period
- Edge cases like missing budget trees, empty queries
"""

from datetime import date
from typing import Dict, List, Tuple

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from common.enums import TransactionTypeEnum
from models import (
    BankAccount,
    BudgetTree,
    BudgetTreeNode,
    Category,
    Counterparty,
    Transaction,
)
from schemas.common import Grouping, RevenueExpensesQuery
from services.analysis_service import AnalysisService


async def create_category_hierarchy(
    session: AsyncSession,
    transaction_type: TransactionTypeEnum = TransactionTypeEnum.EXPENSES,
) -> Dict[str, Category]:
    """Create a category hierarchy for testing.

    Creates:
    - root (root category)
      - food (child)
        - groceries (grandchild)
        - restaurants (grandchild)
      - transport (child)
        - fuel (grandchild)
        - public_transport (grandchild)

    Returns:
        Dict mapping category names to Category objects.
    """
    categories = {}

    # Root category
    root = Category(
        name="root",
        type=transaction_type,
        qualified_name="root",
        is_root=True,
    )
    session.add(root)
    await session.flush()
    categories["root"] = root

    # Food category
    food = Category(
        name="food",
        type=transaction_type,
        qualified_name="root#food",
        parent_id=root.id,
    )
    session.add(food)
    await session.flush()
    categories["food"] = food

    # Food children
    groceries = Category(
        name="groceries",
        type=transaction_type,
        qualified_name="root#food#groceries",
        parent_id=food.id,
    )
    restaurants = Category(
        name="restaurants",
        type=transaction_type,
        qualified_name="root#food#restaurants",
        parent_id=food.id,
    )
    session.add_all([groceries, restaurants])
    await session.flush()
    categories["groceries"] = groceries
    categories["restaurants"] = restaurants

    # Transport category
    transport = Category(
        name="transport",
        type=transaction_type,
        qualified_name="root#transport",
        parent_id=root.id,
    )
    session.add(transport)
    await session.flush()
    categories["transport"] = transport

    # Transport children
    fuel = Category(
        name="fuel",
        type=transaction_type,
        qualified_name="root#transport#fuel",
        parent_id=transport.id,
    )
    public_transport = Category(
        name="public_transport",
        type=transaction_type,
        qualified_name="root#transport#public_transport",
        parent_id=transport.id,
    )
    session.add_all([fuel, public_transport])
    await session.flush()
    categories["fuel"] = fuel
    categories["public_transport"] = public_transport

    await session.commit()
    return categories


async def create_budget_tree(
    session: AsyncSession,
    bank_account: BankAccount,
    categories: Dict[str, Category],
) -> Tuple[BudgetTree, Dict[str, BudgetTreeNode]]:
    """Create a budget tree with nodes for the given categories.

    Budget amounts:
    - root: 0 (just a container)
    - food: 500
      - groceries: 300
      - restaurants: 200
    - transport: 300
      - fuel: 200
      - public_transport: 100

    Returns:
        Tuple of (BudgetTree, dict mapping category names to BudgetTreeNode).
    """
    nodes = {}

    # Root node
    root_node = BudgetTreeNode(
        category_id=categories["root"].id,
        amount=0,
    )
    session.add(root_node)
    await session.flush()
    nodes["root"] = root_node

    # Food node
    food_node = BudgetTreeNode(
        category_id=categories["food"].id,
        amount=500,
        parent_id=root_node.id,
    )
    session.add(food_node)
    await session.flush()
    nodes["food"] = food_node

    # Groceries node
    groceries_node = BudgetTreeNode(
        category_id=categories["groceries"].id,
        amount=300,
        parent_id=food_node.id,
    )
    session.add(groceries_node)
    await session.flush()
    nodes["groceries"] = groceries_node

    # Restaurants node
    restaurants_node = BudgetTreeNode(
        category_id=categories["restaurants"].id,
        amount=200,
        parent_id=food_node.id,
    )
    session.add(restaurants_node)
    await session.flush()
    nodes["restaurants"] = restaurants_node

    # Transport node
    transport_node = BudgetTreeNode(
        category_id=categories["transport"].id,
        amount=300,
        parent_id=root_node.id,
    )
    session.add(transport_node)
    await session.flush()
    nodes["transport"] = transport_node

    # Fuel node
    fuel_node = BudgetTreeNode(
        category_id=categories["fuel"].id,
        amount=200,
        parent_id=transport_node.id,
    )
    session.add(fuel_node)
    await session.flush()
    nodes["fuel"] = fuel_node

    # Public transport node
    public_transport_node = BudgetTreeNode(
        category_id=categories["public_transport"].id,
        amount=100,
        parent_id=transport_node.id,
    )
    session.add(public_transport_node)
    await session.flush()
    nodes["public_transport"] = public_transport_node

    # Create budget tree
    budget_tree = BudgetTree(
        bank_account_id=bank_account.account_number,
        root_id=root_node.id,
        number_of_descendants=6,
    )
    session.add(budget_tree)
    await session.commit()

    return budget_tree, nodes


async def create_test_transactions(
    session: AsyncSession,
    bank_account: BankAccount,
    counterparty: Counterparty,
    categories: Dict[str, Category],
) -> List[Transaction]:
    """Create test transactions for budget tracking.

    Creates transactions in January 2024:
    - groceries: -150, -100 (total: -250)
    - restaurants: -50, -75 (total: -125)
    - fuel: -80, -60 (total: -140)
    - public_transport: -30 (total: -30)

    Returns:
        List of created transactions.
    """
    transactions = []

    tx_data = [
        ("groceries", -150, 1),
        ("groceries", -100, 5),
        ("restaurants", -50, 10),
        ("restaurants", -75, 15),
        ("fuel", -80, 8),
        ("fuel", -60, 20),
        ("public_transport", -30, 12),
    ]

    for idx, (cat_name, amount, day) in enumerate(tx_data):
        category = categories[cat_name]
        booking_date = date(2024, 1, day)

        tx = Transaction(
            transaction_id=f"TX_BUDGET_{idx}_{cat_name}",
            booking_date=booking_date,
            statement_number=f"STMT_BUDGET_{idx}",
            transaction_number=f"TXN_BUDGET_{idx}_{cat_name}",
            currency_date=booking_date,
            amount=float(amount),
            currency="EUR",
            country_code="BE",
            bank_account_id=bank_account.account_number,
            counterparty_id=counterparty.name,
            category_id=category.id,
        )
        session.add(tx)
        transactions.append(tx)

    await session.commit()
    return transactions


@pytest_asyncio.fixture
async def budget_test_data(
    async_session: AsyncSession,
) -> Tuple[
    BankAccount,
    Dict[str, Category],
    BudgetTree,
    Dict[str, BudgetTreeNode],
    List[Transaction],
]:
    """Fixture that creates all necessary data for budget tracking tests.

    Returns:
        Tuple of (bank_account, categories, budget_tree, budget_nodes, transactions).
    """
    # Create bank account (lowercase for normalization)
    bank_account = BankAccount(account_number="budget_test_123", alias="Budget Test Account")
    async_session.add(bank_account)
    await async_session.flush()

    # Create counterparty
    counterparty = Counterparty(name="budget_test_counterparty", account_number="CP_BUDGET")
    async_session.add(counterparty)
    await async_session.flush()

    # Create category hierarchy
    categories = await create_category_hierarchy(async_session)

    # Create budget tree
    budget_tree, budget_nodes = await create_budget_tree(async_session, bank_account, categories)

    # Create transactions
    transactions = await create_test_transactions(async_session, bank_account, counterparty, categories)

    return bank_account, categories, budget_tree, budget_nodes, transactions


@pytest.mark.asyncio
class TestTrackBudget:
    """Tests for AnalysisService.track_budget."""

    async def test_track_budget_returns_correct_totals(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test that track_budget returns correct budget vs actual totals."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.track_budget(query, async_session)

        assert result is not None
        assert result.period is not None

        # Total budgeted: 500 + 300 + 200 + 300 + 200 + 100 = 1600
        # (food + groceries + restaurants + transport + fuel + public_transport)
        # Note: We only count nodes with amount > 0
        expected_budgeted = 500 + 300 + 200 + 300 + 200 + 100
        assert result.total_budgeted == expected_budgeted

        # Total actual spending: 250 + 125 + 140 + 30 = 545
        expected_actual = 250 + 125 + 140 + 30
        assert result.total_actual == expected_actual

        # Difference: budgeted - actual
        assert result.total_difference == expected_budgeted - expected_actual

    async def test_track_budget_returns_entries_per_category(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test that track_budget returns entries for each budgeted category."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.track_budget(query, async_session)

        assert result is not None
        assert len(result.entries) > 0

        # Check that we have entries for categories with budget > 0
        entry_names = {e.category_name for e in result.entries}
        expected_names = {
            "food",
            "groceries",
            "restaurants",
            "transport",
            "fuel",
            "public_transport",
        }
        assert entry_names == expected_names

    async def test_track_budget_groceries_entry_details(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test that groceries budget entry has correct details."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.track_budget(query, async_session)

        groceries_entry = next((e for e in result.entries if e.category_name == "groceries"), None)

        assert groceries_entry is not None
        assert groceries_entry.budgeted_amount == 300
        assert groceries_entry.actual_amount == 250  # -150 + -100
        assert groceries_entry.difference == 50  # 300 - 250 (under budget)
        # percentage_used = (250 / 300) * 100 ≈ 83.33%
        assert abs(groceries_entry.percentage_used - 83.33) < 0.1

    async def test_track_budget_no_budget_tree_raises_error(
        self,
        async_session: AsyncSession,
    ):
        """Test that track_budget raises error when no budget tree exists."""
        # Create bank account without budget tree
        bank_account = BankAccount(account_number="no_budget_account", alias="No Budget")
        async_session.add(bank_account)
        await async_session.commit()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()

        with pytest.raises(ValueError, match="Budget tree.*does not exist"):
            await service.track_budget(query, async_session)

    async def test_track_budget_empty_query_returns_none(
        self,
        async_session: AsyncSession,
    ):
        """Test that empty query returns None."""
        query = RevenueExpensesQuery(
            account_number="",  # Empty account makes query empty
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.track_budget(query, async_session)

        assert result is None

    async def test_track_budget_no_transactions_shows_zero_actual(
        self,
        async_session: AsyncSession,
    ):
        """Test that budget tracking works when there are no transactions."""
        # Create bank account
        bank_account = BankAccount(account_number="empty_tx_account", alias="Empty TX")
        async_session.add(bank_account)
        await async_session.flush()

        # Create single category and budget
        category = Category(
            name="test_cat",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="test_cat",
        )
        async_session.add(category)
        await async_session.flush()

        root_node = BudgetTreeNode(category_id=category.id, amount=500)
        async_session.add(root_node)
        await async_session.flush()

        budget_tree = BudgetTree(
            bank_account_id=bank_account.account_number,
            root_id=root_node.id,
        )
        async_session.add(budget_tree)
        await async_session.commit()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.track_budget(query, async_session)

        assert result is not None
        assert result.total_budgeted == 500
        assert result.total_actual == 0
        assert result.total_difference == 500


@pytest.mark.asyncio
class TestGetCategoryDetailsForPeriod:
    """Tests for AnalysisService.get_category_details_for_period."""

    async def test_get_category_details_returns_breakdown(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test that category details returns correct breakdown."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.get_category_details_for_period(query, "root#food", async_session)

        assert result is not None
        assert result.period is not None
        assert len(result.categories) > 0

        # Food category includes groceries and restaurants
        # Total: 250 + 125 = 375
        assert result.total_amount == 375

    async def test_get_category_details_includes_child_categories(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test that category details includes child category transactions."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.get_category_details_for_period(query, "root#food", async_session)

        # Should have entries for both groceries and restaurants
        category_names = {c.category_name for c in result.categories}
        assert "groceries" in category_names
        assert "restaurants" in category_names

    async def test_get_category_details_calculates_percentages(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test that category details calculates correct percentages."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.get_category_details_for_period(query, "root#food", async_session)

        # Groceries: 250 / 375 * 100 ≈ 66.67%
        # Restaurants: 125 / 375 * 100 ≈ 33.33%
        groceries_detail = next((c for c in result.categories if c.category_name == "groceries"), None)
        restaurants_detail = next((c for c in result.categories if c.category_name == "restaurants"), None)

        assert groceries_detail is not None
        assert abs(groceries_detail.percentage - 66.67) < 0.1

        assert restaurants_detail is not None
        assert abs(restaurants_detail.percentage - 33.33) < 0.1

    async def test_get_category_details_includes_transaction_count(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test that category details includes transaction count."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.get_category_details_for_period(query, "root#food", async_session)

        groceries_detail = next((c for c in result.categories if c.category_name == "groceries"), None)

        assert groceries_detail is not None
        assert groceries_detail.transaction_count == 2  # Two groceries transactions

    async def test_get_category_details_invalid_category_raises_error(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test that invalid category raises error."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()

        with pytest.raises(ValueError, match="Category.*not found"):
            await service.get_category_details_for_period(query, "nonexistent#category", async_session)

    async def test_get_category_details_sorted_by_amount(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test that categories are sorted by amount descending."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.get_category_details_for_period(query, "root#food", async_session)

        # Categories should be sorted by amount descending
        amounts = [c.amount for c in result.categories]
        assert amounts == sorted(amounts, reverse=True)

    async def test_get_category_details_transport_category(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test category details for transport category."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.get_category_details_for_period(query, "root#transport", async_session)

        assert result is not None
        # Transport total: fuel (140) + public_transport (30) = 170
        assert result.total_amount == 170

        category_names = {c.category_name for c in result.categories}
        assert "fuel" in category_names
        assert "public_transport" in category_names

    async def test_get_category_details_leaf_category(
        self,
        async_session: AsyncSession,
        budget_test_data: Tuple[
            BankAccount,
            Dict[str, Category],
            BudgetTree,
            Dict[str, BudgetTreeNode],
            List[Transaction],
        ],
    ):
        """Test category details for a leaf category (no children)."""
        bank_account, categories, budget_tree, budget_nodes, transactions = budget_test_data

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.get_category_details_for_period(query, "root#food#groceries", async_session)

        assert result is not None
        assert result.total_amount == 250  # Only groceries transactions
        assert len(result.categories) == 1
        assert result.categories[0].category_name == "groceries"
        assert result.categories[0].percentage == 100.0
