"""Tests for BankAccountService.

Port of BudgetAssistant-backend/pybackend.tests.test_services.BankAccountsServiceTests
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from models import BankAccount, User
from models.associations import UserBankAccountLink
from services.bank_account_service import BankAccountService


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
async def service() -> BankAccountService:
    """Get BankAccountService instance."""
    return BankAccountService()


class TestBankAccountService:
    """Tests for BankAccountService operations."""

    @pytest.mark.asyncio
    async def test_get_or_create_bank_account_creates_new_account(
        self, async_session: AsyncSession, user: User, service: BankAccountService
    ):
        """Test that get_or_create_bank_account creates a new account."""
        account_number = "123456789"

        bank_account = await service.get_or_create_bank_account(account_number, user, async_session)

        assert bank_account.account_number == account_number
        # Check user is associated with bank account
        accounts = await service.find_by_user(user, async_session)
        assert bank_account in accounts

    @pytest.mark.asyncio
    async def test_get_or_create_bank_account_adds_user_to_existing_account(
        self, async_session: AsyncSession, user: User, service: BankAccountService
    ):
        """Test that get_or_create_bank_account adds user to existing account."""
        account_number = "123456789"

        # Create existing bank account
        existing_account = BankAccount(account_number=account_number)
        async_session.add(existing_account)
        await async_session.commit()

        # Get or create should return existing and add user
        bank_account = await service.get_or_create_bank_account(account_number, user, async_session)

        assert bank_account.account_number == existing_account.account_number
        # Check user is associated with bank account
        accounts = await service.find_by_user(user, async_session)
        assert bank_account in accounts

    @pytest.mark.asyncio
    async def test_find_by_user_returns_accounts(
        self, async_session: AsyncSession, user: User, service: BankAccountService
    ):
        """Test that find_by_user returns user's bank accounts."""
        account_number = "123456789"

        # Create bank account and associate with user
        bank_account = BankAccount(account_number=account_number)
        async_session.add(bank_account)
        await async_session.flush()

        link = UserBankAccountLink(
            user_id=user.id,
            bank_account_number=account_number,
        )
        async_session.add(link)
        await async_session.commit()

        # Find accounts for user
        accounts = await service.find_by_user(user, async_session)

        assert bank_account in accounts

    @pytest.mark.asyncio
    async def test_get_bank_account_returns_account(self, async_session: AsyncSession, service: BankAccountService):
        """Test that get_bank_account returns existing account."""
        account_number = "123456789"

        # Create bank account
        bank_account = BankAccount(account_number=account_number)
        async_session.add(bank_account)
        await async_session.commit()

        # Retrieve account
        retrieved_account = await service.get_bank_account(account_number, async_session)

        assert retrieved_account is not None
        assert retrieved_account.account_number == bank_account.account_number

    @pytest.mark.asyncio
    async def test_get_bank_account_returns_none_if_not_exist(
        self, async_session: AsyncSession, service: BankAccountService
    ):
        """Test that get_bank_account returns None if account doesn't exist."""
        retrieved_account = await service.get_bank_account("nonexistent", async_session)

        assert retrieved_account is None

    @pytest.mark.asyncio
    async def test_save_alias_updates_alias(self, async_session: AsyncSession, service: BankAccountService):
        """Test that save_alias updates the bank account alias."""
        account_number = "123456789"
        alias = "My Savings Account"

        # Create bank account
        bank_account = BankAccount(account_number=account_number)
        async_session.add(bank_account)
        await async_session.commit()

        # Save alias
        updated_account = await service.save_alias(account_number, alias, async_session)

        assert updated_account.alias == alias

    @pytest.mark.asyncio
    async def test_save_alias_raises_error_if_account_not_exist(
        self, async_session: AsyncSession, service: BankAccountService
    ):
        """Test that save_alias raises ValueError if account doesn't exist."""
        with pytest.raises(ValueError) as exc_info:
            await service.save_alias("nonexistent", "Alias", async_session)

        assert "Bank account with account number nonexistent does not exist" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_user_has_access_returns_true_for_associated_user(
        self, async_session: AsyncSession, user: User, service: BankAccountService
    ):
        """Test that user_has_access returns True for associated user."""
        account_number = "123456789"

        # Create bank account and associate with user
        await service.get_or_create_bank_account(account_number, user, async_session)

        # Check access
        has_access = await service.user_has_access(user, account_number, async_session)

        assert has_access is True

    @pytest.mark.asyncio
    async def test_user_has_access_returns_false_for_unassociated_user(
        self, async_session: AsyncSession, user: User, service: BankAccountService
    ):
        """Test that user_has_access returns False for unassociated user."""
        account_number = "123456789"

        # Create bank account without associating user
        bank_account = BankAccount(account_number=account_number)
        async_session.add(bank_account)
        await async_session.commit()

        # Check access
        has_access = await service.user_has_access(user, account_number, async_session)

        assert has_access is False

    @pytest.mark.asyncio
    async def test_get_account_numbers_for_user_returns_account_numbers(
        self, async_session: AsyncSession, user: User, service: BankAccountService
    ):
        """Test that get_account_numbers_for_user returns user's account numbers."""
        account_number1 = "123456789"
        account_number2 = "987654321"

        # Create bank accounts and associate with user
        await service.get_or_create_bank_account(account_number1, user, async_session)
        await service.get_or_create_bank_account(account_number2, user, async_session)

        # Get account numbers
        account_numbers = await service.get_account_numbers_for_user(user, async_session)

        assert account_number1 in account_numbers
        assert account_number2 in account_numbers
        assert len(account_numbers) == 2

    @pytest.mark.asyncio
    async def test_get_account_numbers_for_user_returns_empty_list(
        self, async_session: AsyncSession, user: User, service: BankAccountService
    ):
        """Test that get_account_numbers_for_user returns empty list for user without accounts."""
        account_numbers = await service.get_account_numbers_for_user(user, async_session)

        assert account_numbers == []

    @pytest.mark.asyncio
    async def test_find_by_user_returns_empty_list_for_user_without_accounts(
        self, async_session: AsyncSession, user: User, service: BankAccountService
    ):
        """Test that find_by_user returns empty list for user without accounts."""
        accounts = await service.find_by_user(user, async_session)

        assert accounts == []
