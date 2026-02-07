"""RuleSetWrapper SQLModel database model."""

import json
from logging import Logger
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from common.logging_utils import LoggerFactory

from .associations import UserRuleSetLink

if TYPE_CHECKING:
    from .category import Category
    from .rules import RuleSet
    from .user import User


class RuleSetWrapper(SQLModel, table=True):
    """Wrapper model for storing rule sets as JSON."""

    # ClassVar tells Pydantic this is a class variable, not a model field
    logger: ClassVar[Logger]

    __tablename__ = "rulesetwrapper"

    id: int | None = Field(default=None, primary_key=True)
    rule_set_json: str = Field(default="{}")  # Store rule set as JSON string

    # Foreign key to category (one-to-one)
    category_id: int | None = Field(default=None, foreign_key="category.id", unique=True)

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

    def get_rule_set(self) -> Optional["RuleSet"]:
        """Get the rule set as a strongly-typed RuleSet object.

        Returns:
            A RuleSet object if the JSON is valid and non-empty, None otherwise.
        """
        from .rules import RuleSet

        if not self.rule_set_json or self.rule_set_json == "{}":
            return None

        try:
            rule_set_dict = json.loads(self.rule_set_json)
            if not rule_set_dict:
                return None
            return RuleSet.model_validate(rule_set_dict)
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(
                f"Invalid JSON for rule set wrapper with id {self.id}: {self.rule_set_json}", exc_info=True
            )
            raise e

    def set_rule_set(self, rule_set: "RuleSet") -> None:
        """Set the rule set from a RuleSet object.

        Args:
            rule_set: The RuleSet object to store.
        """
        self.rule_set_json = json.dumps(rule_set.model_dump())

    def set_rule_set_from_dict(self, rule_set_dict: Dict[str, Any]) -> None:
        """Set the rule set from a dictionary (for API compatibility).

        Args:
            rule_set_dict: The rule set as a dictionary.
        """
        self.rule_set_json = json.dumps(rule_set_dict)

    def get_rule_set_as_dict(self) -> Dict[str, Any]:
        """Get the rule set as a dictionary (for API responses).

        Returns:
            The rule set as a dictionary, or empty dict if not set.
        """
        if not self.rule_set_json:
            return {}
        try:
            return json.loads(self.rule_set_json)
        except json.JSONDecodeError as e:
            self.logger.error(
                f"Invalid JSON for rule set wrapper with id {self.id}: {self.rule_set_json}", exc_info=True
            )
            raise e


# Initialize the class-level logger after class definition
RuleSetWrapper.logger = LoggerFactory.for_class(RuleSetWrapper)
