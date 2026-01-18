"""Transactions router."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from enums import TransactionTypeEnum
from models import BankAccount, Category, Counterparty, Transaction
from models.associations import UserBankAccountLink
from routers.auth import CurrentUser
from schemas import (
    CountResponse,
    ErrorResponse,
    PageTransactionsInContextRequest,
    PageTransactionsRequest,
    PageTransactionsToManuallyReviewRequest,
    PaginatedResponse,
    SuccessResponse,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
    UploadTransactionsResponse,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def build_transaction_query_filter(query, user_id: int):
    """Build SQLAlchemy filter conditions from a TransactionQuery."""
    conditions = []

    # User must have access to the bank account
    conditions.append(
        Transaction.bank_account_id.in_(
            select(UserBankAccountLink.bank_account_number).where(
                UserBankAccountLink.user_id == user_id
            )
        )
    )

    if query is None:
        return and_(*conditions)

    if query.account_number and query.account_number != "NULL":
        normalized = BankAccount.normalize_account_number(query.account_number)
        conditions.append(Transaction.bank_account_id == normalized)

    if query.transaction_type:
        if query.transaction_type == TransactionTypeEnum.REVENUE:
            conditions.append(Transaction.amount >= 0)
        elif query.transaction_type == TransactionTypeEnum.EXPENSES:
            conditions.append(Transaction.amount < 0)

    if query.counterparty_name:
        conditions.append(
            Transaction.counterparty_id.ilike(f"%{query.counterparty_name}%")
        )

    if query.min_amount is not None:
        conditions.append(Transaction.amount >= query.min_amount)

    if query.max_amount is not None:
        conditions.append(Transaction.amount <= query.max_amount)

    if query.category_id is not None:
        conditions.append(Transaction.category_id == query.category_id)

    if query.transaction_or_communication:
        search_term = f"%{query.transaction_or_communication}%"
        conditions.append(
            or_(
                Transaction.transaction.ilike(search_term),
                Transaction.communications.ilike(search_term),
            )
        )

    if query.counterparty_account_number:
        # Need to join with Counterparty to filter by account number
        conditions.append(
            Transaction.counterparty_id.in_(
                select(Counterparty.name).where(
                    Counterparty.account_number.ilike(
                        f"%{query.counterparty_account_number}%"
                    )
                )
            )
        )

    if query.start_date:
        conditions.append(Transaction.booking_date >= query.start_date)

    if query.end_date:
        conditions.append(Transaction.booking_date <= query.end_date)

    if query.upload_timestamp:
        conditions.append(Transaction.upload_timestamp == query.upload_timestamp)

    if query.manually_assigned_category:
        conditions.append(Transaction.manually_assigned_category == True)

    return and_(*conditions)


def get_sort_column(sort_property: str):
    """Get the SQLAlchemy column for sorting."""
    sort_map = {
        "transaction_id": Transaction.transaction_id,
        "booking_date": Transaction.booking_date,
        "amount": Transaction.amount,
        "counterparty": Transaction.counterparty_id,
        "category": Transaction.category_id,
        "manually_assigned_category": Transaction.manually_assigned_category,
        "is_recurring": Transaction.is_recurring,
        "is_advance_shared_account": Transaction.is_advance_shared_account,
        "upload_timestamp": Transaction.upload_timestamp,
        "is_manually_reviewed": Transaction.is_manually_reviewed,
        "transaction": Transaction.transaction,
    }
    return sort_map.get(sort_property, Transaction.transaction_id)


@router.post("/page", response_model=PaginatedResponse[TransactionRead])
async def page_transactions(
    request: PageTransactionsRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[TransactionRead]:
    """Get paginated transactions with optional filtering."""
    # Build filter
    filter_condition = build_transaction_query_filter(request.query, current_user.id)

    # Count total
    count_query = select(func.count()).select_from(Transaction).where(filter_condition)
    total_result = await session.execute(count_query)
    total_elements = total_result.scalar() or 0

    # Get sort column and order
    sort_column = get_sort_column(request.sort_property.value)
    if request.sort_order.value == "desc":
        sort_column = sort_column.desc()

    # Get page of transactions
    offset = request.page * request.size
    query = (
        select(Transaction)
        .where(filter_condition)
        .order_by(sort_column)
        .offset(offset)
        .limit(request.size)
    )
    result = await session.execute(query)
    transactions = result.scalars().all()

    content = [TransactionRead.model_validate(t) for t in transactions]
    return PaginatedResponse.create(
        content=content,
        page=request.page,
        size=request.size,
        total_elements=total_elements,
    )


@router.post(
    "/page-in-context", response_model=PaginatedResponse[TransactionRead]
)
async def page_transactions_in_context(
    request: PageTransactionsInContextRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[TransactionRead]:
    """Get paginated transactions for a specific context (period, category)."""
    query = request.query
    normalized_account = BankAccount.normalize_account_number(query.bank_account)

    # Build filter conditions
    conditions = [
        Transaction.bank_account_id == normalized_account,
        Transaction.category_id == query.category_id,
    ]

    # Check user access
    access_result = await session.execute(
        select(UserBankAccountLink).where(
            UserBankAccountLink.user_id == current_user.id,
            UserBankAccountLink.bank_account_number == normalized_account,
        )
    )
    if not access_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    # Add transaction type filter
    if query.transaction_type == TransactionTypeEnum.REVENUE:
        conditions.append(Transaction.amount >= 0)
    elif query.transaction_type == TransactionTypeEnum.EXPENSES:
        conditions.append(Transaction.amount < 0)

    # TODO: Parse period string to date range
    # For now, skip period filtering

    filter_condition = and_(*conditions)

    # Count total
    count_query = select(func.count()).select_from(Transaction).where(filter_condition)
    total_result = await session.execute(count_query)
    total_elements = total_result.scalar() or 0

    # Get sort column
    sort_column = get_sort_column(request.sort_property.value)
    if request.sort_order.value == "desc":
        sort_column = sort_column.desc()

    # Get page
    offset = request.page * request.size
    stmt = (
        select(Transaction)
        .where(filter_condition)
        .order_by(sort_column)
        .offset(offset)
        .limit(request.size)
    )
    result = await session.execute(stmt)
    transactions = result.scalars().all()

    content = [TransactionRead.model_validate(t) for t in transactions]
    return PaginatedResponse.create(
        content=content,
        page=request.page,
        size=request.size,
        total_elements=total_elements,
    )


@router.post(
    "/page-to-manually-review", response_model=PaginatedResponse[TransactionRead]
)
async def page_transactions_to_manually_review(
    request: PageTransactionsToManuallyReviewRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[TransactionRead]:
    """Get paginated transactions that need manual review."""
    normalized_account = BankAccount.normalize_account_number(request.bank_account)

    # Check user access
    access_result = await session.execute(
        select(UserBankAccountLink).where(
            UserBankAccountLink.user_id == current_user.id,
            UserBankAccountLink.bank_account_number == normalized_account,
        )
    )
    if not access_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    # Build filter conditions
    conditions = [
        Transaction.bank_account_id == normalized_account,
        Transaction.is_manually_reviewed == False,
    ]

    if request.transaction_type == TransactionTypeEnum.REVENUE:
        conditions.append(Transaction.amount >= 0)
    elif request.transaction_type == TransactionTypeEnum.EXPENSES:
        conditions.append(Transaction.amount < 0)

    filter_condition = and_(*conditions)

    # Count total
    count_query = select(func.count()).select_from(Transaction).where(filter_condition)
    total_result = await session.execute(count_query)
    total_elements = total_result.scalar() or 0

    # Get sort column
    sort_column = get_sort_column(request.sort_property.value)
    if request.sort_order.value == "desc":
        sort_column = sort_column.desc()

    # Get page
    offset = request.page * request.size
    stmt = (
        select(Transaction)
        .where(filter_condition)
        .order_by(sort_column)
        .offset(offset)
        .limit(request.size)
    )
    result = await session.execute(stmt)
    transactions = result.scalars().all()

    content = [TransactionRead.model_validate(t) for t in transactions]
    return PaginatedResponse.create(
        content=content,
        page=request.page,
        size=request.size,
        total_elements=total_elements,
    )


@router.get("/count-to-manually-review", response_model=CountResponse)
async def count_transactions_to_manually_review(
    bank_account: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> CountResponse:
    """Count transactions that need manual review for a bank account."""
    normalized = BankAccount.normalize_account_number(bank_account)

    # Check user access
    access_result = await session.execute(
        select(UserBankAccountLink).where(
            UserBankAccountLink.user_id == current_user.id,
            UserBankAccountLink.bank_account_number == normalized,
        )
    )
    if not access_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    count_query = (
        select(func.count())
        .select_from(Transaction)
        .where(
            Transaction.bank_account_id == normalized,
            Transaction.is_manually_reviewed == False,
        )
    )
    result = await session.execute(count_query)
    count = result.scalar() or 0

    return CountResponse(count=count)


@router.post("/save", response_model=SuccessResponse, responses={400: {"model": ErrorResponse}})
async def save_transaction(
    transaction_update: TransactionUpdate,
    transaction_id: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Save/update a transaction."""
    # Get the transaction
    result = await session.execute(
        select(Transaction).where(Transaction.transaction_id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    # Check user access
    access_result = await session.execute(
        select(UserBankAccountLink).where(
            UserBankAccountLink.user_id == current_user.id,
            UserBankAccountLink.bank_account_number == transaction.bank_account_id,
        )
    )
    if not access_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this transaction",
        )

    # Update fields
    if transaction_update.category_id is not None:
        # Verify category exists
        cat_result = await session.execute(
            select(Category).where(Category.id == transaction_update.category_id)
        )
        if not cat_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )
        transaction.category_id = transaction_update.category_id

    if transaction_update.manually_assigned_category is not None:
        transaction.manually_assigned_category = (
            transaction_update.manually_assigned_category
        )

    if transaction_update.is_recurring is not None:
        transaction.is_recurring = transaction_update.is_recurring

    if transaction_update.is_advance_shared_account is not None:
        transaction.is_advance_shared_account = (
            transaction_update.is_advance_shared_account
        )

    if transaction_update.is_manually_reviewed is not None:
        transaction.is_manually_reviewed = transaction_update.is_manually_reviewed

    await session.commit()

    return SuccessResponse(message="Transaction saved successfully")


