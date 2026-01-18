"""Tests for User model."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import User, BankAccount


class TestUser:
    """Test cases for the User model."""

    @pytest.mark.asyncio
    async def test_create_user_with_valid_data(self, async_session):
        """Test creating a user with valid data."""
        user = User(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password_hash="hashedpassword123",
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.email == "test@example.com"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_create_user_with_duplicate_username(self, async_session):
        """Test that creating a user with duplicate username raises error."""
        user1 = User(
            username="duplicateuser",
            first_name="First",
            last_name="User",
            email="first@example.com",
            password_hash="password123",
        )
        async_session.add(user1)
        await async_session.commit()

        user2 = User(
            username="duplicateuser",
            first_name="Second",
            last_name="User",
            email="second@example.com",
            password_hash="password456",
        )
        async_session.add(user2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_retrieve_user_by_username(self, async_session):
        """Test retrieving a user by username."""
        username = "testuser"
        user = User(
            username=username,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password_hash="securepassword123",
        )
        async_session.add(user)
        await async_session.commit()

        result = await async_session.execute(
            select(User).where(User.username == username)
        )
        retrieved_user = result.scalar_one_or_none()

        assert retrieved_user is not None
        assert retrieved_user.username == username
        assert retrieved_user.id == user.id

    @pytest.mark.asyncio
    async def test_user_str_method(self, async_session):
        """Test the __str__ method returns the username."""
        user = User(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password_hash="securepassword123",
        )
        assert str(user) == "testuser"

    @pytest.mark.asyncio
    async def test_user_default_values(self, async_session):
        """Test that user has correct default values."""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="password",
        )
        async_session.add(user)
        await async_session.commit()

        assert user.is_active is True
        assert user.is_superuser is False
        assert user.first_name == ""
        assert user.last_name == ""

    @pytest.mark.asyncio
    async def test_associate_bank_account_with_user(self, async_session):
        """Test associating a bank account with a user."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        async_session.add(bank_account)
        await async_session.commit()

        user = User(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password_hash="securepassword123",
        )
        user.bank_accounts.append(bank_account)
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        assert len(user.bank_accounts) == 1
        assert user.bank_accounts[0].account_number == "123456"

    @pytest.mark.asyncio
    async def test_retrieve_non_existent_user(self, async_session):
        """Test retrieving a non-existent user returns None."""
        result = await async_session.execute(
            select(User).where(User.username == "nonexistent_user")
        )
        user = result.scalar_one_or_none()
        assert user is None

    @pytest.mark.asyncio
    async def test_update_user_password(self, async_session):
        """Test updating a user's password."""
        user = User(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password_hash="securepassword123",
        )
        async_session.add(user)
        await async_session.commit()

        new_password_hash = "newsecurepassword456"
        user.password_hash = new_password_hash
        await async_session.commit()
        await async_session.refresh(user)

        assert user.password_hash == new_password_hash

    @pytest.mark.asyncio
    async def test_remove_bank_account_from_user(self, async_session):
        """Test removing a bank account from a user doesn't affect other users."""
        from models.associations import UserBankAccountLink

        bank_account = BankAccount(account_number="123456789", alias="Savings Account")
        async_session.add(bank_account)
        await async_session.commit()

        user1 = User(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password_hash="securepassword123",
        )
        user1.bank_accounts.append(bank_account)
        async_session.add(user1)

        user2 = User(
            username="otheruser",
            first_name="Other",
            last_name="User",
            email="other@example.com",
            password_hash="anotherpassword123",
        )
        async_session.add(user2)
        await async_session.commit()
        await async_session.refresh(user1)
        await async_session.refresh(user2)

        # Check user1 has the bank account
        result1 = await async_session.execute(
            select(UserBankAccountLink).where(
                UserBankAccountLink.user_id == user1.id,
                UserBankAccountLink.bank_account_number == bank_account.account_number,
            )
        )
        assert result1.scalar_one_or_none() is not None

        # Check user2 doesn't have the bank account
        result2 = await async_session.execute(
            select(UserBankAccountLink).where(
                UserBankAccountLink.user_id == user2.id,
                UserBankAccountLink.bank_account_number == bank_account.account_number,
            )
        )
        assert result2.scalar_one_or_none() is None

        # Remove bank account from user1
        link = await async_session.execute(
            select(UserBankAccountLink).where(
                UserBankAccountLink.user_id == user1.id,
                UserBankAccountLink.bank_account_number == bank_account.account_number,
            )
        )
        link_to_delete = link.scalar_one()
        await async_session.delete(link_to_delete)
        await async_session.commit()

        # Check user1 no longer has the bank account
        result3 = await async_session.execute(
            select(UserBankAccountLink).where(
                UserBankAccountLink.user_id == user1.id,
                UserBankAccountLink.bank_account_number == bank_account.account_number,
            )
        )
        assert result3.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_related_name_bank_accounts_to_users(self, async_session):
        """Test the back_populates relationship from BankAccount to Users."""
        bank_account = BankAccount(account_number="12345")
        async_session.add(bank_account)
        await async_session.commit()

        user = User(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password_hash="securepassword123",
        )
        user.bank_accounts.append(bank_account)
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(bank_account)

        assert len(bank_account.users) == 1
        assert bank_account.users[0].username == "testuser"
