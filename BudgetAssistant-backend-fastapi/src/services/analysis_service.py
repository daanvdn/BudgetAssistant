"""Analysis service with async SQLModel operations."""

from datetime import datetime
from typing import List, Optional, Tuple

from enums import RecurrenceType, TransactionTypeEnum
from models import BankAccount, BudgetTree, BudgetTreeNode, Category, Transaction
from schemas import (
    BudgetEntryResult,
    BudgetTrackerResult,
    CategoryAmount,
    CategoryDetailsForPeriodResponse,
    CategoryDetailsForPeriodResult,
    ExpensesAndRevenueForPeriod,
    Grouping,
    PeriodCategoryBreakdown,
    RevenueAndExpensesPerPeriodAndCategory,
    RevenueAndExpensesPerPeriodResponse,
    RevenueExpensesQuery,
)
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class AnalysisService:
    """Service for analysis operations."""

    def _build_transaction_filter(
        self,
        query: RevenueExpensesQuery,
    ):
        """Build SQLAlchemy filter from RevenueExpensesQuery."""
        normalized = BankAccount.normalize_account_number(query.account_number)

        conditions = [
            Transaction.bank_account_id == normalized,
            Transaction.booking_date >= query.start.date(),
            Transaction.booking_date <= query.end.date(),
        ]

        # Transaction type filter
        if query.transaction_type == TransactionTypeEnum.REVENUE:
            conditions.append(Transaction.amount >= 0)
        elif query.transaction_type == TransactionTypeEnum.EXPENSES:
            conditions.append(Transaction.amount < 0)

        # Recurrence filters
        if query.revenue_recurrence:
            if query.revenue_recurrence == RecurrenceType.RECURRENT:
                conditions.append(
                    and_(Transaction.amount >= 0, Transaction.is_recurring == True)
                )
            elif query.revenue_recurrence == RecurrenceType.NON_RECURRENT:
                conditions.append(
                    and_(Transaction.amount >= 0, Transaction.is_recurring == False)
                )

        if query.expenses_recurrence:
            if query.expenses_recurrence == RecurrenceType.RECURRENT:
                conditions.append(
                    and_(Transaction.amount < 0, Transaction.is_recurring == True)
                )
            elif query.expenses_recurrence == RecurrenceType.NON_RECURRENT:
                conditions.append(
                    and_(Transaction.amount < 0, Transaction.is_recurring == False)
                )

        return and_(*conditions)

    def _get_period_key(
        self,
        booking_date: datetime,
        grouping: Grouping,
    ) -> Tuple[str, datetime, datetime]:
        """Get period key, start, and end dates for a booking date."""
        if grouping == Grouping.MONTH:
            start = booking_date.replace(day=1)
            # Get last day of month
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1)
            else:
                end = start.replace(month=start.month + 1, day=1)
            end = end.replace(day=1) - timedelta(days=1)
            key = f"{booking_date.year}-{booking_date.month:02d}"
        elif grouping == Grouping.QUARTER:
            quarter = (booking_date.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start = booking_date.replace(month=start_month, day=1)
            end_month = start_month + 2
            if end_month > 12:
                end = datetime(booking_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = datetime(booking_date.year, end_month + 1, 1) - timedelta(days=1)
            key = f"{booking_date.year}-Q{quarter}"
        elif grouping == Grouping.YEAR:
            start = booking_date.replace(month=1, day=1)
            end = booking_date.replace(month=12, day=31)
            key = str(booking_date.year)
        else:
            # Default to month
            return self._get_period_key(booking_date, Grouping.MONTH)

        return key, start, end

    async def get_revenue_and_expenses_per_period(
        self,
        query: RevenueExpensesQuery,
        session: AsyncSession,
    ) -> RevenueAndExpensesPerPeriodResponse:
        """Get revenue and expenses aggregated per period."""
        if query.is_empty():
            return RevenueAndExpensesPerPeriodResponse(
                content=[],
                page=0,
                total_elements=0,
                size=0,
            )

        filter_condition = self._build_transaction_filter(query)

        # Get all transactions for the period
        result = await session.execute(
            select(Transaction)
            .where(filter_condition)
            .order_by(Transaction.booking_date)
        )
        transactions = result.scalars().all()

        # Group by period
        periods_data = {}
        for txn in transactions:
            period_key, start, end = self._get_period_key(
                txn.booking_date, query.grouping
            )

            if period_key not in periods_data:
                periods_data[period_key] = {
                    "period": period_key,
                    "revenue": 0.0,
                    "expenses": 0.0,
                    "start_date": start,
                    "end_date": end,
                }

            if txn.amount >= 0:
                periods_data[period_key]["revenue"] += txn.amount
            else:
                periods_data[period_key]["expenses"] += abs(txn.amount)

        # Convert to response format
        content = [
            ExpensesAndRevenueForPeriod(
                period=data["period"],
                revenue=data["revenue"],
                expenses=data["expenses"],
                start_date=data["start_date"],
                end_date=data["end_date"],
            )
            for data in sorted(periods_data.values(), key=lambda x: x["start_date"])
        ]

        return RevenueAndExpensesPerPeriodResponse(
            content=content,
            page=0,
            total_elements=len(content),
            size=len(content),
        )

    async def get_revenue_and_expenses_per_period_and_category(
        self,
        query: RevenueExpensesQuery,
        session: AsyncSession,
    ) -> RevenueAndExpensesPerPeriodAndCategory:
        """Get revenue and expenses aggregated per period and category."""
        if query.is_empty():
            return RevenueAndExpensesPerPeriodAndCategory.empty_instance()

        filter_condition = self._build_transaction_filter(query)

        # Get all transactions with categories
        result = await session.execute(
            select(Transaction)
            .where(filter_condition)
            .order_by(Transaction.booking_date)
        )
        transactions = result.scalars().all()

        # Group by period and category
        periods_data = {}
        all_categories = set()

        for txn in transactions:
            period_key, start, end = self._get_period_key(
                txn.booking_date, query.grouping
            )

            if period_key not in periods_data:
                periods_data[period_key] = {
                    "period": period_key,
                    "start_date": start,
                    "end_date": end,
                    "categories": {},
                    "total": 0.0,
                }

            # Get category info
            if txn.category_id:
                cat_result = await session.execute(
                    select(Category).where(Category.id == txn.category_id)
                )
                category = cat_result.scalar_one_or_none()
                cat_name = category.qualified_name if category else "Uncategorized"
                cat_display = category.name if category else "Uncategorized"
            else:
                cat_name = "Uncategorized"
                cat_display = "Uncategorized"

            all_categories.add(cat_name)

            if cat_name not in periods_data[period_key]["categories"]:
                periods_data[period_key]["categories"][cat_name] = {
                    "qualified_name": cat_name,
                    "name": cat_display,
                    "amount": 0.0,
                }

            amount = abs(txn.amount)
            periods_data[period_key]["categories"][cat_name]["amount"] += amount
            periods_data[period_key]["total"] += amount

        # Convert to response format
        periods = []
        for data in sorted(periods_data.values(), key=lambda x: x["start_date"]):
            categories = [
                CategoryAmount(
                    category_qualified_name=cat["qualified_name"],
                    category_name=cat["name"],
                    amount=cat["amount"],
                )
                for cat in data["categories"].values()
            ]

            periods.append(
                PeriodCategoryBreakdown(
                    period=data["period"],
                    start_date=data["start_date"],
                    end_date=data["end_date"],
                    categories=categories,
                    total=data["total"],
                )
            )

        return RevenueAndExpensesPerPeriodAndCategory(
            periods=periods,
            all_categories=sorted(list(all_categories)),
            transaction_type=query.transaction_type,
        )

    async def track_budget(
        self,
        query: RevenueExpensesQuery,
        session: AsyncSession,
    ) -> Optional[BudgetTrackerResult]:
        """Track budget vs actual spending."""
        if query.is_empty():
            return None

        normalized = BankAccount.normalize_account_number(query.account_number)

        # Get budget tree
        tree_result = await session.execute(
            select(BudgetTree).where(BudgetTree.bank_account_id == normalized)
        )
        budget_tree = tree_result.scalar_one_or_none()

        if not budget_tree:
            raise ValueError(
                f"Budget tree for bank account {query.account_number} does not exist"
            )

        # Get actual spending per category
        filter_condition = self._build_transaction_filter(query)

        result = await session.execute(
            select(Transaction.category_id, func.sum(func.abs(Transaction.amount)))
            .where(filter_condition)
            .group_by(Transaction.category_id)
        )
        actual_by_category = {row[0]: row[1] for row in result.all()}

        # Build budget entries
        entries = []
        total_budgeted = 0.0
        total_actual = 0.0

        # Get all budget nodes
        if budget_tree.root_id:
            await self._collect_budget_entries(
                budget_tree.root_id,
                actual_by_category,
                entries,
                session,
            )

        for entry in entries:
            total_budgeted += entry.budgeted_amount
            total_actual += entry.actual_amount

        period_key, _, _ = self._get_period_key(query.start, query.grouping)

        return BudgetTrackerResult(
            period=period_key,
            start_date=query.start,
            end_date=query.end,
            entries=entries,
            total_budgeted=total_budgeted,
            total_actual=total_actual,
            total_difference=total_budgeted - total_actual,
        )

    async def _collect_budget_entries(
        self,
        node_id: int,
        actual_by_category: dict,
        entries: List[BudgetEntryResult],
        session: AsyncSession,
    ) -> None:
        """Recursively collect budget entries from tree nodes."""
        node_result = await session.execute(
            select(BudgetTreeNode).where(BudgetTreeNode.id == node_id)
        )
        node = node_result.scalar_one_or_none()
        if not node:
            return

        # Get category
        cat_result = await session.execute(
            select(Category).where(Category.id == node.category_id)
        )
        category = cat_result.scalar_one_or_none()

        if category and node.amount > 0:
            actual = actual_by_category.get(node.category_id, 0.0)
            budgeted = float(node.amount)
            difference = budgeted - actual
            percentage = (actual / budgeted * 100) if budgeted > 0 else 0.0

            entries.append(
                BudgetEntryResult(
                    category_qualified_name=category.qualified_name,
                    category_name=category.name,
                    budgeted_amount=budgeted,
                    actual_amount=actual,
                    difference=difference,
                    percentage_used=percentage,
                )
            )

        # Process children
        children_result = await session.execute(
            select(BudgetTreeNode).where(BudgetTreeNode.parent_id == node_id)
        )
        children = children_result.scalars().all()

        for child in children:
            await self._collect_budget_entries(
                child.id, actual_by_category, entries, session
            )

    async def get_category_details_for_period(
        self,
        query: RevenueExpensesQuery,
        category_qualified_name: str,
        session: AsyncSession,
    ) -> CategoryDetailsForPeriodResponse:
        """Get detailed category breakdown for a period."""
        filter_condition = self._build_transaction_filter(query)

        # Get category
        cat_result = await session.execute(
            select(Category).where(Category.qualified_name == category_qualified_name)
        )
        category = cat_result.scalar_one_or_none()

        if not category:
            raise ValueError(f"Category {category_qualified_name} not found")

        # Get transactions for this category and its children
        # First, get all child category IDs
        child_ids = await self._get_all_child_category_ids(category.id, session)
        category_ids = [category.id] + child_ids

        # Get transactions
        result = await session.execute(
            select(Transaction).where(
                filter_condition,
                Transaction.category_id.in_(category_ids),
            )
        )
        transactions = result.scalars().all()

        # Group by category
        category_totals = {}
        total_amount = 0.0

        for txn in transactions:
            if txn.category_id not in category_totals:
                # Get category name
                cat = await session.execute(
                    select(Category).where(Category.id == txn.category_id)
                )
                cat_obj = cat.scalar_one_or_none()
                category_totals[txn.category_id] = {
                    "qualified_name": cat_obj.qualified_name if cat_obj else "",
                    "name": cat_obj.name if cat_obj else "",
                    "amount": 0.0,
                    "count": 0,
                }

            amount = abs(txn.amount)
            category_totals[txn.category_id]["amount"] += amount
            category_totals[txn.category_id]["count"] += 1
            total_amount += amount

        # Calculate percentages
        categories = []
        for data in category_totals.values():
            percentage = (
                (data["amount"] / total_amount * 100) if total_amount > 0 else 0
            )
            categories.append(
                CategoryDetailsForPeriodResult(
                    category_qualified_name=data["qualified_name"],
                    category_name=data["name"],
                    amount=data["amount"],
                    transaction_count=data["count"],
                    percentage=percentage,
                )
            )

        period_key, _, _ = self._get_period_key(query.start, query.grouping)

        return CategoryDetailsForPeriodResponse(
            period=period_key,
            start_date=query.start,
            end_date=query.end,
            categories=sorted(categories, key=lambda x: -x.amount),
            total_amount=total_amount,
        )

    async def _get_all_child_category_ids(
        self,
        category_id: int,
        session: AsyncSession,
    ) -> List[int]:
        """Recursively get all child category IDs."""
        result = await session.execute(
            select(Category.id).where(Category.parent_id == category_id)
        )
        child_ids = list(result.scalars().all())

        all_ids = list(child_ids)
        for child_id in child_ids:
            grandchild_ids = await self._get_all_child_category_ids(child_id, session)
            all_ids.extend(grandchild_ids)

        return all_ids


# Import timedelta at top level
from datetime import timedelta

# Singleton instance
analysis_service = AnalysisService()
