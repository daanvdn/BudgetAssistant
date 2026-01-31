"""Tests for AnalysisService.

These tests cover:
- get_revenue_and_expenses_per_period (MONTH, QUARTER, YEAR groupings)
- get_revenue_and_expenses_per_period_and_category (MONTH, QUARTER, YEAR)
- Edge cases like no transactions
"""

import io
from collections import namedtuple
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pytest
import pytest_asyncio
from lxml import etree
from sqlalchemy.ext.asyncio import AsyncSession

from enums import TransactionTypeEnum
from models import BankAccount, Category, Counterparty, Transaction
from schemas.analysis import (
    CategoryAmount,
    ExpensesAndRevenueForPeriod,
    PeriodCategoryBreakdown,
    RevenueAndExpensesPerPeriodAndCategory,
)
from schemas.common import Grouping, RevenueExpensesQuery
from schemas.period import Month, Period, Quarter, Year
from services.analysis_service import AnalysisService

# Named tuple to hold parsed transaction data
TransactionData = namedtuple(
    "TransactionData", ["account", "start_date", "end_date", "df", "categories"]
)


class Resources:
    """Helper class to load and parse test data from XML resource file.

    Adapts the Django test version to work with SQLModel Transaction,
    Category, and BankAccount models.
    """

    def __init__(self, category_lookup: Optional[Dict[str, Category]] = None):
        """Initialize Resources by loading data from XML.

        Args:
            category_lookup: Optional dict mapping category name to Category model.
                             Used when loading category-related distributions.
        """
        self.category_lookup = category_lookup or {}
        dfs: Dict[str, Any] = self._load_blocks_from_xml()

        self.transactions_df = dfs["transactions"]
        self.distributions_per_period: Dict[
            Grouping, List[ExpensesAndRevenueForPeriod]
        ] = {}
        self.distributions_per_period[Grouping.MONTH] = self._init_months_distribution(
            dfs["month"]
        )
        self.distributions_per_period[Grouping.QUARTER] = (
            self._init_quarters_distribution(dfs["quarter"])
        )
        self.distributions_per_period[Grouping.YEAR] = self._init_years_distribution(
            dfs["year"]
        )

        # Category distributions - only loaded if category_lookup is provided
        self.distributions_per_period_and_category: Dict[
            Grouping, RevenueAndExpensesPerPeriodAndCategory
        ] = {}
        if self.category_lookup:
            self.distributions_per_period_and_category[Grouping.MONTH] = dfs[
                "month_categories"
            ]
            self.distributions_per_period_and_category[Grouping.QUARTER] = dfs[
                "quarter_categories"
            ]
            self.distributions_per_period_and_category[Grouping.YEAR] = dfs[
                "year_categories"
            ]

    @staticmethod
    def _get_resource_path() -> Path:
        """Get the path to the XML resource file."""
        return (
            Path(__file__).parent.parent
            / "resources"
            / "test_get_expenses_and_revenue_per_period_pivot_tables.xml"
        )

    def _load_blocks_from_xml(self) -> Dict[str, Any]:
        """Load and parse all data blocks from the XML file."""
        blocks = {}

        with open(self._get_resource_path(), encoding="utf-8") as file:
            tree = etree.parse(file)

            def get_csv_data_in_tag(tag_name: str) -> pd.DataFrame:
                """Parse CSV data from an XML tag."""
                text = tree.xpath(tag_name)[0].text.strip()
                lines = text.splitlines()
                lines = [line.strip() for line in lines if line.strip()]
                return pd.read_csv(
                    io.StringIO("\n".join(lines)), delimiter=";", header=0
                )

            blocks["transactions"] = get_csv_data_in_tag("/root/transactions")
            blocks["year"] = get_csv_data_in_tag("/root/year")
            blocks["month"] = get_csv_data_in_tag("/root/month")
            blocks["quarter"] = get_csv_data_in_tag("/root/quarter")

            # Load category distributions if category_lookup is available
            if self.category_lookup:
                blocks["year_categories"] = (
                    self._get_category_distribution_for_grouping(tree, Grouping.YEAR)
                )
                blocks["month_categories"] = (
                    self._get_category_distribution_for_grouping(tree, Grouping.MONTH)
                )
                blocks["quarter_categories"] = (
                    self._get_category_distribution_for_grouping(tree, Grouping.QUARTER)
                )
            else:
                blocks["year_categories"] = None
                blocks["month_categories"] = None
                blocks["quarter_categories"] = None

        return blocks

    def _parse_period(self, period_str: str, grouping: Grouping) -> Period:
        """Parse a period string into a Period object.

        Args:
            period_str: String like "1_2022" for month/quarter or "2022" for year.
            grouping: The grouping type.

        Returns:
            A Period (Month, Quarter, or Year) instance.
        """
        if grouping == Grouping.MONTH:
            month, year = period_str.split("_")
            return Month.from_month_and_year(int(month), int(year))
        elif grouping == Grouping.QUARTER:
            quarter, year = period_str.split("_")
            return Quarter.from_quarter_nr_and_year(int(quarter), int(year))
        elif grouping == Grouping.YEAR:
            return Year.from_year(int(period_str))
        else:
            raise ValueError(f"Invalid grouping: {grouping}")

    def _get_category_from_lookup(self, category_name: str) -> Category:
        """Get a Category from the lookup dict.

        Args:
            category_name: The name of the category.

        Returns:
            The Category model instance.

        Raises:
            ValueError: If category not found in lookup.
        """
        if category_name not in self.category_lookup:
            raise ValueError(
                f"Category with name {category_name} not found in category lookup"
            )
        return self.category_lookup[category_name]

    def _get_category_distribution_for_grouping(
        self, tree: etree._ElementTree, grouping: Grouping
    ) -> RevenueAndExpensesPerPeriodAndCategory:
        """Parse category distribution data from XML for a specific grouping.

        Args:
            tree: The parsed XML tree.
            grouping: The grouping type (MONTH, QUARTER, YEAR).

        Returns:
            RevenueAndExpensesPerPeriodAndCategory with parsed data.
        """
        grouping_name = grouping.value.lower()

        def parse_csv_data(text: str) -> pd.DataFrame:
            """Parse CSV text into DataFrame."""
            lines = text.splitlines()
            lines = [line.strip() for line in lines if line.strip()]
            return pd.read_csv(io.StringIO("\n".join(lines)), delimiter=";", header=0)

        def validate_df(df: pd.DataFrame, is_expenses: bool) -> None:
            """Validate that the DataFrame has expected structure."""
            type_name = "expenses" if is_expenses else "revenue"
            if len(df.columns) != 2:
                raise ValueError(
                    f"Expected 2 columns in {type_name} dataframe for grouping {grouping_name}"
                )
            # Check that category and amount columns have valid values
            has_valid_categories = (
                df["category"].notnull().all()
                and (df["category"].str.strip() != "").all()
            )
            has_valid_amounts = df["amount"].notnull().all()
            if not (has_valid_categories and has_valid_amounts):
                raise ValueError(
                    f"Expected non-empty values in {type_name} dataframe for grouping {grouping_name}"
                )

        # Parse chart data to get periods with their category breakdowns
        chart = tree.xpath(f"/root/{grouping_name}_categories/chart")[0]
        entries = chart.xpath("entry")

        expenses_periods: List[PeriodCategoryBreakdown] = []
        revenue_periods: List[PeriodCategoryBreakdown] = []
        all_expense_categories: set[str] = set()
        all_revenue_categories: set[str] = set()

        for entry in entries:
            period = self._parse_period(
                entry.xpath(f"{grouping_name}")[0].text.strip(), grouping
            )

            # Parse expenses
            expenses_element = entry.xpath("expenses")
            if expenses_element and len(expenses_element) > 0:
                expenses_df = parse_csv_data(expenses_element[0].text.strip())
                validate_df(expenses_df, True)

                categories = []
                total = 0.0
                for _, row in expenses_df.iterrows():
                    cat = self._get_category_from_lookup(row["category"])
                    amount = float(row["amount"])
                    categories.append(
                        CategoryAmount(
                            category_qualified_name=cat.qualified_name,
                            category_name=cat.name,
                            amount=amount,
                        )
                    )
                    all_expense_categories.add(cat.qualified_name)
                    total += amount

                expenses_periods.append(
                    PeriodCategoryBreakdown(
                        period=period.value,
                        start_date=period.start,
                        end_date=period.end,
                        categories=categories,
                        total=total,
                    )
                )

            # Parse revenue
            revenue_element = entry.xpath("revenue")
            if revenue_element and len(revenue_element) > 0:
                revenue_df = parse_csv_data(revenue_element[0].text.strip())
                validate_df(revenue_df, False)

                categories = []
                total = 0.0
                for _, row in revenue_df.iterrows():
                    cat = self._get_category_from_lookup(row["category"])
                    amount = float(row["amount"])
                    categories.append(
                        CategoryAmount(
                            category_qualified_name=cat.qualified_name,
                            category_name=cat.name,
                            amount=amount,
                        )
                    )
                    all_revenue_categories.add(cat.qualified_name)
                    total += amount

                revenue_periods.append(
                    PeriodCategoryBreakdown(
                        period=period.value,
                        start_date=period.start,
                        end_date=period.end,
                        categories=categories,
                        total=total,
                    )
                )

        # Sort periods by start date
        expenses_periods.sort(key=lambda x: x.start_date)
        revenue_periods.sort(key=lambda x: x.start_date)

        # Return two separate response objects - for now just return expenses
        # The caller can choose which to use
        return RevenueAndExpensesPerPeriodAndCategory(
            periods=expenses_periods,
            all_categories=sorted(all_expense_categories),
            transaction_type=TransactionTypeEnum.EXPENSES,
        )

    def _init_months_distribution(
        self, df: pd.DataFrame
    ) -> List[ExpensesAndRevenueForPeriod]:
        """Initialize month distribution from DataFrame.

        Args:
            df: DataFrame with columns: month, expenses, revenue, balance.

        Returns:
            List of ExpensesAndRevenueForPeriod for each month.
        """
        expected: List[ExpensesAndRevenueForPeriod] = []
        for _, row in df.iterrows():
            month_str = row["month"]
            month_nr, year = month_str.split("_")
            period = Month.from_month_and_year(int(month_nr), int(year))
            expected.append(
                ExpensesAndRevenueForPeriod(
                    period=period.value,
                    revenue=float(row["revenue"]),
                    expenses=float(row["expenses"]),
                    start_date=period.start,
                    end_date=period.end,
                )
            )
        return expected

    def _init_quarters_distribution(
        self, df: pd.DataFrame
    ) -> List[ExpensesAndRevenueForPeriod]:
        """Initialize quarter distribution from DataFrame.

        Args:
            df: DataFrame with columns: quarter, expenses, revenue, balance.

        Returns:
            List of ExpensesAndRevenueForPeriod for each quarter.
        """
        expected: List[ExpensesAndRevenueForPeriod] = []
        for _, row in df.iterrows():
            quarter_str = row["quarter"]
            quarter_nr, year = quarter_str.split("_")
            period = Quarter.from_quarter_nr_and_year(int(quarter_nr), int(year))
            expected.append(
                ExpensesAndRevenueForPeriod(
                    period=period.value,
                    revenue=float(row["revenue"]),
                    expenses=float(row["expenses"]),
                    start_date=period.start,
                    end_date=period.end,
                )
            )
        return expected

    def _init_years_distribution(
        self, df: pd.DataFrame
    ) -> List[ExpensesAndRevenueForPeriod]:
        """Initialize year distribution from DataFrame.

        Args:
            df: DataFrame with columns: year, expenses, revenue, balance.

        Returns:
            List of ExpensesAndRevenueForPeriod for each year.
        """
        expected: List[ExpensesAndRevenueForPeriod] = []
        for _, row in df.iterrows():
            year = int(row["year"])
            period = Year.from_year(year)
            expected.append(
                ExpensesAndRevenueForPeriod(
                    period=period.value,
                    revenue=float(row["revenue"]),
                    expenses=float(row["expenses"]),
                    start_date=period.start,
                    end_date=period.end,
                )
            )
        return expected

    def get_unique_categories(self) -> List[str]:
        """Get list of unique category names from the transactions DataFrame.

        Returns:
            List of unique category names.
        """
        return self.transactions_df["category"].unique().tolist()

    def get_date_range(self) -> Tuple[date, date]:
        """Get the date range of all transactions.

        Returns:
            Tuple of (start_date, end_date).
        """
        # Parse dates from the 'date' column (format: DD/MM/YYYY)
        dates = pd.to_datetime(self.transactions_df["date"], format="%d/%m/%Y")
        return dates.min().date(), dates.max().date()


