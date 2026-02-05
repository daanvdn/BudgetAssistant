"""Tests for analysis schemas."""

from datetime import date

from common.enums import TransactionTypeEnum
from schemas.analysis import (
    BudgetEntryResult,
    BudgetTrackerResult,
    CategoriesForAccountResponse,
    CategoryAmount,
    CategoryDetailsForPeriodResponse,
    CategoryDetailsForPeriodResult,
    ExpensesAndRevenueForPeriod,
    PeriodCategoryBreakdown,
    RevenueAndExpensesPerPeriodAndCategory,
    RevenueAndExpensesPerPeriodResponse,
)


class TestExpensesAndRevenueForPeriod:
    """Tests for ExpensesAndRevenueForPeriod."""

    def test_create_with_all_fields(self):
        """Test creating with all fields."""
        start = date(2023, 1, 1)
        end = date(2023, 1, 31)

        data = ExpensesAndRevenueForPeriod(
            period="2023-01",
            expenses=1500.50,
            revenue=2000.00,
            start_date=start,
            end_date=end,
        )

        assert data.period == "2023-01"
        assert data.expenses == 1500.50
        assert data.revenue == 2000.00
        assert data.start_date == start
        assert data.end_date == end

    def test_default_values(self):
        """Test default values for expenses and revenue."""
        start = date(2023, 1, 1)
        end = date(2023, 1, 31)

        data = ExpensesAndRevenueForPeriod(
            period="2023-01",
            start_date=start,
            end_date=end,
        )

        assert data.expenses == 0.0
        assert data.revenue == 0.0


class TestRevenueAndExpensesPerPeriodResponse:
    """Tests for RevenueAndExpensesPerPeriodResponse."""

    def test_empty_response(self):
        """Test empty response."""
        response = RevenueAndExpensesPerPeriodResponse(
            content=[],
            page=0,
            total_elements=0,
            size=0,
        )

        assert len(response.content) == 0
        assert response.total_elements == 0

    def test_with_content(self):
        """Test response with content."""
        start = date(2023, 1, 1)
        end = date(2023, 1, 31)

        content = [
            ExpensesAndRevenueForPeriod(
                period="2023-01",
                expenses=1000.0,
                revenue=1500.0,
                start_date=start,
                end_date=end,
            )
        ]

        response = RevenueAndExpensesPerPeriodResponse(
            content=content,
            page=0,
            total_elements=1,
            size=1,
        )

        assert len(response.content) == 1
        assert response.content[0].period == "2023-01"


class TestCategoryAmount:
    """Tests for CategoryAmount."""

    def test_create_category_amount(self):
        """Test creating CategoryAmount."""
        cat_amount = CategoryAmount(
            category_qualified_name="expenses/groceries",
            category_name="Groceries",
            amount=250.50,
        )

        assert cat_amount.category_qualified_name == "expenses/groceries"
        assert cat_amount.category_name == "Groceries"
        assert cat_amount.amount == 250.50

    def test_default_amount(self):
        """Test default amount value."""
        cat_amount = CategoryAmount(
            category_qualified_name="expenses/other",
            category_name="Other",
        )

        assert cat_amount.amount == 0.0


class TestPeriodCategoryBreakdown:
    """Tests for PeriodCategoryBreakdown."""

    def test_with_categories(self):
        """Test with category breakdown."""
        start = date(2023, 1, 1)
        end = date(2023, 1, 31)

        categories = [
            CategoryAmount(
                category_qualified_name="expenses/groceries",
                category_name="Groceries",
                amount=300.0,
            ),
            CategoryAmount(
                category_qualified_name="expenses/utilities",
                category_name="Utilities",
                amount=150.0,
            ),
        ]

        breakdown = PeriodCategoryBreakdown(
            period="2023-01",
            start_date=start,
            end_date=end,
            categories=categories,
            total=450.0,
        )

        assert breakdown.period == "2023-01"
        assert len(breakdown.categories) == 2
        assert breakdown.total == 450.0


class TestRevenueAndExpensesPerPeriodAndCategory:
    """Tests for RevenueAndExpensesPerPeriodAndCategory."""

    def test_empty_instance(self):
        """Test empty instance factory method."""
        empty = RevenueAndExpensesPerPeriodAndCategory.empty_instance()

        assert len(empty.periods) == 0
        assert len(empty.all_categories) == 0
        assert empty.transaction_type == TransactionTypeEnum.EXPENSES

    def test_with_data(self):
        """Test with actual data."""
        start = date(2023, 1, 1)
        end = date(2023, 1, 31)

        periods = [
            PeriodCategoryBreakdown(
                period="2023-01",
                start_date=start,
                end_date=end,
                categories=[],
                total=500.0,
            )
        ]

        response = RevenueAndExpensesPerPeriodAndCategory(
            periods=periods,
            all_categories=["groceries", "utilities"],
            transaction_type=TransactionTypeEnum.REVENUE,
        )

        assert len(response.periods) == 1
        assert len(response.all_categories) == 2
        assert response.transaction_type == TransactionTypeEnum.REVENUE


class TestCategoryDetailsForPeriodResponse:
    """Tests for CategoryDetailsForPeriodResponse."""

    def test_with_categories(self):
        """Test response with category details."""
        start = date(2023, 1, 1)
        end = date(2023, 1, 31)

        categories = [
            CategoryDetailsForPeriodResult(
                category_qualified_name="expenses/food",
                category_name="Food",
                amount=500.0,
                transaction_count=25,
                percentage=45.5,
            )
        ]

        response = CategoryDetailsForPeriodResponse(
            period="2023-01",
            start_date=start,
            end_date=end,
            categories=categories,
            total_amount=1100.0,
        )

        assert response.period == "2023-01"
        assert len(response.categories) == 1
        assert response.categories[0].transaction_count == 25
        assert response.total_amount == 1100.0


class TestBudgetTrackerResult:
    """Tests for BudgetTrackerResult."""

    def test_with_entries(self):
        """Test budget tracker result with entries."""
        start = date(2023, 1, 1)
        end = date(2023, 1, 31)

        entries = [
            BudgetEntryResult(
                category_qualified_name="expenses/groceries",
                category_name="Groceries",
                budgeted_amount=400.0,
                actual_amount=350.0,
                difference=50.0,
                percentage_used=87.5,
            ),
            BudgetEntryResult(
                category_qualified_name="expenses/utilities",
                category_name="Utilities",
                budgeted_amount=200.0,
                actual_amount=220.0,
                difference=-20.0,
                percentage_used=110.0,
            ),
        ]

        result = BudgetTrackerResult(
            period="2023-01",
            start_date=start,
            end_date=end,
            entries=entries,
            total_budgeted=600.0,
            total_actual=570.0,
            total_difference=30.0,
        )

        assert result.period == "2023-01"
        assert len(result.entries) == 2
        assert result.total_budgeted == 600.0
        assert result.total_actual == 570.0
        assert result.entries[1].percentage_used == 110.0


class TestCategoriesForAccountResponse:
    """Tests for CategoriesForAccountResponse."""

    def test_with_categories(self):
        """Test response with categories list."""
        response = CategoriesForAccountResponse(
            categories=["groceries", "utilities", "entertainment"],
            transaction_type=TransactionTypeEnum.EXPENSES,
        )

        assert len(response.categories) == 3
        assert "groceries" in response.categories
        assert response.transaction_type == TransactionTypeEnum.EXPENSES

    def test_empty_categories(self):
        """Test response with empty categories."""
        response = CategoriesForAccountResponse(
            categories=[],
            transaction_type=TransactionTypeEnum.REVENUE,
        )

        assert len(response.categories) == 0
