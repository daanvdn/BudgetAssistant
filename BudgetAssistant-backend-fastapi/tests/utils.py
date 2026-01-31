"""Test utility functions for database model testing."""

import random
from datetime import datetime
from typing import Any, Optional, Tuple, Type

from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from enums import TransactionTypeEnum
from models.rules import (
    ALL_OF,
    ANY_OF,
    CONTAINS_CAT_OP,
    CONTAINS_STRING_OP,
    FieldType,
    MATCH_CAT_OP,
    MATCH_STRING_OP,
    MATCH_NUMBER_OP,
    Rule,
    RuleMatchType,
    RuleOperator,
    RuleSet,
)
from schemas.analysis import (
    CategoryAmount,
    CategoryDetailsForPeriodResult,
    ExpensesAndRevenueForPeriod,
    PeriodCategoryBreakdown,
    RevenueAndExpensesPerPeriodAndCategory,
)

# Initialize Faker for generating fake data
fake = Faker()


# =============================================================================
# Rule Factories (ported from Django's utils.py)
# =============================================================================


class RuleOperatorFactory:
    """Factory for creating random RuleOperator instances."""

    @classmethod
    def build(cls) -> RuleOperator:
        """Build a random RuleOperator."""
        return random.choice(
            [
                CONTAINS_STRING_OP,
                MATCH_STRING_OP,
                CONTAINS_CAT_OP,
                MATCH_CAT_OP,
                MATCH_NUMBER_OP,
            ]
        )


class RuleMatchTypeFactory:
    """Factory for creating random RuleMatchType instances."""

    @classmethod
    def build(cls) -> RuleMatchType:
        """Build a random RuleMatchType that is either 'any of' or 'all of'."""
        return random.choice([ANY_OF, ALL_OF])


class StringRuleFactory:
    """Factory for creating string Rule instances."""

    VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS = [
        (ANY_OF, MATCH_STRING_OP),
        (ANY_OF, CONTAINS_STRING_OP),
        (ALL_OF, CONTAINS_STRING_OP),
        (ANY_OF, MATCH_CAT_OP),
        (ANY_OF, CONTAINS_CAT_OP),
        (ALL_OF, CONTAINS_CAT_OP),
    ]
    VALID_FIELDS = [
        "communications",
        "transaction",
        "currency",
        "country_code",
        "counterparty.name",
        "counterparty.account_number",
        "bank_account.account_number",
    ]

    @classmethod
    def field_type(cls) -> FieldType:
        """Return the field type."""
        return "string"

    @classmethod
    def field(cls):
        """Generate a random list of fields."""
        return random.sample(cls.VALID_FIELDS, random.randint(1, len(cls.VALID_FIELDS)))

    @classmethod
    def type_(cls) -> TransactionTypeEnum:
        """Generate a random transaction type."""
        return random.choice(
            [TransactionTypeEnum.EXPENSES, TransactionTypeEnum.REVENUE]
        )

    @classmethod
    def get_value_match_type_and_operator(
        cls,
        operator: Optional[RuleOperator],
        value_match_type: Optional[RuleMatchType],
    ) -> Tuple[RuleMatchType, RuleOperator]:
        """Get a valid combination of value_match_type and operator."""
        if value_match_type:
            if operator:
                # Check if the tuple is in the valid combinations
                if (
                    value_match_type,
                    operator,
                ) in cls.VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS:
                    return value_match_type, operator
                else:
                    raise ValueError(
                        f"Operator {operator} is not compatible with value match type {value_match_type}"
                    )
            else:
                # Random tuple with matching value_match_type
                return random.choice(
                    [
                        t
                        for t in cls.VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS
                        if t[0] == value_match_type
                    ]
                )
        else:
            if not operator:
                # Random valid tuple
                return random.choice(cls.VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS)
            else:
                # Random tuple with matching operator
                return random.choice(
                    [
                        t
                        for t in cls.VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS
                        if t[1] == operator
                    ]
                )

    @classmethod
    def build(cls, **kwargs: Any) -> Rule:
        """Build a Rule instance with the given overrides."""
        field = kwargs.get("field", cls.field())
        value = kwargs.get("value", fake.words(nb=random.randint(1, 10)))
        type_ = kwargs.get("type", cls.type_())
        value_match_type, operator = cls.get_value_match_type_and_operator(
            kwargs.get("operator", None),
            kwargs.get("value_match_type", None),
        )
        field_type = cls.field_type()

        return Rule(
            field=field,
            field_type=field_type,
            value=value,
            value_match_type=value_match_type,
            operator=operator,
            clazz="Rule",
            type=type_,
        )


