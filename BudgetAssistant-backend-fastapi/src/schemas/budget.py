"""Pydantic schemas for Budget API operations."""

from typing import List, Optional

from pydantic import BaseModel


class BudgetTreeNodeCreate(BaseModel):
    """Schema for creating a new budget tree node."""

    amount: int = 0
    category_id: int | None = None
    parent_id: int | None = None


class BudgetTreeNodeRead(BaseModel):
    """Schema for reading budget tree node data (response)."""

    id: int
    amount: int
    category_id: int | None = None
    parent_id: int | None = None
    name: str = ""  # Category name
    qualified_name: str = ""  # Category qualified name
    children: List["BudgetTreeNodeRead"] = []

    model_config = {"from_attributes": True}


class BudgetTreeNodeUpdate(BaseModel):
    """Schema for updating budget tree node data."""

    amount: int | None = None
    category_id: int | None = None


class BudgetTreeCreate(BaseModel):
    """Schema for creating a new budget tree."""

    bank_account_id: str
    root_id: int | None = None


class BudgetTreeRead(BaseModel):
    """Schema for reading budget tree data (response)."""

    bank_account_id: str
    number_of_descendants: int
    root_id: int | None = None
    root: Optional[BudgetTreeNodeRead] = None

    model_config = {"from_attributes": True}


# Required for recursive type reference
BudgetTreeNodeRead.model_rebuild()

