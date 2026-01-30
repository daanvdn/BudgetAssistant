"""Pydantic schemas for analysis API operations."""

from datetime import datetime
from typing import List

from enums import TransactionTypeEnum
from pydantic import BaseModel


class ExpensesAndRevenueForPeriod(BaseModel):
    """Expenses and revenue data for a single period."""

    period: str
    expenses: float = 0.0
    revenue: float = 0.0
    start_date: datetime
    end_date: datetime


class RevenueAndExpensesPerPeriodResponse(BaseModel):
    """Response for revenue and expenses per period."""

    content: List[ExpensesAndRevenueForPeriod]
    page: int = 0
    total_elements: int = 0
    size: int = 0


class CategoryAmount(BaseModel):
    """Amount for a specific category."""

    category_qualified_name: str
    category_name: str
    amount: float = 0.0


class PeriodCategoryBreakdown(BaseModel):
    """Category breakdown for a single period."""

    period: str
    start_date: datetime
    end_date: datetime
    categories: List[CategoryAmount] = []
    total: float = 0.0


class RevenueAndExpensesPerPeriodAndCategory(BaseModel):
    """Response for revenue and expenses per period and category."""

    periods: List[PeriodCategoryBreakdown] = []
    all_categories: List[str] = []
    transaction_type: TransactionTypeEnum

    @classmethod
    def empty_instance(cls) -> "RevenueAndExpensesPerPeriodAndCategory":
        """Create an empty instance."""
        return cls(
            periods=[],
            all_categories=[],
            transaction_type=TransactionTypeEnum.EXPENSES,
        )


class CategoryDetailsForPeriodResult(BaseModel):
    """Category details for a specific period."""

    category_qualified_name: str
    category_name: str
    amount: float = 0.0
    transaction_count: int = 0
    percentage: float = 0.0


class CategoryDetailsForPeriodResponse(BaseModel):
    """Response for category details for a period."""

    period: str
    start_date: datetime
    end_date: datetime
    categories: List[CategoryDetailsForPeriodResult] = []
    total_amount: float = 0.0


class BudgetEntryResult(BaseModel):
    """Budget entry tracking result."""

    category_qualified_name: str
    category_name: str
    budgeted_amount: float = 0.0
    actual_amount: float = 0.0
    difference: float = 0.0
    percentage_used: float = 0.0


class BudgetTrackerResult(BaseModel):
    """Budget tracking result."""

    period: str
    start_date: datetime
    end_date: datetime
    entries: List[BudgetEntryResult] = []
    total_budgeted: float = 0.0
    total_actual: float = 0.0
    total_difference: float = 0.0


class CategoriesForAccountResponse(BaseModel):
    """Response for categories available for an account and transaction type."""

    categories: List[str] = []
    transaction_type: TransactionTypeEnum