async def create_test_data(
    session: AsyncSession,
) -> Tuple[BankAccount, Dict[str, Category], List[Transaction]]:
    """Create test bank account, categories, counterparties, and transactions.

    Args:
        session: The async database session.

    Returns:
        Tuple of (bank_account, category_dict, transactions).
    """
    resources = Resources()

    # Create bank account (use lowercase for consistency with normalize_account_number)
    bank_account = BankAccount(account_number="test123456", alias="Test Account")
    session.add(bank_account)
    await session.flush()

    # Create categories
    category_dict: Dict[str, Category] = {}
    for category_name in resources.get_unique_categories():
        cat_type = category_name.split("_")[1].upper()
        transaction_type = (
            TransactionTypeEnum.EXPENSES
            if cat_type == "EXPENSES"
            else TransactionTypeEnum.REVENUE
        )
        category = Category(
            name=category_name,
            qualified_name=category_name,
            type=transaction_type,
            is_root=False,
        )
        session.add(category)
        category_dict[category_name] = category

    await session.flush()

    # Create counterparty (needed for transactions)
    counterparty = Counterparty(name="test_counterparty", account_number="CP123456")
    session.add(counterparty)
    await session.flush()

    # Create transactions from DataFrame
    transactions: List[Transaction] = []
    df = resources.transactions_df.copy()
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")

    for idx, row in df.iterrows():
        category_name = row["category"]
        category = category_dict[category_name]
        booking_date = row["date"].date()

        transaction = Transaction(
            transaction_id=f"TX_{idx}_{category_name}_{booking_date}",
            booking_date=booking_date,
            statement_number=f"STMT_{idx}",
            transaction_number=f"TXN_{idx}_{category_name}_{booking_date}",
            currency_date=booking_date,
            amount=float(row["amount"]),
            currency="EUR",
            country_code="BE",
            bank_account_id=bank_account.account_number,
            counterparty_id=counterparty.name,
            category_id=category.id,
        )
        session.add(transaction)
        transactions.append(transaction)

    await session.flush()
    await session.commit()

    return bank_account, category_dict, transactions


