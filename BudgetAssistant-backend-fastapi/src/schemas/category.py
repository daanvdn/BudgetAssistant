"""Pydantic schemas for Category API operations."""

from typing import List, Optional

from pydantic import BaseModel

from common.enums import TransactionTypeEnum


class CategoryRead(BaseModel):
    """Schema for reading category data (response)."""

    id: int
    name: str
    qualified_name: str
    is_root: bool
    type: TransactionTypeEnum
    parent_id: int | None = None
    children: List["CategoryRead"] = []

    model_config = {"from_attributes": True}


class CategoryTreeRead(BaseModel):
    """Schema for reading category tree data (response)."""

    id: int
    type: TransactionTypeEnum
    root: Optional[CategoryRead] = None

    model_config = {"from_attributes": True}


class CategoryIndex(BaseModel):
    id_to_category_index: dict[int, CategoryRead]
    qualified_name_to_category_index: dict[str, CategoryRead]
    qualified_name_to_id_index: dict[str, int]
    id_to_name_index: dict[int, str]
    expenses_root_children: List[CategoryRead] = []
    revenue_root_children: List[CategoryRead] = []

    @classmethod
    def from_tree(cls, tree: CategoryTreeRead) -> "CategoryIndex":
        id_to_category_index: dict[int, CategoryRead] = {}
        qualified_name_to_category_index: dict[str, CategoryRead] = {}
        qualified_name_to_id_index: dict[str, int] = {}
        id_to_name_index: dict[int, str] = {}

        def populate_indexes(category: CategoryRead) -> None:
            """Recursively populate indexes from a category and its children."""
            id_to_category_index[category.id] = category
            qualified_name_to_category_index[category.qualified_name] = category
            qualified_name_to_id_index[category.qualified_name] = category.id
            id_to_name_index[category.id] = category.name

            for child in category.children:
                populate_indexes(child)

        # Start from the root if it exists
        if tree.root is not None:
            populate_indexes(tree.root)

        # Get root children based on transaction type
        root_children: List[CategoryRead] = []
        if tree.root is not None:
            root_children = tree.root.children

        expenses_root_children: List[CategoryRead] = []
        revenue_root_children: List[CategoryRead] = []
        if tree.type == TransactionTypeEnum.EXPENSES:
            expenses_root_children = root_children
        elif tree.type == TransactionTypeEnum.REVENUE:
            revenue_root_children = root_children

        return cls(
            id_to_category_index=id_to_category_index,
            qualified_name_to_category_index=qualified_name_to_category_index,
            qualified_name_to_id_index=qualified_name_to_id_index,
            id_to_name_index=id_to_name_index,
            expenses_root_children=expenses_root_children,
            revenue_root_children=revenue_root_children,
        )

    def merge(self, other: "CategoryIndex") -> "CategoryIndex":
        """Merge another CategoryIndex into this one, with the other taking precedence."""
        merged_id_to_category_index = {**self.id_to_category_index, **other.id_to_category_index}
        merged_qualified_name_to_category_index = {
            **self.qualified_name_to_category_index,
            **other.qualified_name_to_category_index,
        }
        merged_qualified_name_to_id_index = {
            **self.qualified_name_to_id_index,
            **other.qualified_name_to_id_index,
        }
        merged_id_to_name_index = {
            **self.id_to_name_index,
            **other.id_to_name_index,
        }

        # Merge root children, filtering out dummy categories from revenue
        merged_expenses_root_children = (
            self.expenses_root_children if self.expenses_root_children else other.expenses_root_children
        )
        merged_revenue_root_children = (
            self.revenue_root_children if self.revenue_root_children else other.revenue_root_children
        )

        return CategoryIndex(
            id_to_category_index=merged_id_to_category_index,
            qualified_name_to_category_index=merged_qualified_name_to_category_index,
            qualified_name_to_id_index=merged_qualified_name_to_id_index,
            id_to_name_index=merged_id_to_name_index,
            expenses_root_children=merged_expenses_root_children,
            revenue_root_children=merged_revenue_root_children,
        )


# Required for recursive type reference
CategoryRead.model_rebuild()
CategoryTreeRead.model_rebuild()
CategoryIndex.model_rebuild()