class RuleSetFactory:
    """Factory for creating RuleSet instances."""

    max_depth = 3
    current_depth = 0

    @classmethod
    def rules(cls) -> list:
        """Generate a list of Rule or RuleSet instances."""
        result = []
        for _ in range(5):
            generate_rule = random.choice([True, False])
            if generate_rule or cls.current_depth >= cls.max_depth:
                result.append(StringRuleFactory.build())
            else:
                cls.current_depth += 1
                result.append(cls.build())
                cls.current_depth -= 1
        return result

    @classmethod
    def build(cls, **kwargs: Any) -> RuleSet:
        """Build a RuleSet instance."""
        condition = kwargs.get("condition", random.choice(["AND", "OR"]))
        rules = kwargs.get("rules", cls.rules())
        is_child = kwargs.get("is_child", random.choice([True, False]))
        type_ = kwargs.get(
            "type",
            random.choice([TransactionTypeEnum.EXPENSES, TransactionTypeEnum.REVENUE]),
        )

        return RuleSet(
            condition=condition,
            rules=rules,
            is_child=is_child,
            clazz="RuleSet",
            type=type_,
        )


def create_random_rule_set() -> RuleSet:
    """Create a random RuleSet with nested rules."""

    def _create_rule_set() -> RuleSet:
        rule_set = RuleSetFactory.build(rules=[])
        rule_set.rules = [StringRuleFactory.build() for _ in range(5)]
        return rule_set

    rule_set = _create_rule_set()
    rule_set.rules.append(_create_rule_set())
    return rule_set


def create_random_rule_set_deep(depth: int = 3) -> RuleSet:
    """Create a deeply nested random RuleSet.

    Args:
        depth: The depth of nesting (default 3).

    Returns:
        A deeply nested RuleSet.
    """

    def _create_rule() -> Rule:
        return StringRuleFactory.build()

    def _create_rule_set() -> RuleSet:
        rule_set = RuleSetFactory.build(rules=[])
        rule_set.rules = [_create_rule() for _ in range(5)]
        return rule_set

    def _create_rule_set_recursive(current_depth: int) -> RuleSet:
        if current_depth == depth:
            return _create_rule_set()
        rule_set = RuleSetFactory.build(rules=[])
        rule_set.rules = [
            _create_rule_set_recursive(current_depth + 1) for _ in range(5)
        ]
        return rule_set

    return _create_rule_set_recursive(0)


# =============================================================================
# Analysis Schema Factories
# =============================================================================


class CategoryAmountFactory(ModelFactory):
    """Factory for CategoryAmount schema."""

    __model__ = CategoryAmount

    @classmethod
    def category_qualified_name(cls) -> str:
        """Generate a qualified category name."""
        return f"{fake.word()}_{fake.random_element(['EXPENSES', 'REVENUE'])}"

    @classmethod
    def category_name(cls) -> str:
        """Generate a category name."""
        return fake.word()

    @classmethod
    def amount(cls) -> float:
        """Generate an amount."""
        return round(fake.pyfloat(min_value=-1000, max_value=1000), 2)


class ExpensesAndRevenueForPeriodFactory(ModelFactory):
    """Factory for ExpensesAndRevenueForPeriod schema."""

    __model__ = ExpensesAndRevenueForPeriod

    @classmethod
    def period(cls) -> str:
        """Generate a period string."""
        return f"{fake.random_int(1, 12):02d}/{fake.random_int(2020, 2025)}"

    @classmethod
    def expenses(cls) -> float:
        """Generate expenses (negative value)."""
        return -abs(round(fake.pyfloat(min_value=0, max_value=1000), 2))

    @classmethod
    def revenue(cls) -> float:
        """Generate revenue (positive value)."""
        return abs(round(fake.pyfloat(min_value=0, max_value=1000), 2))

    @classmethod
    def start_date(cls) -> datetime:
        """Generate start date."""
        return fake.date_time_this_decade()

    @classmethod
    def end_date(cls) -> datetime:
        """Generate end date."""
        return fake.date_time_this_decade()


