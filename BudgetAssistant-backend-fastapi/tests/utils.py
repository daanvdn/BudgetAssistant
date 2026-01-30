"""Test utility functions for database model testing."""

from typing import Any, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel


async def assert_persisted(
    session: AsyncSession,
    model_class: Type[SQLModel],
    pk_field: str,
    pk_value: Any,
    expected: dict[str, Any],
) -> SQLModel:
    """Re-query the database and verify that the persisted data matches expected values.

    Args:
        session: The async database session.
        model_class: The SQLModel class to query.
        pk_field: The name of the primary key field.
        pk_value: The value of the primary key to query.
        expected: A dictionary of field names to expected values.

    Returns:
        The re-queried model instance.

    Raises:
        AssertionError: If the model is not found or field values don't match.
    """
    session.expire_all()
    stmt = select(model_class).where(getattr(model_class, pk_field) == pk_value)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    assert instance is not None, (
        f"{model_class.__name__} with {pk_field}={pk_value} not found in database"
    )

    for field, expected_value in expected.items():
        actual_value = getattr(instance, field)
        assert actual_value == expected_value, (
            f"Field '{field}' mismatch: expected {expected_value!r}, got {actual_value!r}"
        )

    return instance
