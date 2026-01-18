"""Tests for database configuration."""

import pytest
from sqlmodel import SQLModel

from db import create_db_and_tables, get_session


class TestDatabaseConfiguration:
    """Test cases for database configuration."""

    @pytest.mark.asyncio
    async def test_create_db_and_tables(self, async_engine):
        """Test that database tables can be created."""
        # Tables are already created in the fixture
        # This test verifies the engine is working
        async with async_engine.begin() as conn:
            # Check that we can execute queries
            result = await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    SQLModel.metadata.tables["user"].select()
                )
            )
            # Should return empty result, but no error
            assert result is not None

    @pytest.mark.asyncio
    async def test_session_can_be_used(self, async_session):
        """Test that async session can be used for queries."""
        from sqlalchemy import text

        result = await async_session.execute(text("SELECT 1"))
        row = result.scalar()
        assert row == 1

    @pytest.mark.asyncio
    async def test_session_rollback_on_error(self, async_session):
        """Test that session rolls back on error."""
        from models import User
        from sqlalchemy.exc import IntegrityError

        # Add a user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="password",
        )
        async_session.add(user)
        await async_session.commit()

        # Try to add duplicate - should fail
        user2 = User(
            username="testuser",  # Duplicate
            email="test2@example.com",
            password_hash="password2",
        )
        async_session.add(user2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

        # Session should be rolled back
        await async_session.rollback()