@router.post("/upload", response_model=UploadTransactionsResponse)
async def upload_transactions(
    files: List[UploadFile] = File(...),
    current_user: CurrentUser = None,
    session: AsyncSession = Depends(get_session),
) -> UploadTransactionsResponse:
    """Upload transaction files (CSV) for processing.

    Note: This is a placeholder implementation. The actual parsing logic
    from BelfiusTransactionParser would need to be ported.
    """
    upload_timestamp = datetime.now()
    created = 0
    updated = 0

    for file in files:
        # Read file content
        content = await file.read()
        try:
            text_content = content.decode("utf-8")
            lines = text_content.splitlines()

            # TODO: Implement actual transaction parsing
            # This would use a parser similar to BelfiusTransactionParser
            # For now, just count lines as a placeholder
            created += len(lines) - 1  # Assume first line is header

        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not decode file {file.filename}. Expected UTF-8 encoding.",
            )

    return UploadTransactionsResponse(
        created=created,
        updated=updated,
        upload_timestamp=upload_timestamp,
    )


@router.get("/distinct-counterparty-names", response_model=List[str])
async def get_distinct_counterparty_names(
    bank_account: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> List[str]:
    """Get distinct counterparty names for a bank account."""
    normalized = BankAccount.normalize_account_number(bank_account)

    # Check user access
    access_result = await session.execute(
        select(UserBankAccountLink).where(
            UserBankAccountLink.user_id == current_user.id,
            UserBankAccountLink.bank_account_number == normalized,
        )
    )
    if not access_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    result = await session.execute(
        select(Transaction.counterparty_id)
        .where(Transaction.bank_account_id == normalized)
        .distinct()
    )
    names = result.scalars().all()
    return list(names)


@router.get("/distinct-counterparty-accounts", response_model=List[str])
async def get_distinct_counterparty_accounts(
    bank_account: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> List[str]:
    """Get distinct counterparty account numbers for a bank account."""
    normalized = BankAccount.normalize_account_number(bank_account)

    # Check user access
    access_result = await session.execute(
        select(UserBankAccountLink).where(
            UserBankAccountLink.user_id == current_user.id,
            UserBankAccountLink.bank_account_number == normalized,
        )
    )
    if not access_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    result = await session.execute(
        select(Counterparty.account_number)
        .join(Transaction, Transaction.counterparty_id == Counterparty.name)
        .where(Transaction.bank_account_id == normalized)
        .distinct()
    )
    accounts = result.scalars().all()
    return [acc for acc in accounts if acc]  # Filter out empty strings

