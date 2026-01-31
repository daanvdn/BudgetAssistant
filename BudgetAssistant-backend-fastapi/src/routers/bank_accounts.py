"""Bank accounts router."""

from typing import List

from db.database import get_session
from fastapi import APIRouter, Depends, HTTPException, status
from routers.auth import CurrentUser
from schemas import (
    BankAccountCreate,
    BankAccountRead,
    BankAccountUpdate,
    SaveAliasRequest,
    SuccessResponse,
)
from services.bank_account_service import bank_account_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/bank-accounts", tags=["Bank Accounts"])


@router.get("", response_model=List[BankAccountRead])
async def get_bank_accounts_for_user(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> List[BankAccountRead]:
    """Get all bank accounts for the current user."""
    bank_accounts = await bank_account_service.find_by_user(current_user, session)
    return [BankAccountRead.model_validate(ba) for ba in bank_accounts]


@router.post("", response_model=BankAccountRead, status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    bank_account: BankAccountCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BankAccountRead:
    """Create a new bank account and associate it with the current user."""
    db_bank_account = await bank_account_service.create_bank_account(
        bank_account, current_user, session
    )

    return BankAccountRead.model_validate(db_bank_account)


@router.get("/{account_number}", response_model=BankAccountRead)
async def get_bank_account(
    account_number: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BankAccountRead:
    """Get a specific bank account by account number."""
    # Check user has access to this account
    if not await bank_account_service.user_has_access(
        current_user, account_number, session
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )

    bank_account = await bank_account_service.get_bank_account(account_number, session)
    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )

    return BankAccountRead.model_validate(bank_account)


@router.patch("/{account_number}", response_model=BankAccountRead)
async def update_bank_account(
    account_number: str,
    updates: BankAccountUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BankAccountRead:
    """Update a bank account's alias."""
    # Check user has access to this account
    if not await bank_account_service.user_has_access(
        current_user, account_number, session
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )

    if updates.alias is not None:
        try:
            bank_account = await bank_account_service.save_alias(
                account_number, updates.alias, session
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account not found",
            )
    else:
        bank_account = await bank_account_service.get_bank_account(
            account_number, session
        )
        if not bank_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bank account not found",
            )

    return BankAccountRead.model_validate(bank_account)


@router.post("/save-alias", response_model=SuccessResponse)
async def save_alias(
    request: SaveAliasRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Save an alias for a bank account."""
    # Check user has access to this account
    if not await bank_account_service.user_has_access(
        current_user, request.bank_account, session
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )

    try:
        await bank_account_service.save_alias(
            request.bank_account, request.alias, session
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )

    return SuccessResponse(message="Alias saved successfully")


@router.delete("/{account_number}", response_model=SuccessResponse)
async def remove_bank_account_from_user(
    account_number: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Remove association between user and bank account.

    Note: This doesn't delete the bank account, just removes the user's access.
    """
    removed = await bank_account_service.remove_user_access(
        current_user, account_number, session
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account association not found",
        )

    return SuccessResponse(message="Bank account removed from user")
