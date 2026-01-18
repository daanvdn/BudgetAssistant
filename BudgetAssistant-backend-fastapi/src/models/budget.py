"""Budget tree SQLModel database models."""

from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .bank_account import BankAccount
    from .category import Category


class BudgetTreeNode(SQLModel, table=True):
    """Budget tree node model representing a node in the budget hierarchy."""

    __tablename__ = "budgettreenode"

    id: int | None = Field(default=None, primary_key=True)
    amount: int = Field(default=0)

    # Self-referential foreign key for parent-child relationship
    parent_id: int | None = Field(default=None, foreign_key="budgettreenode.id")

    # Foreign key to category
    category_id: int | None = Field(default=None, foreign_key="category.id")

    # Relationships
    parent: Optional["BudgetTreeNode"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "BudgetTreeNode.id"},
    )
    children: List["BudgetTreeNode"] = Relationship(back_populates="parent")
    category: Optional["Category"] = Relationship(back_populates="budget_tree_nodes")

    # Back reference to budget tree (when this node is the root)
    budget_tree: Optional["BudgetTree"] = Relationship(
        back_populates="root",
        sa_relationship_kwargs={"uselist": False},
    )

    def __str__(self) -> str:
        category_name = self.category.name if self.category else "No Category"
        return f"{category_name} - {self.amount}"

    def add_child(self, child: "BudgetTreeNode") -> None:
        """Add a child node."""
        child.parent_id = self.id
        child.parent = self

    def is_root_category(self) -> bool:
        """Check if this node's category is the root category."""
        if self.category is None:
            return False
        return self.category.name == "root"

    def parent_node_is_root(self) -> bool:
        """Check if parent node is the root category."""
        if self.parent is None or self.parent.category is None:
            return False
        return self.parent.category.name == "root"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BudgetTreeNode):
            return False
        return (
            self.id == other.id
            and self.category_id == other.category_id
            and self.amount == other.amount
        )

    def __hash__(self) -> int:
        return hash((self.id, self.category_id, self.amount))


class BudgetTree(SQLModel, table=True):
    """Budget tree model representing the budget hierarchy for a bank account."""

    __tablename__ = "budgettree"

    # Use bank account as primary key (one budget tree per account)
    bank_account_id: str = Field(
        primary_key=True,
        foreign_key="bankaccount.account_number",
    )
    number_of_descendants: int = Field(default=0)

    # Foreign key to root node
    root_id: int | None = Field(
        default=None, foreign_key="budgettreenode.id", unique=True
    )

    # Relationships
    bank_account: Optional["BankAccount"] = Relationship(
        back_populates="budget_tree",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    root: Optional["BudgetTreeNode"] = Relationship(
        back_populates="budget_tree",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def __str__(self) -> str:
        return self.bank_account_id