class PeriodCategoryBreakdownFactory(ModelFactory):
    """Factory for PeriodCategoryBreakdown schema."""

    __model__ = PeriodCategoryBreakdown

    @classmethod
    def period(cls) -> str:
        """Generate a period string."""
        return f"{fake.random_int(1, 12):02d}/{fake.random_int(2020, 2025)}"

    @classmethod
    def start_date(cls) -> datetime:
        """Generate start date."""
        return fake.date_time_this_decade()

    @classmethod
    def end_date(cls) -> datetime:
        """Generate end date."""
        return fake.date_time_this_decade()

    @classmethod
    def categories(cls) -> list:
        """Generate a list of CategoryAmount instances."""
        return CategoryAmountFactory.batch(fake.random_int(1, 5))

    @classmethod
    def total(cls) -> float:
        """Generate total amount."""
        return round(fake.pyfloat(min_value=-1000, max_value=1000), 2)


class RevenueAndExpensesPerPeriodAndCategoryFactory(ModelFactory):
    """Factory for RevenueAndExpensesPerPeriodAndCategory schema."""

    __model__ = RevenueAndExpensesPerPeriodAndCategory

    @classmethod
    def periods(cls) -> list:
        """Generate a list of PeriodCategoryBreakdown instances."""
        return PeriodCategoryBreakdownFactory.batch(fake.random_int(1, 5))

    @classmethod
    def all_categories(cls) -> list:
        """Generate a list of category names."""
        return [
            f"{fake.word()}_{fake.random_element(['EXPENSES', 'REVENUE'])}"
            for _ in range(fake.random_int(1, 5))
        ]

    @classmethod
    def transaction_type(cls) -> TransactionTypeEnum:
        """Generate a transaction type."""
        return fake.random_element(
            [TransactionTypeEnum.EXPENSES, TransactionTypeEnum.REVENUE]
        )


class CategoryDetailsForPeriodResultFactory(ModelFactory):
    """Factory for CategoryDetailsForPeriodResult schema."""

    __model__ = CategoryDetailsForPeriodResult

    @classmethod
    def category_qualified_name(cls) -> str:
        """Generate a qualified category name."""
        return f"{fake.word()}_{fake.random_element(['EXPENSES', 'REVENUE'])}"

    @classmethod
    def category_name(cls) -> str:
        """Generate a category name."""
        return fake.word()

    @classmethod
    def amount(cls) -> float:
        """Generate an amount."""
        return round(fake.pyfloat(min_value=-1000, max_value=1000), 2)

    @classmethod
    def transaction_count(cls) -> int:
        """Generate transaction count."""
        return fake.random_int(0, 100)

    @classmethod
    def percentage(cls) -> float:
        """Generate percentage."""
        return round(fake.pyfloat(min_value=0, max_value=100), 2)


async def assert_persisted(
    session: AsyncSession,
    model_class: Type[SQLModel],
    pk_field: str,
    pk_value: Any,
    expected: dict[str, Any],
) -> SQLModel:
    """Re-query the database and verify that the persisted data matches expected values.

    Args:
        session: The async database session.
        model_class: The SQLModel class to query.
        pk_field: The name of the primary key field.
        pk_value: The value of the primary key to query.
        expected: A dictionary of field names to expected values.

    Returns:
        The re-queried model instance.

    Raises:
        AssertionError: If the model is not found or field values don't match.
    """
    session.expire_all()
    stmt = select(model_class).where(getattr(model_class, pk_field) == pk_value)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    assert instance is not None, (
        f"{model_class.__name__} with {pk_field}={pk_value} not found in database"
    )

    for field, expected_value in expected.items():
        actual_value = getattr(instance, field)
        assert actual_value == expected_value, (
            f"Field '{field}' mismatch: expected {expected_value!r}, got {actual_value!r}"
        )

    return instance