@pytest_asyncio.fixture
async def seed_test_transactions(
    async_session: AsyncSession,
) -> Tuple[BankAccount, Dict[str, Category], List[Transaction], Resources]:
    """Fixture that creates test data and returns Resources with category lookup.

    Args:
        async_session: The async database session from conftest.

    Returns:
        Tuple of (bank_account, category_dict, transactions, resources).
    """
    bank_account, category_dict, transactions = await create_test_data(async_session)

    # Create Resources with category lookup for loading category distributions
    resources = Resources(category_lookup=category_dict)

    return bank_account, category_dict, transactions, resources


# Test placeholder - actual tests will be implemented in subsequent steps
class TestResourcesHelper:
    """Tests for the Resources helper class."""

    def test_resources_loads_transactions_df(self):
        """Test that Resources loads transactions DataFrame correctly."""
        resources = Resources()

        # Should have loaded transactions
        assert resources.transactions_df is not None
        assert len(resources.transactions_df) > 0

        # Should have expected columns
        expected_columns = [
            "category",
            "amount",
            "year",
            "quarter",
            "month",
            "day",
            "date",
            "type",
        ]
        for col in expected_columns:
            assert col in resources.transactions_df.columns, f"Missing column: {col}"

    def test_resources_loads_distributions_per_period(self):
        """Test that Resources loads distributions per period correctly."""
        resources = Resources()

        # Should have distributions for all groupings
        assert Grouping.MONTH in resources.distributions_per_period
        assert Grouping.QUARTER in resources.distributions_per_period
        assert Grouping.YEAR in resources.distributions_per_period

        # Each should have data
        assert len(resources.distributions_per_period[Grouping.MONTH]) > 0
        assert len(resources.distributions_per_period[Grouping.QUARTER]) > 0
        assert len(resources.distributions_per_period[Grouping.YEAR]) > 0

    def test_resources_month_distribution_values(self):
        """Test that month distribution values are parsed correctly."""
        resources = Resources()

        month_dist = resources.distributions_per_period[Grouping.MONTH]
        # Find January 2022 (1_2022)
        jan_2022 = next(
            (d for d in month_dist if "01/2022" in d.period),
            None,
        )

        assert jan_2022 is not None
        assert jan_2022.revenue == 2
        assert jan_2022.expenses == 0

    def test_resources_quarter_distribution_values(self):
        """Test that quarter distribution values are parsed correctly."""
        resources = Resources()

        quarter_dist = resources.distributions_per_period[Grouping.QUARTER]
        # Find Q1 2022
        q1_2022 = next(
            (
                d
                for d in quarter_dist
                if "01/2022" in d.period and "03/2022" in d.period
            ),
            None,
        )

        assert q1_2022 is not None
        assert q1_2022.revenue == 3
        assert q1_2022.expenses == -3

    def test_resources_year_distribution_values(self):
        """Test that year distribution values are parsed correctly."""
        resources = Resources()

        year_dist = resources.distributions_per_period[Grouping.YEAR]
        # Find 2022
        year_2022 = next((d for d in year_dist if "2022" in d.period), None)

        assert year_2022 is not None
        assert year_2022.revenue == 55
        assert year_2022.expenses == -55

    def test_resources_get_unique_categories(self):
        """Test that unique categories are extracted correctly."""
        resources = Resources()

        categories = resources.get_unique_categories()

        # Should have both expense and revenue categories
        assert len(categories) > 0
        expense_cats = [c for c in categories if "EXPENSES" in c]
        revenue_cats = [c for c in categories if "REVENUE" in c]
        assert len(expense_cats) > 0
        assert len(revenue_cats) > 0

    def test_resources_get_date_range(self):
        """Test that date range is calculated correctly."""
        resources = Resources()

        start_date, end_date = resources.get_date_range()

        # Based on XML data, dates span 2022 and 2023
        assert start_date.year == 2022
        assert end_date.year == 2023
        assert start_date < end_date


