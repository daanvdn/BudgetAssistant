import random
from datetime import datetime
from typing import Any, Callable, Optional, Tuple

from faker import Faker
from model_bakery import baker
from polyfactory.factories.dataclass_factory import DataclassFactory

from pybackend.analysis import DistributionByCategoryForPeriodChartData, DistributionByCategoryForPeriodTableData, \
    RevenueAndExpensesPerPeriodAndCategory
from pybackend.commons import TransactionTypeEnum
from pybackend.models import Category
from pybackend.period import Month, Period
from pybackend.rules import ALL_OF, ANY_OF, CONTAINS_CAT_OP, CONTAINS_STRING_OP, FieldType, MATCH_CAT_OP, \
    MATCH_NUMBER_OP, MATCH_STRING_OP, \
    Rule, \
    RuleMatchType, RuleMatchTypes, RuleOperator, \
    RuleSet

# instantiate a random boolean generator
random_boolean = lambda: random.choice([True, False])

def generate_random_period() -> Period:
    # random datetime
    start = datetime.now()
    end = start.replace(year=start.year + 1)
    return Month(start=start, end=end)


class RuleOperatorFactory(DataclassFactory[RuleOperator]):

    @classmethod
    def build(cls) -> RuleOperator:
        return random.choice([CONTAINS_STRING_OP,
                              MATCH_STRING_OP,
                              CONTAINS_CAT_OP,
                              MATCH_CAT_OP,
                              MATCH_NUMBER_OP])


class RuleMatchTypeFactory(DataclassFactory[RuleMatchType]):
    __model__ = RuleMatchType

    # build a random RuleMatchType that is either 'any of' or 'all of'
    @classmethod
    def build(cls) -> RuleMatchType:
        return random.choice([ANY_OF, ALL_OF])


class RuleFactory(DataclassFactory[Rule]):

    @classmethod
    def field_match_type(cls) -> RuleMatchTypes:
        return RuleMatchTypeFactory.build()

    @classmethod
    def value_match_type(cls) -> RuleMatchTypes:
        return RuleMatchTypeFactory.build()

    @classmethod
    def operator(cls) -> RuleOperator:
        return RuleOperatorFactory.build()

    @classmethod
    def clazz(cls) -> str:
        return 'Rule'

    @classmethod
    def field_type(cls) -> FieldType:
        return 'string'

# pybackend/tests/utils.py

fake = Faker()
class StringRuleFactory(RuleFactory):
    VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS = [
        (ANY_OF, MATCH_STRING_OP),
        (ANY_OF, CONTAINS_STRING_OP),
        (ALL_OF, CONTAINS_STRING_OP),
        (ANY_OF, MATCH_CAT_OP),
        (ANY_OF, CONTAINS_CAT_OP),
        (ALL_OF, CONTAINS_CAT_OP)
    ]
    VALID_FIELDS = ['communications', 'transaction', 'currency', 'country_code', 'counterparty.name',
                    'counterparty.account_number', 'bank_account.account_number']

    @classmethod
    def field_type(cls) -> FieldType:
        return 'string'

    @classmethod
    def field(cls):
        return random.sample(cls.VALID_FIELDS, random.randint(1, len(cls.VALID_FIELDS)))

    @classmethod
    def value_match_type(cls) -> RuleMatchTypes:
        if cls.operator() == MATCH_STRING_OP:
            return ANY_OF
        return RuleMatchTypeFactory.build()

    @classmethod
    def operator(cls) -> RuleOperator:
        return random.choice([MATCH_STRING_OP, CONTAINS_STRING_OP])

    @classmethod
    def type(cls) -> TransactionTypeEnum:
        return random.choice([TransactionTypeEnum.EXPENSES, TransactionTypeEnum.REVENUE])

    @classmethod
    def build(cls, factory_use_construct: bool = False,
              **kwargs: Any) -> Rule:
        field = kwargs.get('field', cls.field())
        value = kwargs.get('value', fake.words(nb=random.randint(1, 10)))
        type = kwargs.get('type', cls.type())
        value_match_type, operator = cls.get_value_match_type_and_operator(kwargs.get('operator', None),
                                                                           kwargs.get('value_match_type', None))

        field_type = cls.field_type()
        return Rule(
            field=field,
            field_type=field_type,
            value=value,
            value_match_type=value_match_type,
            operator=operator,
            clazz='Rule',
            type=type
        )

    @classmethod
    def get_value_match_type_and_operator(cls, operator: Optional[RuleOperator],
                                          value_match_type: Optional[RuleMatchTypes]) -> Tuple[
        RuleMatchTypes, RuleOperator]:
        if value_match_type:
            if operator:
                # check if the tuple (operator, value_match_type) is in the list of VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS
                if (value_match_type, operator) in cls.VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS:
                    return value_match_type, operator
                else:
                    raise ValueError(f"Operator {operator} is not compatible with value match type {value_match_type}")
            else:
                # take a random tuple from VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS where the value match type is equal to value_match_type
                return random.choice(
                    [t for t in cls.VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS if t[0] == value_match_type])
        else:
            if not operator:
                # take a random tuple from VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS
                return random.choice(cls.VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS)
            else:
                # take a random tuple from VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS where the operator is equal to operator
                return random.choice([t for t in cls.VALUE_MATCH_TYPE_OPERATOR_COMBINATIONS if t[1] == operator])


