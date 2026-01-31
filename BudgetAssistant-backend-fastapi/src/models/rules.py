"""Rule models for transaction categorization.

This module contains Pydantic/dataclass equivalents of Django's Rule classes
for evaluating categorization rules.
"""

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, List, Literal, Union

from pydantic import BaseModel, field_validator, model_validator

from enums import TransactionTypeEnum

if TYPE_CHECKING:
    from models.transaction import Transaction

# Type aliases matching Django implementation
OperatorName = Literal["contains", "exact match", "fuzzy match"]
FieldType = Literal["number", "string", "categorical"]
MatchTypeOptions = Literal["any of", "all of"]
Condition = Literal["AND", "OR"]
Clazz = Literal["Rule", "RuleSet"]
TransactionField = Literal[
    "communications",
    "transaction",
    "currency",
    "country_code",
    "counterparty.name",
    "counterparty.account_number",
    "bank_account.account_number",
    "amount",
]


class RuleMatchType(BaseModel):
    """Model for rule match type (any of / all of)."""

    name: MatchTypeOptions
    value: MatchTypeOptions

    @staticmethod
    def from_name(name: MatchTypeOptions) -> "RuleMatchType":
        """Create RuleMatchType from name."""
        if name == "any of":
            return RuleMatchType(name=name, value="any of")
        elif name == "all of":
            return RuleMatchType(name=name, value="all of")
        else:
            raise ValueError(f"Invalid name: {name}")

    def __hash__(self) -> int:
        return hash((self.name, self.value))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RuleMatchType):
            return False
        return self.name == other.name and self.value == other.value


# Singleton instances for match types
ANY_OF = RuleMatchType.from_name("any of")
ALL_OF = RuleMatchType.from_name("all of")

RuleMatchTypes = Union[RuleMatchType, RuleMatchType]  # Type hint for ANY_OF or ALL_OF


class RuleOperator(BaseModel):
    """Model for rule operator (contains, exact match, etc.)."""

    name: OperatorName
    value: str
    type: FieldType

    @staticmethod
    def create(name: OperatorName, type_: FieldType) -> "RuleOperator":
        """Create a RuleOperator with name as value."""
        return RuleOperator(name=name, value=name, type=type_)

    def __hash__(self) -> int:
        return hash((self.name, self.value, self.type))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RuleOperator):
            return False
        return (
            self.name == other.name
            and self.value == other.value
            and self.type == other.type
        )


# Singleton instances for operators
CONTAINS_STRING_OP = RuleOperator.create("contains", "string")
MATCH_STRING_OP = RuleOperator.create("exact match", "string")
CONTAINS_CAT_OP = RuleOperator.create("contains", "categorical")
MATCH_CAT_OP = RuleOperator.create("exact match", "categorical")
MATCH_NUMBER_OP = RuleOperator.create("exact match", "number")

RuleOperatorType = Union[
    RuleOperator, RuleOperator, RuleOperator, RuleOperator, RuleOperator
]


class RuleIF(ABC):
    """Abstract base class for rules."""

    @abstractmethod
    def get_clazz(self) -> str:
        """Get the class type of the rule."""
        pass

    @abstractmethod
    def evaluate(self, transaction: "Transaction") -> bool:
        """Evaluate the rule against a transaction."""
        pass

    @abstractmethod
    def set_type(self, type_: TransactionTypeEnum) -> None:
        """Set the transaction type for this rule."""
        pass


