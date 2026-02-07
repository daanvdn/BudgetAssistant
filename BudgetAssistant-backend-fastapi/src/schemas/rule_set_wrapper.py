"""Pydantic schemas for RuleSetWrapper API operations."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RuleSetWrapperCreate(BaseModel):
    """Schema for creating a new rule set wrapper."""

    category_id: int
    rule_set: Dict[str, Any]
    user_ids: List[int] = []


class RuleSetWrapperRead(BaseModel):
    """Schema for reading rule set wrapper data (response)."""

    id: int
    category_id: int | None = None
    rule_set: Dict[str, Any]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_rule_set(cls, obj) -> "RuleSetWrapperRead":
        """Create from ORM object, parsing the JSON rule set."""
        return cls(
            id=obj.id,
            category_id=obj.category_id,
            rule_set=obj.get_rule_set_as_dict(),
        )


class RuleSetWrapperBatchRead(BaseModel):
    expenses_rules: dict[str, RuleSetWrapperRead] = Field(
        ..., description="a mapping of qualified name to rule set wrapper"
    )
    revenue_rules: dict[str, RuleSetWrapperRead] = Field(
        ..., description="a mapping of qualified name to rule set wrapper"
    )


class RuleSetWrapperUpdate(BaseModel):
    """Schema for updating rule set wrapper data."""

    rule_set: Dict[str, Any] | None = None
    category_id: int | None = None
