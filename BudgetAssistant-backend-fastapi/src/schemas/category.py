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

    @classmethod
    def from_tree(cls, tree: CategoryTreeRead) -> "CategoryIndex":
        id_to_category_index: dict[int, CategoryRead] = {}
        qualified_name_to_category_index: dict[str, CategoryRead] = {}
        qualified_name_to_id_index: dict[str, int] = {}

        def populate_indexes(category: CategoryRead) -> None:
            """Recursively populate indexes from a category and its children."""
            id_to_category_index[category.id] = category
            qualified_name_to_category_index[category.qualified_name] = category
            qualified_name_to_id_index[category.qualified_name] = category.id

            for child in category.children:
                populate_indexes(child)

        # Start from the root if it exists
        if tree.root is not None:
            populate_indexes(tree.root)

        return cls(
            id_to_category_index=id_to_category_index,
            qualified_name_to_category_index=qualified_name_to_category_index,
            qualified_name_to_id_index=qualified_name_to_id_index,
        )


# Required for recursive type reference
CategoryRead.model_rebuild()
