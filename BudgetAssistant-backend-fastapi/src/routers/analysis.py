"""Analysis router for revenue/expenses analysis."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import CurrentUser
from common.enums import TransactionTypeEnum
from common.logging_utils import LoggerFactory
from db.database import get_session
from schemas import (
    BudgetTrackerResult,
    CategoriesForAccountResponse,
    CategoryDetailsForPeriodResponse,
    DateRangeShortcut,
    ResolvedDateRange,
    RevenueAndExpensesPerPeriodAndCategory,
    RevenueAndExpensesPerPeriodResponse,
    RevenueExpensesQuery,
    RevenueExpensesQueryWithCategory,
)
from services.analysis_service import analysis_service
from services.period_service import period_service

logger = LoggerFactory.for_caller()
router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post(
    "/revenue-expenses-per-period",
    response_model=RevenueAndExpensesPerPeriodResponse,
)
async def get_revenue_and_expenses_per_period(
    query: RevenueExpensesQuery,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> RevenueAndExpensesPerPeriodResponse:
    """Get revenue and expenses aggregated per period."""
    if query.is_empty():
        return RevenueAndExpensesPerPeriodResponse(
            content=[],
            page=0,
            total_elements=0,
            size=0,
        )

    return await analysis_service.get_revenue_and_expenses_per_period(query, session)


@router.post(
    "/revenue-expenses-per-period-and-category",
    response_model=RevenueAndExpensesPerPeriodAndCategory,
)
async def get_revenue_and_expenses_per_period_and_category(
    query: RevenueExpensesQuery,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> RevenueAndExpensesPerPeriodAndCategory:
    """Get revenue and expenses aggregated per period and category."""
    if query.is_empty():
        return RevenueAndExpensesPerPeriodAndCategory.empty_instance()

    return await analysis_service.get_revenue_and_expenses_per_period_and_category(query, session)


@router.post(
    "/category-details-for-period",
    response_model=CategoryDetailsForPeriodResponse,
)
async def get_category_details_for_period(
    query: RevenueExpensesQueryWithCategory,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> CategoryDetailsForPeriodResponse:
    """Get detailed category breakdown for a specific period."""
    try:
        return await analysis_service.get_category_details_for_period(query, query.category_qualified_name, session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/categories-for-account",
    response_model=CategoriesForAccountResponse,
)
async def get_categories_for_account_and_transaction_type(
    bank_account: str = Query(..., description="Bank account number"),
    transaction_type: TransactionTypeEnum = Query(..., description="Transaction type"),
    current_user: CurrentUser = None,
    session: AsyncSession = Depends(get_session),
) -> CategoriesForAccountResponse:
    """Get categories used in transactions for a bank account."""
    categories = await analysis_service.get_categories_for_account(
        bank_account=bank_account,
        transaction_type=transaction_type,
        session=session,
    )

    return CategoriesForAccountResponse(
        categories=categories,
        transaction_type=transaction_type,
    )


@router.post("/track-budget", response_model=BudgetTrackerResult)
async def track_budget(
    query: RevenueExpensesQuery,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BudgetTrackerResult:
    """Track budget vs actual spending for a period."""
    if query.is_empty():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    try:
        result = await analysis_service.track_budget(query, session)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not track budget - query may be invalid",
            )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/resolve-date-shortcut", response_model=ResolvedDateRange)
async def resolve_start_end_date_shortcut(
    shortcut: DateRangeShortcut = Query(..., description="Date range shortcut"),
    current_user: CurrentUser = None,
    session: AsyncSession = Depends(get_session),
) -> ResolvedDateRange:
    """Resolve a date range shortcut to actual start and end dates."""
    return period_service.resolve_start_end_date_shortcut(shortcut)
