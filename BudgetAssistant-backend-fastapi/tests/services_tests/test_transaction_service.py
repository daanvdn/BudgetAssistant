"""Tests for TransactionService.

Port of BudgetAssistant-backend/pybackend.tests.test_services.TransactionsServiceTests
"""

from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from common.enums import TransactionTypeEnum
from models import BankAccount, Category, Counterparty, Transaction, User
from models.associations import UserBankAccountLink
from schemas import TransactionQuery, TransactionUpdate
from services.transaction_service import TransactionService


@pytest_asyncio.fixture
async def user(async_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        password_hash="hashed_password123",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def bank_account(async_session: AsyncSession) -> BankAccount:
    """Create a test bank account."""
    bank_account = BankAccount(account_number="123456789")
    async_session.add(bank_account)
    await async_session.commit()
    await async_session.refresh(bank_account)
    return bank_account


@pytest_asyncio.fixture
async def bank_account_with_user(async_session: AsyncSession, user: User) -> BankAccount:
    """Create a test bank account associated with user."""
    bank_account = BankAccount(account_number="test_account")
    async_session.add(bank_account)
    await async_session.flush()

    link = UserBankAccountLink(
        user_id=user.id,
        bank_account_number=bank_account.account_number,
    )
    async_session.add(link)
    await async_session.commit()
    await async_session.refresh(bank_account)
    return bank_account


@pytest_asyncio.fixture
async def category(async_session: AsyncSession) -> Category:
    """Create a test category."""
    category = Category(
        name="Test Category",
        qualified_name="Test Category",
        type=TransactionTypeEnum.EXPENSES,
        is_root=True,
    )
    async_session.add(category)
    await async_session.commit()
    await async_session.refresh(category)
    return category


@pytest_asyncio.fixture
async def counterparty(async_session: AsyncSession) -> Counterparty:
    """Create a test counterparty."""
    counterparty = Counterparty(
        name="Test Counterparty",
        account_number="987654321",
    )
    async_session.add(counterparty)
    await async_session.commit()
    await async_session.refresh(counterparty)
    return counterparty


@pytest_asyncio.fixture
async def service() -> TransactionService:
    """Get TransactionService instance."""
    return TransactionService()


async def create_transaction(
    async_session: AsyncSession,
    bank_account: BankAccount,
    counterparty: Counterparty,
    amount: float = -10.0,
    is_manually_reviewed: bool = False,
    category_id: int | None = None,
    manually_assigned_category: bool = False,
    upload_timestamp: datetime | None = None,
    transaction_number: str | None = None,
) -> Transaction:
    """Helper to create a test transaction."""
    if transaction_number is None:
        # Generate unique transaction number
        import uuid

        transaction_number = str(uuid.uuid4())

    transaction_id = Transaction.create_transaction_id(transaction_number, bank_account.account_number)

    transaction = Transaction(
        transaction_id=transaction_id,
        bank_account_id=bank_account.account_number,
        booking_date=date.today(),
        statement_number="001",
        counterparty_id=counterparty.name,
        transaction_number=transaction_number,
        transaction="Test transaction",
        currency_date=date.today(),
        amount=amount,
        currency="EUR",
        country_code="BE",
        communications="Test communication",
        category_id=category_id,
        manually_assigned_category=manually_assigned_category,
        is_manually_reviewed=is_manually_reviewed,
        upload_timestamp=upload_timestamp or datetime.now(timezone.utc),
    )
    async_session.add(transaction)
    await async_session.flush()
    return transaction


class TestTransactionService:
    """Tests for TransactionService operations."""

    @pytest.mark.asyncio
    async def test_page_uncategorized_transactions_returns_transactions(
        self,
        async_session: AsyncSession,
        service: TransactionService,
    ):
        """Test that page_uncategorized_transactions returns transactions needing review."""
        # Create bank account
        bank_account = BankAccount(account_number="123456789")
        async_session.add(bank_account)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transactions - 3 expenses (negative), 1 revenue (positive)
        # All with is_manually_reviewed=False
        transaction1 = await create_transaction(
            async_session, bank_account, counterparty, amount=-10.0, is_manually_reviewed=False, category_id=None
        )
        transaction2 = await create_transaction(
            async_session, bank_account, counterparty, amount=-10.0, is_manually_reviewed=False, category_id=None
        )
        transaction3 = await create_transaction(
            async_session, bank_account, counterparty, amount=-10.0, is_manually_reviewed=False, category_id=None
        )
        transaction4 = await create_transaction(
            async_session, bank_account, counterparty, amount=10.0, is_manually_reviewed=False, category_id=1
        )
        await async_session.commit()

        transactions, total = await service.page_uncategorized_transactions(
            bank_account=bank_account.account_number,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="amount",
            transaction_type=TransactionTypeEnum.EXPENSES,
            session=async_session,
        )

        assert total == 3
        transaction_ids = [t.transaction_id for t in transactions]
        assert transaction1.transaction_id in transaction_ids
        assert transaction2.transaction_id in transaction_ids
        assert transaction3.transaction_id in transaction_ids
        assert transaction4.transaction_id not in transaction_ids

    @pytest.mark.asyncio
    async def test_page_uncategorized_transactions_returns_empty_if_no_transactions(
        self,
        async_session: AsyncSession,
        bank_account: BankAccount,
        service: TransactionService,
    ):
        """Test that page_transactions_to_manually_review returns empty if no transactions."""
        transactions, total = await service.page_uncategorized_transactions(
            bank_account=bank_account.account_number,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="transaction_id",
            transaction_type=TransactionTypeEnum.EXPENSES,
            session=async_session,
        )

        assert transactions == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_count_uncategorized_transactions_returns_count(
        self,
        async_session: AsyncSession,
        service: TransactionService,
    ):
        """Test that count_uncategorized_transactions returns correct count."""
        # Create bank account
        bank_account = BankAccount(account_number="123456789")
        async_session.add(bank_account)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create 4 transactions that need manual review
        await create_transaction(
            async_session, bank_account, counterparty, amount=-10.0, is_manually_reviewed=False, category_id=None
        )
        await create_transaction(
            async_session, bank_account, counterparty, amount=-10.0, is_manually_reviewed=False, category_id=None
        )
        await create_transaction(
            async_session, bank_account, counterparty, amount=-10.0, is_manually_reviewed=False, category_id=None
        )
        await create_transaction(
            async_session, bank_account, counterparty, amount=10.0, is_manually_reviewed=False, category_id=10
        )
        await async_session.commit()

        count = await service.count_uncategorized_transactions(
            bank_account=bank_account.account_number,
            session=async_session,
        )

        assert count == 3

    @pytest.mark.asyncio
    async def test_count_uncategorized_transactions_returns_zero_if_no_transactions(
        self,
        async_session: AsyncSession,
        bank_account: BankAccount,
        service: TransactionService,
    ):
        """Test that count_uncategorized_transactions returns zero if no transactions."""
        count = await service.count_uncategorized_transactions(
            bank_account=bank_account.account_number,
            session=async_session,
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_save_transaction_updates_existing_transaction(
        self,
        async_session: AsyncSession,
        service: TransactionService,
        category: Category,
    ):
        """Test that save_transaction updates an existing transaction."""
        # Create bank account
        bank_account = BankAccount(account_number="123456789")
        async_session.add(bank_account)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transaction with manually_assigned_category=False
        transaction = await create_transaction(
            async_session, bank_account, counterparty, manually_assigned_category=False
        )
        await async_session.commit()

        # Update transaction
        update_data = TransactionUpdate(
            manually_assigned_category=True,
            category_id=category.id,
        )
        updated_transaction = await service.save_transaction(
            transaction_id=transaction.transaction_id,
            update_data=update_data,
            session=async_session,
        )

        assert updated_transaction.manually_assigned_category is True
        assert updated_transaction.category_id == category.id

    @pytest.mark.asyncio
    async def test_save_transaction_raises_error_if_transaction_not_exist(
        self,
        async_session: AsyncSession,
        service: TransactionService,
    ):
        """Test that save_transaction raises ValueError if transaction doesn't exist."""
        update_data = TransactionUpdate(manually_assigned_category=True)

        with pytest.raises(ValueError) as exc_info:
            await service.save_transaction(
                transaction_id="nonexistent",
                update_data=update_data,
                session=async_session,
            )

        assert "Transaction with id 'nonexistent' does not exist" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_page_transactions_pagination(
        self,
        async_session: AsyncSession,
        user: User,
        service: TransactionService,
    ):
        """Test that page_transactions handles pagination correctly."""
        # Create bank account associated with user
        bank_account = BankAccount(account_number="test_account")
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=bank_account.account_number,
        )
        async_session.add(link)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create 99 transactions
        transactions = []
        for i in range(99):
            transaction = await create_transaction(
                async_session,
                bank_account,
                counterparty,
                amount=-10.0,
                transaction_number=f"TXN{i:03d}",
            )
            transactions.append(transaction)
        await async_session.commit()

        # Sort transactions by transaction_id for comparison
        transactions.sort(key=lambda t: t.transaction_id)

        # Check all pages from 0 to 9 (0-indexed pages)
        for page_num in range(10):
            response_transactions, total = await service.page_transactions(
                query=None,
                page=page_num,
                size=10,
                sort_order="asc",
                sort_property="transaction_id",
                user=user,
                session=async_session,
            )

            # Verify total_elements is always 99
            assert total == 99

            # Calculate expected content size (10 for pages 0-8, 9 for page 9)
            expected_size = 9 if page_num == 9 else 10
            assert len(response_transactions) == expected_size

            # Calculate expected transactions for this page
            start_idx = page_num * 10
            end_idx = min(start_idx + 10, 99)
            expected_transaction_ids = [t.transaction_id for t in transactions[start_idx:end_idx]]

            # Verify content matches expected transactions
            actual_transaction_ids = [t.transaction_id for t in response_transactions]
            assert actual_transaction_ids == expected_transaction_ids

    @pytest.mark.asyncio
    async def test_page_transactions_upload_timestamp_filter(
        self,
        async_session: AsyncSession,
        user: User,
        service: TransactionService,
    ):
        """Test that page_transactions filters by upload_timestamp correctly."""
        # Create bank account associated with user
        bank_account = BankAccount(account_number="test_account")
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=bank_account.account_number,
        )
        async_session.add(link)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create 10 transactions with first upload timestamp
        upload_timestamp_1 = datetime(2025, 5, 1, 15, 53, 37, 0, tzinfo=timezone.utc)
        transactions_1 = []
        for i in range(10):
            transaction = await create_transaction(
                async_session,
                bank_account,
                counterparty,
                amount=-10.0,
                upload_timestamp=upload_timestamp_1,
                transaction_number=f"TXN_TS1_{i:03d}",
            )
            transactions_1.append(transaction)

        # Create 10 transactions with second upload timestamp
        upload_timestamp_2 = datetime(2025, 5, 2, 15, 53, 37, 0, tzinfo=timezone.utc)
        transactions_2 = []
        for i in range(10):
            transaction = await create_transaction(
                async_session,
                bank_account,
                counterparty,
                amount=-10.0,
                upload_timestamp=upload_timestamp_2,
                transaction_number=f"TXN_TS2_{i:03d}",
            )
            transactions_2.append(transaction)
        await async_session.commit()

        # Query transactions with first upload timestamp
        query = TransactionQuery(
            transaction_type=TransactionTypeEnum.BOTH,
            upload_timestamp=upload_timestamp_1,
        )

        response_transactions, total = await service.page_transactions(
            query=query,
            page=0,
            size=10,
            sort_order="desc",
            sort_property="booking_date",
            user=user,
            session=async_session,
        )

        # Verify total_elements is 10
        assert total == 10

        # Verify all transactions have the first upload timestamp
        for transaction in response_transactions:
            assert transaction.upload_timestamp == upload_timestamp_1

        # Verify content matches transactions_1
        response_ids = {t.transaction_id for t in response_transactions}
        expected_ids = {t.transaction_id for t in transactions_1}
        assert response_ids == expected_ids

    @pytest.mark.asyncio
    async def test_get_transaction_returns_transaction(
        self,
        async_session: AsyncSession,
        service: TransactionService,
    ):
        """Test that get_transaction returns a transaction by ID."""
        # Create bank account
        bank_account = BankAccount(account_number="123456789")
        async_session.add(bank_account)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transaction
        transaction = await create_transaction(async_session, bank_account, counterparty)
        await async_session.commit()

        # Retrieve transaction
        retrieved = await service.get_transaction(
            transaction_id=transaction.transaction_id,
            session=async_session,
        )

        assert retrieved is not None
        assert retrieved.transaction_id == transaction.transaction_id

    @pytest.mark.asyncio
    async def test_get_transaction_returns_none_if_not_exist(
        self,
        async_session: AsyncSession,
        service: TransactionService,
    ):
        """Test that get_transaction returns None if transaction doesn't exist."""
        retrieved = await service.get_transaction(
            transaction_id="nonexistent",
            session=async_session,
        )

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_or_create_transaction_creates_new(
        self,
        async_session: AsyncSession,
        bank_account: BankAccount,
        counterparty: Counterparty,
        service: TransactionService,
    ):
        """Test that get_or_create_transaction creates a new transaction."""
        from schemas import TransactionCreate

        transaction_in = TransactionCreate(
            bank_account_id=bank_account.account_number,
            booking_date=date.today(),
            statement_number="001",
            counterparty_id=counterparty.name,
            transaction_number="NEW_TXN_001",
            transaction="Test transaction",
            currency_date=date.today(),
            amount=-50.0,
            currency="EUR",
            country_code="BE",
            communications="Test communication",
        )

        upload_timestamp = datetime.now(timezone.utc)
        transaction, created = await service.get_or_create_transaction(
            transaction_in=transaction_in,
            upload_timestamp=upload_timestamp,
            session=async_session,
        )

        assert created is True
        assert transaction is not None
        assert transaction.amount == -50.0

    @pytest.mark.asyncio
    async def test_get_or_create_transaction_returns_existing(
        self,
        async_session: AsyncSession,
        bank_account: BankAccount,
        counterparty: Counterparty,
        service: TransactionService,
    ):
        """Test that get_or_create_transaction returns existing transaction."""
        from schemas import TransactionCreate

        # Create existing transaction
        existing = await create_transaction(
            async_session, bank_account, counterparty, transaction_number="EXISTING_TXN"
        )
        await async_session.commit()

        # Try to create with same transaction_number
        transaction_in = TransactionCreate(
            bank_account_id=bank_account.account_number,
            booking_date=date.today(),
            statement_number="001",
            counterparty_id=counterparty.name,
            transaction_number="EXISTING_TXN",
            transaction="Test transaction",
            currency_date=date.today(),
            amount=-100.0,  # Different amount
            currency="EUR",
            country_code="BE",
            communications="Test communication",
        )

        upload_timestamp = datetime.now(timezone.utc)
        transaction, created = await service.get_or_create_transaction(
            transaction_in=transaction_in,
            upload_timestamp=upload_timestamp,
            session=async_session,
        )

        assert created is False
        assert transaction.transaction_id == existing.transaction_id

    @pytest.mark.asyncio
    async def test_page_transactions_filters_by_transaction_type_expenses(
        self,
        async_session: AsyncSession,
        user: User,
        service: TransactionService,
    ):
        """Test that page_transactions filters by transaction type (expenses)."""
        # Create bank account associated with user
        bank_account = BankAccount(account_number="test_account")
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=bank_account.account_number,
        )
        async_session.add(link)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create expense transaction
        expense_txn = await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-50.0,
            transaction_number="EXPENSE_1",
        )
        # Create revenue transaction
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=100.0,
            transaction_number="REVENUE_1",
        )
        await async_session.commit()

        # Query expenses only
        query = TransactionQuery(transaction_type=TransactionTypeEnum.EXPENSES)
        transactions, total = await service.page_transactions(
            query=query,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="transaction_id",
            user=user,
            session=async_session,
        )

        assert total == 1
        assert transactions[0].transaction_id == expense_txn.transaction_id

    @pytest.mark.asyncio
    async def test_page_transactions_filters_by_transaction_type_revenue(
        self,
        async_session: AsyncSession,
        user: User,
        service: TransactionService,
    ):
        """Test that page_transactions filters by transaction type (revenue)."""
        # Create bank account associated with user
        bank_account = BankAccount(account_number="test_account")
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=bank_account.account_number,
        )
        async_session.add(link)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create expense transaction
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-50.0,
            transaction_number="EXPENSE_1",
        )
        # Create revenue transaction
        revenue_txn = await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=100.0,
            transaction_number="REVENUE_1",
        )
        await async_session.commit()

        # Query revenue only
        query = TransactionQuery(transaction_type=TransactionTypeEnum.REVENUE)
        transactions, total = await service.page_transactions(
            query=query,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="transaction_id",
            user=user,
            session=async_session,
        )

        assert total == 1
        assert transactions[0].transaction_id == revenue_txn.transaction_id

    @pytest.mark.asyncio
    async def test_page_transactions_filters_by_amount_range(
        self,
        async_session: AsyncSession,
        user: User,
        service: TransactionService,
    ):
        """Test that page_transactions filters by min and max amount."""
        # Create bank account associated with user
        bank_account = BankAccount(account_number="test_account")
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=bank_account.account_number,
        )
        async_session.add(link)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transactions with different amounts
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-10.0,
            transaction_number="TXN_10",
        )
        txn2 = await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-50.0,
            transaction_number="TXN_50",
        )
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-100.0,
            transaction_number="TXN_100",
        )
        await async_session.commit()

        # Query with amount range
        query = TransactionQuery(min_amount=-60.0, max_amount=-40.0)
        transactions, total = await service.page_transactions(
            query=query,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="transaction_id",
            user=user,
            session=async_session,
        )

        assert total == 1
        assert transactions[0].transaction_id == txn2.transaction_id

    @pytest.mark.asyncio
    async def test_page_transactions_filters_by_counterparty_name(
        self,
        async_session: AsyncSession,
        user: User,
        service: TransactionService,
    ):
        """Test that page_transactions filters by counterparty name."""
        # Create bank account associated with user
        bank_account = BankAccount(account_number="test_account")
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=bank_account.account_number,
        )
        async_session.add(link)
        await async_session.flush()

        # Create two counterparties
        counterparty1 = Counterparty(name="Supermarket ABC", account_number="111111111")
        counterparty2 = Counterparty(name="Gas Station XYZ", account_number="222222222")
        async_session.add(counterparty1)
        async_session.add(counterparty2)
        await async_session.flush()

        # Create transactions
        txn1 = await create_transaction(async_session, bank_account, counterparty1, transaction_number="TXN_ABC")
        await create_transaction(async_session, bank_account, counterparty2, transaction_number="TXN_XYZ")
        await async_session.commit()

        # Query by counterparty name (partial match)
        query = TransactionQuery(counterparty_name="ABC")
        transactions, total = await service.page_transactions(
            query=query,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="transaction_id",
            user=user,
            session=async_session,
        )

        assert total == 1
        assert transactions[0].transaction_id == txn1.transaction_id

    @pytest.mark.asyncio
    async def test_page_transactions_sorts_ascending(
        self,
        async_session: AsyncSession,
        user: User,
        service: TransactionService,
    ):
        """Test that page_transactions sorts in ascending order."""
        # Create bank account associated with user
        bank_account = BankAccount(account_number="test_account")
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=bank_account.account_number,
        )
        async_session.add(link)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transactions with different amounts
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-100.0,
            transaction_number="TXN_100",
        )
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-10.0,
            transaction_number="TXN_10",
        )
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-50.0,
            transaction_number="TXN_50",
        )
        await async_session.commit()

        # Query sorted by amount ascending
        transactions, total = await service.page_transactions(
            query=None,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="amount",
            user=user,
            session=async_session,
        )

        assert total == 3
        assert transactions[0].amount == -100.0
        assert transactions[1].amount == -50.0
        assert transactions[2].amount == -10.0

    @pytest.mark.asyncio
    async def test_page_transactions_sorts_descending(
        self,
        async_session: AsyncSession,
        user: User,
        service: TransactionService,
    ):
        """Test that page_transactions sorts in descending order."""
        # Create bank account associated with user
        bank_account = BankAccount(account_number="test_account")
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=bank_account.account_number,
        )
        async_session.add(link)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transactions with different amounts
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-100.0,
            transaction_number="TXN_100",
        )
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-10.0,
            transaction_number="TXN_10",
        )
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-50.0,
            transaction_number="TXN_50",
        )
        await async_session.commit()

        # Query sorted by amount descending
        transactions, total = await service.page_transactions(
            query=None,
            page=0,
            size=10,
            sort_order="desc",
            sort_property="amount",
            user=user,
            session=async_session,
        )

        assert total == 3
        assert transactions[0].amount == -10.0
        assert transactions[1].amount == -50.0
        assert transactions[2].amount == -100.0

    @pytest.mark.asyncio
    async def test_page_transactions_returns_empty_for_user_without_accounts(
        self,
        async_session: AsyncSession,
        user: User,
        service: TransactionService,
    ):
        """Test that page_transactions returns empty for user without bank accounts."""
        transactions, total = await service.page_transactions(
            query=None,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="transaction_id",
            user=user,
            session=async_session,
        )

        assert transactions == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_distinct_counterparty_names(
        self,
        async_session: AsyncSession,
        bank_account: BankAccount,
        service: TransactionService,
    ):
        """Test that get_distinct_counterparty_names returns unique names."""
        # Create counterparties
        counterparty1 = Counterparty(name="Counterparty A", account_number="111111111")
        counterparty2 = Counterparty(name="Counterparty B", account_number="222222222")
        async_session.add(counterparty1)
        async_session.add(counterparty2)
        await async_session.flush()

        # Create transactions - 2 with counterparty1, 1 with counterparty2
        await create_transaction(async_session, bank_account, counterparty1, transaction_number="TXN_1")
        await create_transaction(async_session, bank_account, counterparty1, transaction_number="TXN_2")
        await create_transaction(async_session, bank_account, counterparty2, transaction_number="TXN_3")
        await async_session.commit()

        names = await service.get_distinct_counterparty_names(
            bank_account=bank_account.account_number,
            session=async_session,
        )

        assert len(names) == 2
        assert "Counterparty A" in names
        assert "Counterparty B" in names

    @pytest.mark.asyncio
    async def test_page_transactions_to_manually_review_filters_by_revenue(
        self,
        async_session: AsyncSession,
        service: TransactionService,
    ):
        """Test that page_transactions_to_manually_review filters by revenue type."""
        # Create bank account
        bank_account = BankAccount(account_number="123456789")
        async_session.add(bank_account)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create expense and revenue transactions
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=-50.0,
            is_manually_reviewed=False,
        )
        revenue_txn = await create_transaction(
            async_session,
            bank_account,
            counterparty,
            amount=100.0,
            is_manually_reviewed=False,
        )
        await async_session.commit()

        # Query for revenue only
        transactions, total = await service.page_uncategorized_transactions(
            bank_account=bank_account.account_number,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="amount",
            transaction_type=TransactionTypeEnum.REVENUE,
            session=async_session,
        )

        assert total == 1
        assert transactions[0].transaction_id == revenue_txn.transaction_id

    @pytest.mark.asyncio
    async def test_page_uncategorized_transactions_filters_transactions_with_category(
        self,
        async_session: AsyncSession,
        service: TransactionService,
    ):
        """Test that page_transactions_to_manually_review excludes reviewed transactions."""
        # Create bank account
        bank_account = BankAccount(account_number="123456789")
        async_session.add(bank_account)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transactions - one reviewed, one not reviewed
        await create_transaction(
            async_session, bank_account, counterparty, amount=-50.0, is_manually_reviewed=True, category_id=1
        )
        no_cat_txn = await create_transaction(
            async_session, bank_account, counterparty, amount=-50.0, is_manually_reviewed=False, category_id=None
        )
        await async_session.commit()

        # Query for transactions to review
        transactions, total = await service.page_uncategorized_transactions(
            bank_account=bank_account.account_number,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="amount",
            transaction_type=TransactionTypeEnum.EXPENSES,
            session=async_session,
        )

        assert total == 1
        assert transactions[0].transaction_id == no_cat_txn.transaction_id

    @pytest.mark.asyncio
    async def test_save_transaction_updates_is_recurring(
        self,
        async_session: AsyncSession,
        service: TransactionService,
    ):
        """Test that save_transaction updates is_recurring field."""
        # Create bank account
        bank_account = BankAccount(account_number="123456789")
        async_session.add(bank_account)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transaction with is_recurring=False
        transaction = await create_transaction(async_session, bank_account, counterparty)
        await async_session.commit()

        # Update is_recurring
        update_data = TransactionUpdate(is_recurring=True)
        updated = await service.save_transaction(
            transaction_id=transaction.transaction_id,
            update_data=update_data,
            session=async_session,
        )

        assert updated.is_recurring is True

    @pytest.mark.asyncio
    async def test_save_transaction_updates_is_advance_shared_account(
        self,
        async_session: AsyncSession,
        service: TransactionService,
    ):
        """Test that save_transaction updates is_advance_shared_account field."""
        # Create bank account
        bank_account = BankAccount(account_number="123456789")
        async_session.add(bank_account)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transaction with is_advance_shared_account=False
        transaction = await create_transaction(async_session, bank_account, counterparty)
        await async_session.commit()

        # Update is_advance_shared_account
        update_data = TransactionUpdate(is_advance_shared_account=True)
        updated = await service.save_transaction(
            transaction_id=transaction.transaction_id,
            update_data=update_data,
            session=async_session,
        )

        assert updated.is_advance_shared_account is True

    @pytest.mark.asyncio
    async def test_save_transaction_updates_is_manually_reviewed(
        self,
        async_session: AsyncSession,
        service: TransactionService,
    ):
        """Test that save_transaction updates is_manually_reviewed field."""
        # Create bank account
        bank_account = BankAccount(account_number="123456789")
        async_session.add(bank_account)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transaction with is_manually_reviewed=False
        transaction = await create_transaction(async_session, bank_account, counterparty)
        await async_session.commit()

        # Update is_manually_reviewed
        update_data = TransactionUpdate(is_manually_reviewed=True)
        updated = await service.save_transaction(
            transaction_id=transaction.transaction_id,
            update_data=update_data,
            session=async_session,
        )

        assert updated.is_manually_reviewed is True

    @pytest.mark.asyncio
    async def test_page_transactions_filters_by_category_id(
        self,
        async_session: AsyncSession,
        user: User,
        category: Category,
        service: TransactionService,
    ):
        """Test that page_transactions filters by category_id."""
        # Create bank account associated with user
        bank_account = BankAccount(account_number="test_account")
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=bank_account.account_number,
        )
        async_session.add(link)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transactions - one with category, one without
        txn_with_category = await create_transaction(
            async_session,
            bank_account,
            counterparty,
            category_id=category.id,
            transaction_number="TXN_CAT",
        )
        await create_transaction(
            async_session,
            bank_account,
            counterparty,
            category_id=None,
            transaction_number="TXN_NO_CAT",
        )
        await async_session.commit()

        # Query by category_id
        query = TransactionQuery(category_id=category.id)
        transactions, total = await service.page_transactions(
            query=query,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="transaction_id",
            user=user,
            session=async_session,
        )

        assert total == 1
        assert transactions[0].transaction_id == txn_with_category.transaction_id

    @pytest.mark.asyncio
    async def test_page_transactions_filters_by_transaction_or_communication(
        self,
        async_session: AsyncSession,
        user: User,
        service: TransactionService,
    ):
        """Test that page_transactions filters by transaction or communication text."""
        # Create bank account associated with user
        bank_account = BankAccount(account_number="test_account")
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=bank_account.account_number,
        )
        async_session.add(link)
        await async_session.flush()

        # Create counterparty
        counterparty = Counterparty(name="Test Counterparty", account_number="987654321")
        async_session.add(counterparty)
        await async_session.flush()

        # Create transactions with different communications
        import uuid

        txn_id_1 = str(uuid.uuid4())
        txn_id_2 = str(uuid.uuid4())

        txn1 = Transaction(
            transaction_id=Transaction.create_transaction_id(txn_id_1, bank_account.account_number),
            bank_account_id=bank_account.account_number,
            booking_date=date.today(),
            statement_number="001",
            counterparty_id=counterparty.name,
            transaction_number=txn_id_1,
            transaction="Groceries purchase",
            currency_date=date.today(),
            amount=-50.0,
            currency="EUR",
            country_code="BE",
            communications="Payment for groceries",
            upload_timestamp=datetime.now(timezone.utc),
        )
        txn2 = Transaction(
            transaction_id=Transaction.create_transaction_id(txn_id_2, bank_account.account_number),
            bank_account_id=bank_account.account_number,
            booking_date=date.today(),
            statement_number="001",
            counterparty_id=counterparty.name,
            transaction_number=txn_id_2,
            transaction="Fuel purchase",
            currency_date=date.today(),
            amount=-30.0,
            currency="EUR",
            country_code="BE",
            communications="Payment for fuel",
            upload_timestamp=datetime.now(timezone.utc),
        )
        async_session.add(txn1)
        async_session.add(txn2)
        await async_session.commit()

        # Query by transaction text
        query = TransactionQuery(transaction_or_communication="groceries")
        transactions, total = await service.page_transactions(
            query=query,
            page=0,
            size=10,
            sort_order="asc",
            sort_property="transaction_id",
            user=user,
            session=async_session,
        )

        assert total == 1
        assert transactions[0].transaction_id == txn1.transaction_id