class Rule(BaseModel, RuleIF):
    """Model for a single categorization rule."""

    FIELD_TYPE_CHOICES: ClassVar = [
        ("number", "number"),
        ("string", "string"),
        ("categorical", "categorical"),
    ]

    MATCH_TYPE_CHOICES: ClassVar = [
        ("any of", "any of"),
        ("all of", "all of"),
    ]

    field: List[TransactionField]
    field_type: FieldType
    value: List[Any]
    value_match_type: RuleMatchType
    operator: RuleOperator
    clazz: Clazz = "Rule"
    type: TransactionTypeEnum

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def validate_rule(self) -> "Rule":
        """Validate rule constraints."""
        # Check all field values contain at most 1 period
        if not all(f.count(".") <= 1 for f in self.field):
            raise ValueError("Field must contain at most one period")

        # Validate value types based on field_type
        if self.field_type == "number" and not all(
            isinstance(val, (int, float)) for val in self.value
        ):
            raise ValueError("All values must be numbers if the field_type is 'number'")

        if self.field_type in ["string", "categorical"] and not all(
            isinstance(val, str) for val in self.value
        ):
            raise ValueError(
                "All values must be strings if the field_type is 'string' or 'categorical'"
            )

        # Validate operator based on field_type
        if self.field_type == "number" and self.operator != MATCH_NUMBER_OP:
            raise ValueError("Invalid operator for number field_type")

        if self.field_type in ["string", "categorical"] and self.operator not in [
            CONTAINS_STRING_OP,
            MATCH_STRING_OP,
            CONTAINS_CAT_OP,
            MATCH_CAT_OP,
        ]:
            raise ValueError(
                f"Encountered {self.operator}: Invalid operator for string or categorical field_type!"
            )

        # Validate match type for exact match operators
        if (
            self.operator in [MATCH_STRING_OP, MATCH_CAT_OP]
            and self.value_match_type == ALL_OF
        ):
            raise ValueError(
                "Value match type must be 'any of' if operator is 'exact match'"
            )

        return self

    def _all_match(self, string_values_to_match: List[str], actual_value: str) -> bool:
        """Check if all values match using regex."""
        for string_value in string_values_to_match:
            if not re.search(
                string_value.replace(" ", "\\s*"), actual_value, re.IGNORECASE
            ):
                return False
        return True

    def _any_match(self, string_values_to_match: List[str], actual_value: str) -> bool:
        """Check if any value matches using regex."""
        for string_value in string_values_to_match:
            if re.search(
                string_value.replace(" ", "\\s*"), actual_value, re.IGNORECASE
            ):
                return True
        return False

    def evaluate_string(
        self, actual_value: str, string_values_to_match: List[str]
    ) -> bool:
        """Evaluate string field against rule values."""
        if self.operator == CONTAINS_STRING_OP:
            if self.value_match_type == ANY_OF:
                return self._any_match(string_values_to_match, actual_value)
            elif self.value_match_type == ALL_OF:
                return self._all_match(string_values_to_match, actual_value)

        elif self.operator == MATCH_STRING_OP:
            if self.value_match_type == ANY_OF:
                return self._any_match(string_values_to_match, actual_value)
            elif self.value_match_type == ALL_OF:
                return self._all_match(string_values_to_match, actual_value)
        else:
            raise ValueError(f"Unsupported operator {self.operator}")
        return False

    def _get_field_value(
        self, transaction: "Transaction", field_name: TransactionField
    ) -> Any:
        """Get field value from transaction, supporting nested fields."""
        num_period = field_name.count(".")
        if num_period == 0:
            return getattr(transaction, field_name, None)
        elif num_period == 1:
            first_part, second_part = field_name.split(".")
            first_part_obj = getattr(transaction, first_part, None)
            if first_part_obj is None:
                return None
            return getattr(first_part_obj, second_part, None)
        else:
            raise ValueError("Field cannot have more than 1 '.'")

    def evaluate_field(
        self, transaction: "Transaction", field_name: TransactionField
    ) -> bool:
        """Evaluate a single field against the rule."""
        actual_field_value = self._get_field_value(transaction, field_name)
        if actual_field_value is None:
            return False

        if self.field_type == "number":
            if not isinstance(actual_field_value, (int, float)):
                raise ValueError(f"Field value is not a number: {actual_field_value}")
            if not all(isinstance(val, (int, float)) for val in self.value):
                raise ValueError("All values must be numbers")
            # Implement number evaluation logic here
            raise NotImplementedError("Number evaluation not implemented")

        elif self.field_type in ["string", "categorical"]:
            if not isinstance(actual_field_value, str):
                raise ValueError(f"Field value is not a string: {actual_field_value}")
            return self.evaluate_string(actual_field_value, self.value)

        return False

    def evaluate(self, transaction: "Transaction") -> bool:
        """Evaluate the rule against a transaction."""
        return any(self.evaluate_field(transaction, f) for f in self.field)

    def set_type(self, type_: TransactionTypeEnum) -> None:
        """Set the transaction type for this rule."""
        self.type = type_

    def get_clazz(self) -> str:
        """Get the class type of the rule."""
        return self.clazz


class RuleSet(BaseModel, RuleIF):
    """Model for a set of rules with AND/OR conditions."""

    condition: Condition
    rules: List[Union[Rule, "RuleSet"]]
    is_child: bool
    clazz: Clazz = "RuleSet"
    type: TransactionTypeEnum

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("type", mode="before")
    @classmethod
    def convert_type(cls, v: Any) -> TransactionTypeEnum:
        """Convert string type to TransactionTypeEnum."""
        if isinstance(v, str):
            return TransactionTypeEnum.from_value(v)
        return v

    @field_validator("rules", mode="before")
    @classmethod
    def convert_rules(cls, v: Any) -> List[Union[Rule, "RuleSet"]]:
        """Convert dict rules to Rule/RuleSet objects."""
        if not isinstance(v, list):
            return v

        converted_rules = []
        for rule_data in v:
            if isinstance(rule_data, (Rule, RuleSet)):
                converted_rules.append(rule_data)
            elif isinstance(rule_data, dict):
                clazz = rule_data.get("clazz", "Rule")
                if clazz == "RuleSet":
                    converted_rules.append(RuleSet.model_validate(rule_data))
                else:
                    converted_rules.append(Rule.model_validate(rule_data))
            else:
                raise ValueError(f"Unsupported rule type: {type(rule_data)}")
        return converted_rules

    def evaluate(self, transaction: "Transaction") -> bool:
        """Evaluate the rule set against a transaction."""
        if not self.rules:
            return False

        if self.condition == "AND":
            return all(rule.evaluate(transaction) for rule in self.rules)
        elif self.condition == "OR":
            return any(rule.evaluate(transaction) for rule in self.rules)

        return False

    def set_type(self, type_: TransactionTypeEnum) -> None:
        """Set the transaction type for this rule set and all child rules."""
        self.type = type_
        for rule in self.rules:
            rule.set_type(type_)

    def get_clazz(self) -> str:
        """Get the class type of the rule."""
        return self.clazz

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RuleSet):
            return False
        return (
            self.condition == other.condition
            and self.rules == other.rules
            and self.is_child == other.is_child
        )


# Update forward references for recursive type
RuleSet.model_rebuild()
