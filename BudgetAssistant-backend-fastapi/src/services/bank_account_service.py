"""Bank Account service with async SQLModel operations."""

from typing import List, Optional

from models import BankAccount, User
from models.associations import UserBankAccountLink
from schemas import BankAccountCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BankAccountService:
    """Service for bank account operations."""

    async def get_or_create_bank_account(
        self,
        account_number: str,
        user: User,
        session: AsyncSession,
    ) -> BankAccount:
        """Get or create a bank account and associate it with the user."""
        normalized = BankAccount.normalize_account_number(account_number)

        # Try to get existing bank account
        result = await session.execute(
            select(BankAccount).where(BankAccount.account_number == normalized)
        )
        bank_account = result.scalar_one_or_none()

        if not bank_account:
            # Create new bank account
            bank_account = BankAccount(account_number=normalized)
            session.add(bank_account)
            await session.flush()

        # Check if user is already associated
        link_result = await session.execute(
            select(UserBankAccountLink).where(
                UserBankAccountLink.user_id == user.id,
                UserBankAccountLink.bank_account_number == normalized,
            )
        )
        if not link_result.scalar_one_or_none():
            # Create association
            link = UserBankAccountLink(
                user_id=user.id,
                bank_account_number=normalized,
            )
            session.add(link)

        await session.commit()
        await session.refresh(bank_account)
        return bank_account

    async def find_by_user(
        self,
        user: User,
        session: AsyncSession,
    ) -> List[BankAccount]:
        """Find all bank accounts for a user."""
        result = await session.execute(
            select(BankAccount)
            .join(UserBankAccountLink)
            .where(UserBankAccountLink.user_id == user.id)
            .distinct()
        )
        return list(result.scalars().all())

    async def get_bank_account(
        self,
        account_number: str,
        session: AsyncSession,
    ) -> Optional[BankAccount]:
        """Get a bank account by account number."""
        normalized = BankAccount.normalize_account_number(account_number)
        result = await session.execute(
            select(BankAccount).where(BankAccount.account_number == normalized)
        )
        return result.scalar_one_or_none()

    async def save_alias(
        self,
        account_number: str,
        alias: str,
        session: AsyncSession,
    ) -> BankAccount:
        """Save an alias for a bank account."""
        bank_account = await self.get_bank_account(account_number, session)
        if not bank_account:
            raise ValueError(
                f"Bank account with account number {account_number} does not exist"
            )

        bank_account.alias = alias
        await session.commit()
        await session.refresh(bank_account)
        return bank_account

    async def create_bank_account(
        self,
        bank_account_in: BankAccountCreate,
        user: User,
        session: AsyncSession,
    ) -> BankAccount:
        """Create a new bank account."""
        return await self.get_or_create_bank_account(
            bank_account_in.account_number,
            user,
            session,
        )

    async def user_has_access(
        self,
        user: User,
        account_number: str,
        session: AsyncSession,
    ) -> bool:
        """Check if user has access to a bank account."""
        normalized = BankAccount.normalize_account_number(account_number)
        result = await session.execute(
            select(UserBankAccountLink).where(
                UserBankAccountLink.user_id == user.id,
                UserBankAccountLink.bank_account_number == normalized,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_account_numbers_for_user(
        self,
        user: User,
        session: AsyncSession,
    ) -> List[str]:
        """Get all account numbers for a user."""
        result = await session.execute(
            select(UserBankAccountLink.bank_account_number).where(
                UserBankAccountLink.user_id == user.id
            )
        )
        return list(result.scalars().all())


# Singleton instance
bank_account_service = BankAccountService()
