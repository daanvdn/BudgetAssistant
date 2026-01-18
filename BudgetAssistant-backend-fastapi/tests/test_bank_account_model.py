"""Tests for BankAccount model."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import BankAccount, User


class TestBankAccount:
    """Test cases for the BankAccount model."""

    @pytest.mark.asyncio
    async def test_create_bank_account_with_valid_data(self, async_session):
        """Test creating a bank account with valid data."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        async_session.add(bank_account)
        await async_session.commit()

        assert bank_account.account_number == "123456"
        assert bank_account.alias == "Savings"

    @pytest.mark.asyncio
    async def test_create_bank_account_with_duplicate_account_number(self, async_session):
        """Test that creating a bank account with duplicate account number raises error."""
        bank_account1 = BankAccount(account_number="123456", alias="Savings")
        async_session.add(bank_account1)
        await async_session.commit()

        bank_account2 = BankAccount(account_number="123456", alias="Checking")
        async_session.add(bank_account2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_to_json_includes_all_fields(self, async_session):
        """Test that to_json includes all fields."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        async_session.add(bank_account)
        await async_session.commit()

        bank_account_json = bank_account.to_json()

        assert bank_account_json["account_number"] == "123456"
        assert bank_account_json["alias"] == "Savings"

    def test_normalize_account_number_removes_spaces_and_lowercases(self):
        """Test that normalize_account_number removes spaces and converts to lowercase."""
        normalized = BankAccount.normalize_account_number(" 123 456 ")
        assert normalized == "123456"

    @pytest.mark.asyncio
    async def test_str_method_returns_account_number(self, async_session):
        """Test that __str__ returns the account number."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        assert str(bank_account) == "123456"

    @pytest.mark.asyncio
    async def test_add_multiple_users_to_bank_account(self, async_session):
        """Test adding multiple users to a bank account."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        async_session.add(bank_account)
        await async_session.commit()

        user1 = User(
            username="user1",
            first_name="Test1",
            last_name="User1",
            email="user1@example.com",
            password_hash="password1",
        )
        user2 = User(
            username="user2",
            first_name="Test2",
            last_name="User2",
            email="user2@example.com",
            password_hash="password2",
        )
        user3 = User(
            username="user3",
            first_name="Test3",
            last_name="User3",
            email="user3@example.com",
            password_hash="password3",
        )

        user1.bank_accounts.append(bank_account)
        user2.bank_accounts.append(bank_account)
        user3.bank_accounts.append(bank_account)

        async_session.add_all([user1, user2, user3])
        await async_session.commit()

        # Query the users associated with the bank account using link table
        from sqlalchemy import select
        from models.associations import UserBankAccountLink
        result = await async_session.execute(
            select(User).join(UserBankAccountLink).where(
                UserBankAccountLink.bank_account_number == bank_account.account_number
            )
        )
        users = result.scalars().all()

        assert len(users) == 3
        usernames = [u.username for u in users]
        assert "user1" in usernames
        assert "user2" in usernames
        assert "user3" in usernames

    @pytest.mark.asyncio
    async def test_bank_account_with_null_alias(self, async_session):
        """Test creating a bank account with null alias."""
        bank_account = BankAccount(account_number="789012")
        async_session.add(bank_account)
        await async_session.commit()

        assert bank_account.alias is None

    @pytest.mark.asyncio
    async def test_retrieve_bank_account_by_account_number(self, async_session):
        """Test retrieving a bank account by account number."""
        bank_account = BankAccount(account_number="654321", alias="Checking")
        async_session.add(bank_account)
        await async_session.commit()

        result = await async_session.execute(
            select(BankAccount).where(BankAccount.account_number == "654321")
        )
        retrieved = result.scalar_one_or_none()

        assert retrieved is not None
        assert retrieved.account_number == "654321"
        assert retrieved.alias == "Checking"

