"""Counterparty SQLModel database model."""

import re
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from .associations import UserCounterpartyLink

if TYPE_CHECKING:
    from .category import Category
    from .transaction import Transaction
    from .user import User


class Counterparty(SQLModel, table=True):
    """Counterparty model representing transaction counterparties."""

    __tablename__ = "counterparty"

    name: str = Field(primary_key=True, max_length=255)
    account_number: str = Field(default="")
    street_and_number: str | None = Field(default=None)
    zip_code_and_city: str | None = Field(default=None)

    # Foreign keys
    category_id: int | None = Field(default=None, foreign_key="category.id")

    # Relationships
    category: Optional["Category"] = Relationship(
        back_populates="counterparties",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    users: List["User"] = Relationship(
        back_populates="counterparties",
        link_model=UserCounterpartyLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    transactions: List["Transaction"] = Relationship(
        back_populates="counterparty",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def normalize_counterparty(counterparty_name: str) -> str:
        """Normalize counterparty name by reducing whitespace and converting to lowercase."""
        return re.sub(r"\s{2,}", " ", counterparty_name.strip().lower())

