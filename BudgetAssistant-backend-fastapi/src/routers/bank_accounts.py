"""Bank accounts router."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from models import BankAccount, User
from models.associations import UserBankAccountLink
from routers.auth import CurrentUser
from schemas import (
    BankAccountCreate,
    BankAccountRead,
    BankAccountUpdate,
    SaveAliasRequest,
    SuccessResponse,
)

router = APIRouter(prefix="/bank-accounts", tags=["Bank Accounts"])


@router.get("", response_model=List[BankAccountRead])
async def get_bank_accounts_for_user(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> List[BankAccountRead]:
    """Get all bank accounts for the current user."""
    # Query bank accounts through the link table
    result = await session.execute(
        select(BankAccount)
        .join(UserBankAccountLink)
        .where(UserBankAccountLink.user_id == current_user.id)
    )
    bank_accounts = result.scalars().all()
    return [BankAccountRead.model_validate(ba) for ba in bank_accounts]


@router.post("", response_model=BankAccountRead, status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    bank_account: BankAccountCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BankAccountRead:
    """Create a new bank account and associate it with the current user."""
    # Normalize account number
    normalized_account = BankAccount.normalize_account_number(
        bank_account.account_number
    )

    # Check if account already exists
    result = await session.execute(
        select(BankAccount).where(BankAccount.account_number == normalized_account)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # If it exists, just associate with user if not already
        link_result = await session.execute(
            select(UserBankAccountLink).where(
                UserBankAccountLink.user_id == current_user.id,
                UserBankAccountLink.bank_account_number == normalized_account,
            )
        )
        if not link_result.scalar_one_or_none():
            link = UserBankAccountLink(
                user_id=current_user.id, bank_account_number=normalized_account
            )
            session.add(link)
            await session.commit()
        return BankAccountRead.model_validate(existing)

    # Create new bank account
    db_bank_account = BankAccount(
        account_number=normalized_account,
        alias=bank_account.alias,
    )
    session.add(db_bank_account)
    await session.flush()

    # Create association with user
    link = UserBankAccountLink(
        user_id=current_user.id, bank_account_number=normalized_account
    )
    session.add(link)
    await session.commit()
    await session.refresh(db_bank_account)

    return BankAccountRead.model_validate(db_bank_account)


@router.get("/{account_number}", response_model=BankAccountRead)
async def get_bank_account(
    account_number: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BankAccountRead:
    """Get a specific bank account by account number."""
    normalized = BankAccount.normalize_account_number(account_number)

    # Check user has access to this account
    result = await session.execute(
        select(BankAccount)
        .join(UserBankAccountLink)
        .where(
            UserBankAccountLink.user_id == current_user.id,
            BankAccount.account_number == normalized,
        )
    )
    bank_account = result.scalar_one_or_none()

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
    normalized = BankAccount.normalize_account_number(account_number)

    # Check user has access to this account
    result = await session.execute(
        select(BankAccount)
        .join(UserBankAccountLink)
        .where(
            UserBankAccountLink.user_id == current_user.id,
            BankAccount.account_number == normalized,
        )
    )
    bank_account = result.scalar_one_or_none()

    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )

    if updates.alias is not None:
        bank_account.alias = updates.alias

    await session.commit()
    await session.refresh(bank_account)

    return BankAccountRead.model_validate(bank_account)


@router.post("/save-alias", response_model=SuccessResponse)
async def save_alias(
    request: SaveAliasRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Save an alias for a bank account."""
    normalized = BankAccount.normalize_account_number(request.bank_account)

    # Check user has access to this account
    result = await session.execute(
        select(BankAccount)
        .join(UserBankAccountLink)
        .where(
            UserBankAccountLink.user_id == current_user.id,
            BankAccount.account_number == normalized,
        )
    )
    bank_account = result.scalar_one_or_none()

    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )

    bank_account.alias = request.alias
    await session.commit()

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
    normalized = BankAccount.normalize_account_number(account_number)

    result = await session.execute(
        select(UserBankAccountLink).where(
            UserBankAccountLink.user_id == current_user.id,
            UserBankAccountLink.bank_account_number == normalized,
        )
    )
    link = result.scalar_one_or_none()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account association not found",
        )

    await session.delete(link)
    await session.commit()

    return SuccessResponse(message="Bank account removed from user")