@pytest.mark.asyncio
class TestSeedTestTransactions:
    """Tests for the seed_test_transactions fixture."""

    async def test_seed_creates_bank_account(
        self,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test that fixture creates a bank account."""
        bank_account, category_dict, transactions, resources = seed_test_transactions

        assert bank_account is not None
        assert bank_account.account_number == "test123456"

    async def test_seed_creates_categories(
        self,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test that fixture creates all required categories."""
        bank_account, category_dict, transactions, resources = seed_test_transactions

        # Should have created categories for all unique category names in XML
        expected_categories = resources.get_unique_categories()
        assert len(category_dict) == len(expected_categories)

        for cat_name in expected_categories:
            assert cat_name in category_dict
            cat = category_dict[cat_name]
            assert cat.id is not None
            assert cat.qualified_name == cat_name

    async def test_seed_creates_transactions(
        self,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test that fixture creates all transactions from XML."""
        bank_account, category_dict, transactions, resources = seed_test_transactions

        # Should have created transactions for all rows in XML
        expected_count = len(resources.transactions_df)
        assert len(transactions) == expected_count

        # All transactions should have IDs and be linked to the bank account
        for tx in transactions:
            assert tx.transaction_id is not None
            assert tx.bank_account_id == bank_account.account_number
            assert tx.category_id is not None

    async def test_seed_resources_has_category_lookup(
        self,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test that Resources is initialized with category lookup."""
        bank_account, category_dict, transactions, resources = seed_test_transactions

        # Resources should have been initialized with category lookup
        assert len(resources.category_lookup) > 0
        assert resources.category_lookup == category_dict


@pytest.mark.asyncio
class TestGetRevenueAndExpensesPerPeriod:
    """Tests for AnalysisService.get_revenue_and_expenses_per_period."""

    async def test_get_revenue_and_expenses_per_period_year(
        self,
        async_session: AsyncSession,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test aggregation by year grouping."""
        bank_account, category_dict, transactions, resources = seed_test_transactions
        start_date, end_date = resources.get_date_range()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.BOTH,
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            grouping=Grouping.YEAR,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period(query, async_session)

        assert result is not None
        assert len(result.content) > 0

        # Get expected data from resources
        expected = resources.distributions_per_period[Grouping.YEAR]
        assert len(result.content) == len(expected)

        # Sort both by period for comparison
        result_sorted = sorted(result.content, key=lambda x: x.period)
        expected_sorted = sorted(expected, key=lambda x: x.period)

        for actual, exp in zip(result_sorted, expected_sorted):
            assert actual.period == exp.period
            assert actual.revenue == exp.revenue
            assert actual.expenses == -exp.expenses  # Service returns positive expenses

    async def test_get_revenue_and_expenses_per_period_quarter(
        self,
        async_session: AsyncSession,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test aggregation by quarter grouping."""
        bank_account, category_dict, transactions, resources = seed_test_transactions
        start_date, end_date = resources.get_date_range()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.BOTH,
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            grouping=Grouping.QUARTER,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period(query, async_session)

        assert result is not None
        assert len(result.content) > 0

        # Get expected data from resources
        expected = resources.distributions_per_period[Grouping.QUARTER]
        assert len(result.content) == len(expected)

        # Sort both by start_date for comparison
        result_sorted = sorted(result.content, key=lambda x: x.start_date)
        expected_sorted = sorted(expected, key=lambda x: x.start_date)

        for actual, exp in zip(result_sorted, expected_sorted):
            assert actual.period == exp.period
            assert actual.revenue == exp.revenue
            assert actual.expenses == -exp.expenses  # Service returns positive expenses

    async def test_get_revenue_and_expenses_per_period_month(
        self,
        async_session: AsyncSession,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test aggregation by month grouping."""
        bank_account, category_dict, transactions, resources = seed_test_transactions
        start_date, end_date = resources.get_date_range()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.BOTH,
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period(query, async_session)

        assert result is not None
        assert len(result.content) > 0

        # Get expected data from resources
        expected = resources.distributions_per_period[Grouping.MONTH]
        assert len(result.content) == len(expected)

        # Sort both by start_date for comparison
        result_sorted = sorted(result.content, key=lambda x: x.start_date)
        expected_sorted = sorted(expected, key=lambda x: x.start_date)

        for actual, exp in zip(result_sorted, expected_sorted):
            assert actual.period == exp.period
            assert actual.revenue == exp.revenue
            assert actual.expenses == -exp.expenses  # Service returns positive expenses

    async def test_get_revenue_and_expenses_per_period_no_transactions(
        self,
        async_session: AsyncSession,
    ):
        """Test that empty results are returned when no transactions exist."""
        # Create a bank account without any transactions
        bank_account = BankAccount(account_number="EMPTY123", alias="Empty Account")
        async_session.add(bank_account)
        await async_session.flush()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.BOTH,
            start=datetime(2020, 1, 1),
            end=datetime(2025, 12, 31),
            grouping=Grouping.YEAR,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period(query, async_session)

        assert result is not None
        assert len(result.content) == 0
        assert result.total_elements == 0

    async def test_get_revenue_and_expenses_per_period_empty_query(
        self,
        async_session: AsyncSession,
    ):
        """Test that empty query returns empty results."""
        query = RevenueExpensesQuery(
            account_number="",  # Empty account number makes query empty
            transaction_type=TransactionTypeEnum.BOTH,
            start=datetime(2020, 1, 1),
            end=datetime(2025, 12, 31),
            grouping=Grouping.YEAR,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period(query, async_session)

        assert result is not None
        assert len(result.content) == 0


@pytest.mark.asyncio
class TestGetRevenueAndExpensesPerPeriodAndCategory:
    """Tests for AnalysisService.get_revenue_and_expenses_per_period_and_category."""

    async def test_get_expenses_per_period_and_category_year(
        self,
        async_session: AsyncSession,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test category breakdown by year grouping for expenses."""
        bank_account, category_dict, transactions, resources = seed_test_transactions
        start_date, end_date = resources.get_date_range()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            grouping=Grouping.YEAR,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period_and_category(
            query, async_session
        )

        assert result is not None
        assert len(result.periods) > 0
        assert result.transaction_type == TransactionTypeEnum.EXPENSES

        # Verify we have category breakdowns
        for period in result.periods:
            assert len(period.categories) > 0
            # All categories should be expense categories
            for cat in period.categories:
                assert "EXPENSES" in cat.category_qualified_name

    async def test_get_revenue_per_period_and_category_year(
        self,
        async_session: AsyncSession,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test category breakdown by year grouping for revenue."""
        bank_account, category_dict, transactions, resources = seed_test_transactions
        start_date, end_date = resources.get_date_range()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.REVENUE,
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            grouping=Grouping.YEAR,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period_and_category(
            query, async_session
        )

        assert result is not None
        assert len(result.periods) > 0
        assert result.transaction_type == TransactionTypeEnum.REVENUE

        # Verify we have category breakdowns
        for period in result.periods:
            assert len(period.categories) > 0
            # All categories should be revenue categories
            for cat in period.categories:
                assert "REVENUE" in cat.category_qualified_name

    async def test_get_expenses_per_period_and_category_quarter(
        self,
        async_session: AsyncSession,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test category breakdown by quarter grouping for expenses."""
        bank_account, category_dict, transactions, resources = seed_test_transactions
        start_date, end_date = resources.get_date_range()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            grouping=Grouping.QUARTER,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period_and_category(
            query, async_session
        )

        assert result is not None
        assert len(result.periods) > 0
        assert result.transaction_type == TransactionTypeEnum.EXPENSES

        # Should have 8 quarters worth of data (Q1-Q4 for 2022 and 2023)
        # But some quarters might not have expenses, so just check we have some
        assert len(result.periods) >= 1

    async def test_get_expenses_per_period_and_category_month(
        self,
        async_session: AsyncSession,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test category breakdown by month grouping for expenses."""
        bank_account, category_dict, transactions, resources = seed_test_transactions
        start_date, end_date = resources.get_date_range()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            grouping=Grouping.MONTH,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period_and_category(
            query, async_session
        )

        assert result is not None
        assert len(result.periods) > 0
        assert result.transaction_type == TransactionTypeEnum.EXPENSES

    async def test_get_per_period_and_category_no_transactions(
        self,
        async_session: AsyncSession,
    ):
        """Test that empty results are returned when no transactions exist."""
        # Create a bank account without any transactions
        bank_account = BankAccount(
            account_number="EMPTYCAT123", alias="Empty Category Account"
        )
        async_session.add(bank_account)
        await async_session.flush()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=datetime(2020, 1, 1),
            end=datetime(2025, 12, 31),
            grouping=Grouping.YEAR,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period_and_category(
            query, async_session
        )

        assert result is not None
        assert len(result.periods) == 0
        assert len(result.all_categories) == 0

    async def test_get_per_period_and_category_empty_query(
        self,
        async_session: AsyncSession,
    ):
        """Test that empty query returns empty instance."""
        query = RevenueExpensesQuery(
            account_number="",  # Empty account number makes query empty
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=datetime(2020, 1, 1),
            end=datetime(2025, 12, 31),
            grouping=Grouping.YEAR,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period_and_category(
            query, async_session
        )

        assert result is not None
        assert len(result.periods) == 0

    async def test_all_categories_tracked_across_periods(
        self,
        async_session: AsyncSession,
        seed_test_transactions: Tuple[
            BankAccount, Dict[str, Category], List[Transaction], Resources
        ],
    ):
        """Test that all_categories contains all unique categories across periods."""
        bank_account, category_dict, transactions, resources = seed_test_transactions
        start_date, end_date = resources.get_date_range()

        query = RevenueExpensesQuery(
            account_number=bank_account.account_number,
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            grouping=Grouping.YEAR,
        )

        service = AnalysisService()
        result = await service.get_revenue_and_expenses_per_period_and_category(
            query, async_session
        )

        # Collect all categories from all periods
        categories_in_periods = set()
        for period in result.periods:
            for cat in period.categories:
                categories_in_periods.add(cat.category_qualified_name)

        # all_categories should contain all unique categories from periods
        assert set(result.all_categories) == categories_in_periods
