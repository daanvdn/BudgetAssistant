"""Transactions router."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import CurrentUser
from db.database import get_session
from models import Category
from schemas import (
    CountResponse,
    ErrorResponse,
    PageTransactionsInContextRequest,
    PageTransactionsRequest,
    PageUncategorizedTransactionsRequest,
    PaginatedResponse,
    SuccessResponse,
    TransactionRead,
    TransactionUpdate,
    UploadTransactionsResponse,
)
from services.bank_account_service import bank_account_service
from services.transaction_service import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/page", response_model=PaginatedResponse[TransactionRead])
async def page_transactions(
    request: PageTransactionsRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[TransactionRead]:
    """Get paginated transactions with optional filtering."""
    transactions, total_elements = await transaction_service.page_transactions(
        query=request.query,
        page=request.page,
        size=request.size,
        sort_order=request.sort_order.value,
        sort_property=request.sort_property.value,
        user=current_user,
        session=session,
    )

    content = [TransactionRead.model_validate(t) for t in transactions]
    return PaginatedResponse.create(
        content=content,
        page=request.page,
        size=request.size,
        total_elements=total_elements,
    )


@router.post("/page-in-context", response_model=PaginatedResponse[TransactionRead])
async def page_transactions_in_context(
    request: PageTransactionsInContextRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[TransactionRead]:
    """Get paginated transactions for a specific context (period, category)."""
    query = request.query

    # Check user access
    if not await bank_account_service.user_has_access(current_user, query.bank_account, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    (
        transactions,
        total_elements,
    ) = await transaction_service.page_transactions_in_context(
        bank_account=query.bank_account,
        category_id=query.category_id,
        transaction_type=query.transaction_type,
        page=request.page,
        size=request.size,
        sort_order=request.sort_order.value,
        sort_property=request.sort_property.value,
        session=session,
        start_date=None,
        end_date=None,
    )

    content = [TransactionRead.model_validate(t) for t in transactions]
    return PaginatedResponse.create(
        content=content,
        page=request.page,
        size=request.size,
        total_elements=total_elements,
    )


@router.post("/page-uncategorized", response_model=PaginatedResponse[TransactionRead])
async def page_uncategorized_transactions(
    request: PageUncategorizedTransactionsRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[TransactionRead]:
    """Get paginated transactions that need manual review."""
    # Check user access
    if not await bank_account_service.user_has_access(current_user, request.bank_account, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    (
        transactions,
        total_elements,
    ) = await transaction_service.page_uncategorized_transactions(
        bank_account=request.bank_account,
        page=request.page,
        size=request.size,
        sort_order=request.sort_order.value,
        sort_property=request.sort_property.value,
        transaction_type=request.transaction_type,
        session=session,
    )

    content = [TransactionRead.model_validate(t) for t in transactions]
    return PaginatedResponse.create(
        content=content,
        page=request.page,
        size=request.size,
        total_elements=total_elements,
    )


@router.get("/count-uncategorized", response_model=CountResponse)
async def count_uncategorized_transactions(
    bank_account: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> CountResponse:
    """Count transactions that need manual review for a bank account."""
    # Check user access
    if not await bank_account_service.user_has_access(current_user, bank_account, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    count = await transaction_service.count_uncategorized_transactions(
        bank_account=bank_account,
        session=session,
    )

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
    transaction = await transaction_service.get_transaction(transaction_id, session)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    # Check user access to the transaction's bank account
    if not await bank_account_service.user_has_access(current_user, transaction.bank_account_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this transaction",
        )

    # Verify category exists if provided
    if transaction_update.category_id is not None:
        cat_result = await session.execute(select(Category).where(Category.id == transaction_update.category_id))
        if not cat_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )

    # Update transaction via service
    await transaction_service.save_transaction(
        transaction_id=transaction_id,
        update_data=transaction_update,
        session=session,
    )

    return SuccessResponse(message="Transaction saved successfully")


@router.post("/upload", response_model=UploadTransactionsResponse)
async def upload_transactions(
    files: List[UploadFile] = File(...),
    current_user: CurrentUser = None,
    session: AsyncSession = Depends(get_session),
) -> UploadTransactionsResponse:
    """Upload transaction files (CSV) for processing.

    Supports Belfius CSV format. Files are parsed and transactions
    are created or updated in the database.
    """
    from services.transaction_parser import belfius_parser

    upload_timestamp = datetime.now()
    total_created = 0
    total_updated = 0

    for file in files:
        # Read file content
        content = await file.read()
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                text_content = content.decode("latin-1")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Could not decode file {file.filename}. Expected UTF-8 or Latin-1 encoding.",
                )

        lines = text_content.splitlines()

        # Parse using Belfius parser
        parse_result = await belfius_parser.parse(
            lines=lines,
            user=current_user,
            session=session,
            upload_timestamp=upload_timestamp,
        )

        total_created += parse_result.created
        total_updated += parse_result.updated

    return UploadTransactionsResponse(
        created=total_created,
        updated=total_updated,
        upload_timestamp=upload_timestamp,
    )


@router.get("/distinct-counterparty-names", response_model=List[str])
async def get_distinct_counterparty_names(
    bank_account: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> List[str]:
    """Get distinct counterparty names for a bank account."""
    # Check user access
    if not await bank_account_service.user_has_access(current_user, bank_account, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    return await transaction_service.get_distinct_counterparty_names(
        bank_account=bank_account,
        session=session,
    )


@router.get("/distinct-counterparty-accounts", response_model=List[str])
async def get_distinct_counterparty_accounts(
    bank_account: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> List[str]:
    """Get distinct counterparty account numbers for a bank account."""
    # Check user access
    if not await bank_account_service.user_has_access(current_user, bank_account, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    return await transaction_service.get_distinct_counterparty_accounts(
        bank_account=bank_account,
        session=session,
    )
