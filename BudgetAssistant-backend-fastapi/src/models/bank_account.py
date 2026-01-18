"""BankAccount SQLModel database model."""

from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from .associations import UserBankAccountLink

if TYPE_CHECKING:
    from .budget import BudgetTree
    from .transaction import Transaction
    from .user import User


class BankAccount(SQLModel, table=True):
    """Bank account model."""

    __tablename__ = "bankaccount"

    account_number: str = Field(primary_key=True, max_length=255)
    alias: str | None = Field(default=None, max_length=255)

    # Relationships
    users: List["User"] = Relationship(
        back_populates="bank_accounts",
        link_model=UserBankAccountLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    transactions: List["Transaction"] = Relationship(
        back_populates="bank_account",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    budget_tree: Optional["BudgetTree"] = Relationship(
        back_populates="bank_account",
        sa_relationship_kwargs={"uselist": False, "lazy": "selectin"},
    )

    def __str__(self) -> str:
        return self.account_number

    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "account_number": self.account_number,
            "alias": self.alias,
        }

    @staticmethod
    def normalize_account_number(account_number: str) -> str:
        """Normalize account number by removing spaces and converting to lowercase."""
        return account_number.replace(" ", "").lower()

