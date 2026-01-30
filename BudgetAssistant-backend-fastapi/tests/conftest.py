"""Pytest configuration and fixtures for async database testing."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from db.database import get_session
from httpx import ASGITransport, AsyncClient
from main import app

# Import all models to ensure they're registered
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
TEST_USER_USERNAME = "testuser"
TEST_USER_PASSWORD = "testpassword123"
TEST_USER_EMAIL = "testuser@example.com"


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing without authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


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
                    "username": TEST_USER_USERNAME,
                    "password": TEST_USER_PASSWORD,
                    "email": TEST_USER_EMAIL,
                },
            )
            # It's okay if registration fails (user might already exist in same session)

            # Login to get token
            login_response = await client.post(
                "/api/auth/token",
                data={
                    "username": TEST_USER_USERNAME,
                    "password": TEST_USER_PASSWORD,
                },
            )

            if login_response.status_code == 200:
                token_data = login_response.json()
                access_token = token_data["access_token"]
                yield client, access_token
            else:
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
async def seed_categories(authenticated_client) -> None:
    """Seed the database with required categories for testing."""
    client, access_token = authenticated_client
    headers = {"Authorization": f"Bearer {access_token}"}

    # The categories are typically seeded via init_db, so this might not be needed
    # But we ensure we can at least get categories
    response = await client.get("/api/categories", headers=headers)
    # Categories should exist from database initialization


@pytest_asyncio.fixture(scope="function")
async def seed_bank_account(authenticated_client) -> str:
    """Seed a bank account for testing and return the account number."""
    client, access_token = authenticated_client
    headers = {"Authorization": f"Bearer {access_token}"}

    test_account_number = "BE68539007547034"

    # Create a bank account
    response = await client.post(
        "/api/bank-accounts",
        json={
            "account_number": test_account_number,
            "alias": "Test Account",
        },
        headers=headers,
    )

    return test_account_number
