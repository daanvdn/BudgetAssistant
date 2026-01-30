"""User SQLModel database model."""

from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship, SQLModel

from .associations import UserBankAccountLink, UserCounterpartyLink, UserRuleSetLink

if TYPE_CHECKING:
    from .bank_account import BankAccount
    from .counterparty import Counterparty
    from .rule_set_wrapper import RuleSetWrapper


class User(SQLModel, table=True):
    """User model for authentication and ownership."""

    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=150)
    email: str = Field(max_length=255)
    password_hash: str = Field(max_length=255)
    first_name: str = Field(default="", max_length=150)
    last_name: str = Field(default="", max_length=150)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    # Relationships
    bank_accounts: List["BankAccount"] = Relationship(
        back_populates="users",
        link_model=UserBankAccountLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    counterparties: List["Counterparty"] = Relationship(
        back_populates="users",
        link_model=UserCounterpartyLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    rule_sets: List["RuleSetWrapper"] = Relationship(
        back_populates="users",
        link_model=UserRuleSetLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def __str__(self) -> str:
        return self.username