class RuleSetFactory(DataclassFactory[RuleSet]):
    max_depth = 3
    current_depth = 0

    @classmethod
    def rules(cls):
        result = []
        for i in range(5):
            generate_rule = random_boolean()
            if generate_rule or cls.current_depth >= cls.max_depth:
                result.append(StringRuleFactory.build())
            else:
                cls.current_depth += 1
                result.append(RuleSetFactory.build())
                cls.current_depth -= 1
        return result
    @classmethod
    def clazz(cls):
        return 'RuleSet'

def create_random_rule_set() -> RuleSet:
    def _create_rule_set() -> RuleSet:
        rule_set = RuleSetFactory.build()
        rule_set.rules = [StringRuleFactory.build() for _ in range(5)]
        return rule_set

    rule_set: RuleSet = _create_rule_set()
    rule_set.rules.append(_create_rule_set())
    return rule_set


class DistributionByCategoryForPeriodChartDataFactory(DataclassFactory[DistributionByCategoryForPeriodChartData]):

    @classmethod
    def get_provider_map(cls) -> dict[Any, Callable[[], Any]]:
        providers_map = super().get_provider_map()

        return {
            Period: lambda: generate_random_period(),
            Category: lambda: baker.make(Category),
            **providers_map,
        }


class DistributionByCategoryForPeriodTableDataFactory(DataclassFactory[DistributionByCategoryForPeriodTableData]):
    @classmethod
    def get_provider_map(cls) -> dict[Any, Callable[[], Any]]:
        providers_map = super().get_provider_map()
        return {
            Period: lambda: generate_random_period(),
            Category: lambda: baker.make(Category),
            **providers_map,
        }


class RevenueAndExpensesPerPeriodAndCategoryFactory(DataclassFactory[RevenueAndExpensesPerPeriodAndCategory]):
    @classmethod
    def get_provider_map(cls) -> dict[Any, Callable[[], Any]]:
        providers_map = super().get_provider_map()

        return {
            Period: lambda: generate_random_period(),
            **providers_map,
        }

    @classmethod
    def chart_data_revenue(cls):
        return DistributionByCategoryForPeriodChartDataFactory.batch(size=5)

    @classmethod
    def chart_data_expenses(cls):
        return DistributionByCategoryForPeriodChartDataFactory.batch(size=5)

    @classmethod
    def table_data_revenue(cls):
        return DistributionByCategoryForPeriodTableDataFactory.batch(size=5)

    @classmethod
    def table_data_expenses(cls):
        return DistributionByCategoryForPeriodTableDataFactory.batch(size=5)

    @classmethod
    def table_column_names_revenue(cls):
        # return 5 strings
        return ['a', 'b', 'c', 'd', 'e']

    @classmethod
    def table_column_names_expenses(cls):
        # return 5 strings
        return ['a', 'b', 'c', 'd', 'e']

