"""Database configuration and session management for async SQLite."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

# SQLite async connection string
DATABASE_URL = "sqlite+aiosqlite:///./budgetassistant.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


def get_engine():
    """Get the async engine."""
    return engine


async def create_db_and_tables() -> None:
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_db_and_tables() -> None:
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def init_db() -> None:
    """Initialize the database.

    Creates all database tables and initializes category trees for both
    EXPENSES and REVENUE transaction types if they don't already exist.
    """
    await create_db_and_tables()

    # Initialize category trees
    from enums import TransactionTypeEnum
    from services.providers import CategoryTreeProvider

    async with AsyncSessionLocal() as session:
        try:
            provider = CategoryTreeProvider()
            await provider.provide(TransactionTypeEnum.EXPENSES, session)
            await provider.provide(TransactionTypeEnum.REVENUE, session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
