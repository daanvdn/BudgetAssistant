"""Pytest configuration and fixtures for async database testing."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Import all models to ensure they're registered with SQLModel metadata
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from db.database import engine as production_engine
from db.database import get_session
from main import app

# Import all models to ensure foreign keys can be resolved
from models import (  # noqa: F401
    BankAccount,
    Category,
    CategoryTree,
    Counterparty,
    Transaction,
    User,
)
from models.password_reset_token import PasswordResetToken  # noqa: F401
from models.token_blocklist import TokenBlocklist  # noqa: F401

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session", autouse=True)
def cleanup_production_engine():
    """Cleanup production engine after all tests complete"""
    yield
    # Dispose the production engine to prevent hanging

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(production_engine.dispose())
        else:
            loop.run_until_complete(production_engine.dispose())
    except RuntimeError:
        # If no event loop, create one for cleanup
        asyncio.run(production_engine.dispose())


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create an async engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# Test user credentials
TEST_USER_PASSWORD = "TestPassword123"  # Must have uppercase for password validation
TEST_USER_EMAIL = "testuser@example.com"


@pytest_asyncio.fixture(scope="function")
async def client(async_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing without authentication.

    This fixture overrides the get_session dependency to use the test database
    so that the FastAPI app uses the same database as the test session.
    """
    # Create a session maker for the test database
    test_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    # Override the get_session dependency to use the test database
    async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_session] = get_test_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(
    async_engine,
) -> AsyncGenerator[tuple[AsyncClient, str], None]:
    """Create an async HTTP client with authentication.

    This fixture registers a new user, logs in, and returns the client
    with the access token. Returns a tuple of (client, access_token).
    """
    # Create a session maker for the test database
    test_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    # Override the get_session dependency to use the test database
    async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_session] = get_test_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Register a new user
            register_response = await client.post(
                "/api/auth/register",
                json={
                    "password": TEST_USER_PASSWORD,
                    "email": TEST_USER_EMAIL,
                },
            )
            # Log registration result for debugging
            if register_response.status_code != 201:
                print(f"Registration response: {register_response.status_code} - {register_response.text}")

            # Login to get token - use /login endpoint with JSON body
            login_response = await client.post(
                "/api/auth/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD,
                },
            )

            if login_response.status_code == 200:
                token_data = login_response.json()
                access_token = token_data["access_token"]
                yield client, access_token
            else:
                # Log login failure for debugging
                print(f"Login response: {login_response.status_code} - {login_response.text}")
                # If login fails, yield without auth (tests will fail appropriately)
                yield client, ""
    finally:
        # Clean up the dependency override
        app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture(scope="function")
async def auth_headers(authenticated_client) -> dict[str, str]:
    """Return headers dict with authorization bearer token."""
    client, access_token = authenticated_client
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture(scope="function")
async def seed_category_trees(async_session: AsyncSession) -> dict:
    """Seed category trees for testing.

    Returns a dict with 'expenses' and 'revenue' CategoryTree objects.
    """
    from common.enums import TransactionTypeEnum
    from services.providers import CategoryTreeProvider

    provider = CategoryTreeProvider()
    expenses_tree = await provider.provide(TransactionTypeEnum.EXPENSES, async_session)
    revenue_tree = await provider.provide(TransactionTypeEnum.REVENUE, async_session)
    await async_session.commit()

    return {
        "expenses": expenses_tree,
        "revenue": revenue_tree,
    }


@pytest_asyncio.fixture(scope="function")
async def seed_categories(authenticated_client) -> None:
    """Seed the database with required categories for testing."""
    client, access_token = authenticated_client
    headers = {"Authorization": f"Bearer {access_token}"}

    # The categories are typically seeded via init_db, so this might not be needed
    # But we ensure we can at least get categories
    await client.get("/api/categories", headers=headers)
    # Categories should exist from database initialization


@pytest_asyncio.fixture(scope="function")
async def seed_bank_account(authenticated_client) -> str:
    """Seed a bank account for testing and return the account number."""
    client, access_token = authenticated_client
    headers = {"Authorization": f"Bearer {access_token}"}

    test_account_number = "BE68539007547034"

    # Create a bank account
    await client.post(
        "/api/bank-accounts",
        json={
            "account_number": test_account_number,
            "alias": "Test Account",
        },
        headers=headers,
    )

    return test_account_number
