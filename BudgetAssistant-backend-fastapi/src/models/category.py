"""Category and CategoryTree SQLModel database models."""

from typing import TYPE_CHECKING, ClassVar, List, Optional

from enums import TransactionTypeEnum
from sqlalchemy import Column, String
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .budget import BudgetTreeNode
    from .counterparty import Counterparty
    from .rule_set_wrapper import RuleSetWrapper
    from .transaction import Transaction


class Category(SQLModel, table=True):
    """Category model for transaction categorization."""

    __tablename__ = "category"

    # Class constants (not database columns)
    ROOT_NAME: ClassVar[str] = "root"
    NO_CATEGORY_NAME: ClassVar[str] = "NO CATEGORY"
    DUMMY_CATEGORY_NAME: ClassVar[str] = "DUMMY CATEGORY"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    qualified_name: str = Field(default="")
    is_root: bool = Field(default=False)
    type: TransactionTypeEnum = Field(sa_column=Column(String(20)))

    # Self-referential foreign key for parent-child relationship
    parent_id: int | None = Field(default=None, foreign_key="category.id")

    # Relationships
    parent: Optional["Category"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Category.id", "lazy": "selectin"},
    )
    children: List["Category"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    # Back references
    transactions: List["Transaction"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    counterparties: List["Counterparty"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    budget_tree_nodes: List["BudgetTreeNode"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    rule_set_wrapper: Optional["RuleSetWrapper"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"uselist": False, "lazy": "selectin"},
    )
    category_tree: Optional["CategoryTree"] = Relationship(
        back_populates="root",
        sa_relationship_kwargs={"uselist": False, "lazy": "selectin"},
    )

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        if not self.qualified_name:
            raise ValueError("Qualified name is not set.")
        return hash(self.qualified_name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Category):
            return False
        if not self.qualified_name:
            raise ValueError("Qualified name is not set.")
        if not other.qualified_name:
            raise ValueError("Qualified name is not set on other.")
        return self.qualified_name == other.qualified_name

    def __lt__(self, other: "Category") -> bool:
        return self.qualified_name < other.qualified_name

    def __gt__(self, other: "Category") -> bool:
        return self.qualified_name > other.qualified_name

    @staticmethod
    def no_category_object() -> "Category":
        """Return a placeholder 'no category' instance."""
        return Category(
            id=-1,
            name=Category.NO_CATEGORY_NAME,
            is_root=False,
            type=TransactionTypeEnum.BOTH,
        )

    def add_child(self, child: "Category") -> None:
        """Add a child category."""
        child.parent_id = self.id
        child.parent = self


class CategoryTree(SQLModel, table=True):
    """Category tree model representing a hierarchy of categories."""

    __tablename__ = "categorytree"

    id: int | None = Field(default=None, primary_key=True)
    type: TransactionTypeEnum = Field(sa_column=Column(String(20)))

    # Foreign key to root category
    root_id: int | None = Field(default=None, foreign_key="category.id", unique=True)

    # Relationship
    root: Optional["Category"] = Relationship(
        back_populates="category_tree",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def __str__(self) -> str:
        root_name = self.root.name if self.root else "None"
        return f"{self.type} - {root_name}"
