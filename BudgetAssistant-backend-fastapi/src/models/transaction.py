"""Transaction SQLModel database model."""

import hashlib
import json
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from enums import TransactionTypeEnum

if TYPE_CHECKING:
    from .bank_account import BankAccount
    from .category import Category
    from .counterparty import Counterparty


class Transaction(SQLModel, table=True):
    """Transaction model representing financial transactions."""

    __tablename__ = "transaction"

    transaction_id: str = Field(primary_key=True, max_length=64)
    booking_date: date
    statement_number: str
    transaction_number: str = Field(unique=True)
    transaction: str | None = Field(default=None)
    currency_date: date
    amount: float
    currency: str = Field(max_length=255)
    bic: str | None = Field(default=None, max_length=255)
    country_code: str = Field(max_length=255)
    communications: str | None = Field(default=None)
    manually_assigned_category: bool = Field(default=False)
    is_recurring: bool = Field(default=False)
    is_advance_shared_account: bool = Field(default=False)
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    is_manually_reviewed: bool = Field(default=False)

    # Foreign keys
    bank_account_id: str = Field(foreign_key="bankaccount.account_number")
    counterparty_id: str = Field(foreign_key="counterparty.name")
    category_id: int | None = Field(default=None, foreign_key="category.id")

    # Relationships
    bank_account: Optional["BankAccount"] = Relationship(
        back_populates="transactions",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    counterparty: Optional["Counterparty"] = Relationship(
        back_populates="transactions",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    category: Optional["Category"] = Relationship(
        back_populates="transactions",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def __str__(self) -> str:
        return self.transaction_id

    def has_category(self) -> bool:
        """Check if transaction has an assigned category."""
        return self.category_id is not None

    def get_transaction_type(self) -> TransactionTypeEnum:
        """Determine transaction type based on amount."""
        if self.amount >= 0.0:
            return TransactionTypeEnum.REVENUE
        return TransactionTypeEnum.EXPENSES

    def to_json_str(self) -> str:
        """Convert transaction to JSON string."""
        return json.dumps(
            {
                "transaction_id": self.transaction_id,
                "booking_date": str(self.booking_date),
                "amount": self.amount,
                "currency": self.currency,
            }
        )

    @staticmethod
    def create_transaction_id(transaction_number: str, bank_account_number: str) -> str:
        """Create a unique transaction ID from transaction number and bank account."""
        raw_value = "_".join([transaction_number, str(hash(bank_account_number))])
        return hashlib.sha256(raw_value.encode()).hexdigest()[:64]

