"""RuleSetWrapper SQLModel database model."""

import json
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from .associations import UserRuleSetLink

if TYPE_CHECKING:
    from .category import Category
    from .user import User


class RuleSetWrapper(SQLModel, table=True):
    """Wrapper model for storing rule sets as JSON."""

    __tablename__ = "rulesetwrapper"

    id: int | None = Field(default=None, primary_key=True)
    rule_set_json: str = Field(default="{}")  # Store rule set as JSON string

    # Foreign key to category (one-to-one)
    category_id: int | None = Field(
        default=None, foreign_key="category.id", unique=True
    )

    # Relationships
    category: Optional["Category"] = Relationship(
        back_populates="rule_set_wrapper",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    users: List["User"] = Relationship(
        back_populates="rule_sets",
        link_model=UserRuleSetLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def get_rule_set_dict(self) -> dict:
        """Get the rule set as a dictionary."""
        return json.loads(self.rule_set_json) if self.rule_set_json else {}

    def set_rule_set_dict(self, rule_set: dict) -> None:
        """Set the rule set from a dictionary."""
        self.rule_set_json = json.dumps(rule_set)

