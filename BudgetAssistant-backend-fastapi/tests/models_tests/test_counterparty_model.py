"""Tests for Counterparty model."""

import pytest
from sqlalchemy.exc import IntegrityError

from models import Counterparty, User
from tests.utils import assert_persisted


class TestCounterparty:
    """Test cases for the Counterparty model."""

    @pytest.mark.asyncio
    async def test_create_counterparty_with_valid_data(self, async_session):
        """Test creating a counterparty with valid data and name normalization."""
        counterparty = Counterparty(
            name=Counterparty.normalize_counterparty(" Counterparty   1 2  "),
            account_number="ACC001",
        )
        async_session.add(counterparty)
        await async_session.commit()

        assert counterparty.name == "counterparty 1 2"

        # Re-query from database to verify persistence
        await assert_persisted(
            async_session,
            Counterparty,
            "name",
            "counterparty 1 2",
            {"name": "counterparty 1 2", "account_number": "ACC001"},
        )

    @pytest.mark.asyncio
    async def test_create_counterparty_with_duplicate_name(self, async_session):
        """Test that duplicate counterparty names raise an error."""
        counterparty1 = Counterparty(
            name=Counterparty.normalize_counterparty(" Counterparty   1 2  "),
            account_number="ACC001",
        )
        async_session.add(counterparty1)
        await async_session.commit()

        counterparty2 = Counterparty(
            name="counterparty 1 2",
            account_number="ACC002",
        )
        async_session.add(counterparty2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

    def test_normalize_counterparty_name(self):
        """Test counterparty name normalization."""
        normalized = Counterparty.normalize_counterparty(" Counterparty   1 2  ")
        assert normalized == "counterparty 1 2"

    @pytest.mark.asyncio
    async def test_str_method_returns_name(self, async_session):
        """Test that __str__ returns the counterparty name."""
        counterparty = Counterparty(name="test counterparty", account_number="ACC001")
        assert str(counterparty) == "test counterparty"

    @pytest.mark.asyncio
    async def test_add_users_to_counterparty(self, async_session):
        """Test adding users to a counterparty."""
        counterparty = Counterparty(
            name=Counterparty.normalize_counterparty(" Counterparty   1 2  "),
            account_number="ACC001",
        )
        async_session.add(counterparty)
        await async_session.commit()

        user1 = User(
            first_name="Test1",
            last_name="User1",
            email="user1@example.com",
            password_hash="password1",
        )
        user2 = User(
            first_name="Test2",
            last_name="User2",
            email="user2@example.com",
            password_hash="password2",
        )

        user1.counterparties.append(counterparty)
        user2.counterparties.append(counterparty)
        async_session.add_all([user1, user2])
        await async_session.commit()

        # Query the users associated with the counterparty
        from sqlalchemy import select

        from models.associations import UserCounterpartyLink

        result = await async_session.execute(
            select(User)
            .join(UserCounterpartyLink)
            .where(UserCounterpartyLink.counterparty_name == counterparty.name)
        )
        users = result.scalars().all()

        assert len(users) == 2
        emails = [u.email for u in users]
        assert "user1@example.com" in emails
        assert "user2@example.com" in emails

    @pytest.mark.asyncio
    async def test_counterparty_with_optional_fields(self, async_session):
        """Test creating counterparty with optional fields."""
        counterparty = Counterparty(
            name="test counterparty",
            account_number="ACC001",
            street_and_number="123 Main St",
            zip_code_and_city="12345 Test City",
        )
        async_session.add(counterparty)
        await async_session.commit()

        assert counterparty.street_and_number == "123 Main St"
        assert counterparty.zip_code_and_city == "12345 Test City"

        # Re-query from database to verify optional fields are persisted
        await assert_persisted(
            async_session,
            Counterparty,
            "name",
            "test counterparty",
            {
                "name": "test counterparty",
                "account_number": "ACC001",
                "street_and_number": "123 Main St",
                "zip_code_and_city": "12345 Test City",
            },
        )

    @pytest.mark.asyncio
    async def test_counterparty_default_optional_fields_are_none(self, async_session):
        """Test that optional fields default to None."""
        counterparty = Counterparty(
            name="test counterparty",
            account_number="ACC001",
        )
        async_session.add(counterparty)
        await async_session.commit()

        assert counterparty.street_and_number is None
        assert counterparty.zip_code_and_city is None
        assert counterparty.category_id is None

        # Re-query from database to verify default None values are persisted
        await assert_persisted(
            async_session,
            Counterparty,
            "name",
            "test counterparty",
            {
                "name": "test counterparty",
                "account_number": "ACC001",
                "street_and_number": None,
                "zip_code_and_city": None,
                "category_id": None,
            },
        )
