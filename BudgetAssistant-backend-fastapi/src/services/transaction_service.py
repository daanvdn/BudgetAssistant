"""Transaction service with async SQLModel operations."""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.enums import TransactionTypeEnum
from models import BankAccount, Counterparty, Transaction, User
from models.associations import UserBankAccountLink
from schemas import (
    TransactionCreate,
    TransactionQuery,
    TransactionUpdate,
)


class TransactionService:
    """Service for transaction operations."""

    def _build_base_filter(self, user_account_numbers: List[str]):
        """Build base filter for user's accessible transactions."""
        return Transaction.bank_account_id.in_(user_account_numbers)

    def _build_query_filter(
        self,
        query: Optional[TransactionQuery],
        user_account_numbers: List[str],
    ):
        """Build SQLAlchemy filter from TransactionQuery."""
        conditions = [self._build_base_filter(user_account_numbers)]

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
            conditions.append(Transaction.counterparty_id.ilike(f"%{query.counterparty_name}%"))

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

        if query.start_date:
            conditions.append(Transaction.booking_date >= query.start_date)

        if query.end_date:
            conditions.append(Transaction.booking_date <= query.end_date)

        if query.upload_timestamp:
            conditions.append(Transaction.upload_timestamp == query.upload_timestamp)

        if query.manually_assigned_category:
            conditions.append(Transaction.manually_assigned_category.is_(True))

        return and_(*conditions)

    def _get_sort_column(self, sort_property: str, sort_order: str):
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
        column = sort_map.get(sort_property, Transaction.transaction_id)
        if sort_order.lower() == "desc":
            return column.desc()
        return column

    async def page_transactions(
        self,
        query: Optional[TransactionQuery],
        page: int,
        size: int,
        sort_order: str,
        sort_property: str,
        user: User,
        session: AsyncSession,
    ) -> Tuple[List[Transaction], int]:
        """Get paginated transactions with filtering."""
        # Get user's accessible account numbers
        account_result = await session.execute(
            select(UserBankAccountLink.bank_account_number).where(UserBankAccountLink.user_id == user.id)
        )
        user_accounts = list(account_result.scalars().all())

        if not user_accounts:
            return [], 0

        # Build filter
        filter_condition = self._build_query_filter(query, user_accounts)

        # Count total
        count_query = select(func.count()).select_from(Transaction).where(filter_condition)
        total_result = await session.execute(count_query)
        total_elements = total_result.scalar() or 0

        # Get sorted and paginated results
        sort_column = self._get_sort_column(sort_property, sort_order)
        offset = page * size

        stmt = select(Transaction).where(filter_condition).order_by(sort_column).offset(offset).limit(size)
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        return transactions, total_elements

    async def page_transactions_in_context(
        self,
        bank_account: str,
        category_id: int,
        transaction_type: TransactionTypeEnum,
        page: int,
        size: int,
        sort_order: str,
        sort_property: str,
        session: AsyncSession,
    ) -> Tuple[List[Transaction], int]:
        """Get paginated transactions for a specific context (period, category)."""
        normalized = BankAccount.normalize_account_number(bank_account)

        conditions = [
            Transaction.bank_account_id == normalized,
            Transaction.category_id == category_id,
        ]

        if transaction_type == TransactionTypeEnum.REVENUE:
            conditions.append(Transaction.amount >= 0)
        elif transaction_type == TransactionTypeEnum.EXPENSES:
            conditions.append(Transaction.amount < 0)

        # TODO: Parse period string to date range
        # For now, skip period filtering

        filter_condition = and_(*conditions)

        # Count total
        count_query = select(func.count()).select_from(Transaction).where(filter_condition)
        total_result = await session.execute(count_query)
        total_elements = total_result.scalar() or 0

        # Get sorted and paginated results
        sort_column = self._get_sort_column(sort_property, sort_order)
        offset = page * size

        stmt = select(Transaction).where(filter_condition).order_by(sort_column).offset(offset).limit(size)
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        return transactions, total_elements

    async def page_transactions_to_manually_review(
        self,
        bank_account: str,
        page: int,
        size: int,
        sort_order: str,
        sort_property: str,
        transaction_type: TransactionTypeEnum,
        session: AsyncSession,
    ) -> Tuple[List[Transaction], int]:
        """Get paginated transactions that need manual review."""
        normalized = BankAccount.normalize_account_number(bank_account)

        conditions = [
            Transaction.bank_account_id == normalized,
            Transaction.is_manually_reviewed.is_(False),
        ]

        if transaction_type == TransactionTypeEnum.REVENUE:
            conditions.append(Transaction.amount >= 0)
        elif transaction_type == TransactionTypeEnum.EXPENSES:
            conditions.append(Transaction.amount < 0)

        filter_condition = and_(*conditions)

        # Count total
        count_query = select(func.count()).select_from(Transaction).where(filter_condition)
        total_result = await session.execute(count_query)
        total_elements = total_result.scalar() or 0

        # Get sorted and paginated results
        sort_column = self._get_sort_column(sort_property, sort_order)
        offset = page * size

        stmt = select(Transaction).where(filter_condition).order_by(sort_column).offset(offset).limit(size)
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        return transactions, total_elements

    async def count_transactions_to_manually_review(
        self,
        bank_account: str,
        session: AsyncSession,
    ) -> int:
        """Count transactions that need manual review."""
        normalized = BankAccount.normalize_account_number(bank_account)

        count_query = (
            select(func.count())
            .select_from(Transaction)
            .where(
                Transaction.bank_account_id == normalized,
                Transaction.is_manually_reviewed.is_(False),
            )
        )
        result = await session.execute(count_query)
        return result.scalar() or 0

    async def get_transaction(
        self,
        transaction_id: str,
        session: AsyncSession,
    ) -> Optional[Transaction]:
        """Get a transaction by ID."""
        result = await session.execute(select(Transaction).where(Transaction.transaction_id == transaction_id))
        return result.scalar_one_or_none()

    async def save_transaction(
        self,
        transaction_id: str,
        update_data: TransactionUpdate,
        session: AsyncSession,
    ) -> Transaction:
        """Update a transaction."""
        transaction = await self.get_transaction(transaction_id, session)
        if not transaction:
            raise ValueError(f"Transaction with id '{transaction_id}' does not exist")

        # Update fields
        if update_data.category_id is not None:
            transaction.category_id = update_data.category_id

        if update_data.manually_assigned_category is not None:
            transaction.manually_assigned_category = update_data.manually_assigned_category

        if update_data.is_recurring is not None:
            transaction.is_recurring = update_data.is_recurring

        if update_data.is_advance_shared_account is not None:
            transaction.is_advance_shared_account = update_data.is_advance_shared_account

        if update_data.is_manually_reviewed is not None:
            transaction.is_manually_reviewed = update_data.is_manually_reviewed

        await session.commit()
        await session.refresh(transaction)
        return transaction

    async def create_transaction(
        self,
        transaction_in: TransactionCreate,
        upload_timestamp: datetime,
        session: AsyncSession,
    ) -> Transaction:
        """Create a new transaction."""
        transaction_id = Transaction.create_transaction_id(
            transaction_in.transaction_number,
            transaction_in.bank_account_id,
        )

        transaction = Transaction(
            transaction_id=transaction_id,
            bank_account_id=transaction_in.bank_account_id,
            booking_date=transaction_in.booking_date,
            statement_number=transaction_in.statement_number,
            counterparty_id=transaction_in.counterparty_id,
            transaction_number=transaction_in.transaction_number,
            transaction=transaction_in.transaction,
            currency_date=transaction_in.currency_date,
            amount=transaction_in.amount,
            currency=transaction_in.currency,
            bic=transaction_in.bic,
            country_code=transaction_in.country_code,
            communications=transaction_in.communications,
            category_id=transaction_in.category_id,
            manually_assigned_category=transaction_in.manually_assigned_category,
            is_recurring=transaction_in.is_recurring,
            is_advance_shared_account=transaction_in.is_advance_shared_account,
            upload_timestamp=upload_timestamp,
        )

        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)
        return transaction

    async def get_or_create_transaction(
        self,
        transaction_in: TransactionCreate,
        upload_timestamp: datetime,
        session: AsyncSession,
    ) -> Tuple[Transaction, bool]:
        """Get or create a transaction. Returns (transaction, created)."""
        transaction_id = Transaction.create_transaction_id(
            transaction_in.transaction_number,
            transaction_in.bank_account_id,
        )

        existing = await self.get_transaction(transaction_id, session)
        if existing:
            return existing, False

        transaction = await self.create_transaction(transaction_in, upload_timestamp, session)
        return transaction, True

    async def get_distinct_counterparty_names(
        self,
        bank_account: str,
        session: AsyncSession,
    ) -> List[str]:
        """Get distinct counterparty names for a bank account."""
        normalized = BankAccount.normalize_account_number(bank_account)

        result = await session.execute(
            select(Transaction.counterparty_id).where(Transaction.bank_account_id == normalized).distinct()
        )
        return [name for name in result.scalars().all() if name]

    async def get_distinct_counterparty_accounts(
        self,
        bank_account: str,
        session: AsyncSession,
    ) -> List[str]:
        """Get distinct counterparty account numbers for a bank account."""
        normalized = BankAccount.normalize_account_number(bank_account)

        result = await session.execute(
            select(Counterparty.account_number)
            .join(Transaction, Transaction.counterparty_id == Counterparty.name)
            .where(Transaction.bank_account_id == normalized)
            .distinct()
        )
        return [acc for acc in result.scalars().all() if acc]


# Singleton instance
transaction_service = TransactionService()
