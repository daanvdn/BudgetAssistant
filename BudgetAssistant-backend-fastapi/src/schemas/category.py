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


# Required for recursive type reference
CategoryRead.model_rebuild()
