"""Tests for the rules module - evaluation and serialization.

Ported from Django's test_rules.py, adapting to pytest and Pydantic validation.
"""

import random
from abc import ABC, abstractmethod
from typing import List, Tuple, Union

import pytest
from faker import Faker

from common.enums import TransactionTypeEnum
from models import RuleSetWrapper
from models.rules import (
    ALL_OF,
    ANY_OF,
    CONTAINS_STRING_OP,
    EQUALS_NUMBER_OP,
    FUZZY_MATCH_STRING_OP,
    GT_NUMBER_OP,
    LTE_NUMBER_OP,
    MATCH_NUMBER_OP,
    MATCH_STRING_OP,
    NOT_EQUALS_NUMBER_OP,
    Rule,
    RuleMatchType,
    RuleOperator,
    RuleSet,
    TransactionField,
)
from tests.utils import (
    RuleSetFactory,
    StringRuleFactory,
    create_random_rule_set,
    create_random_rule_set_deep,
)

faker = Faker()


# =============================================================================
# Helper classes for preparing rules and mock transactions
# =============================================================================


class Attribute(ABC):
    """Abstract base class for setting attribute values on transactions."""

    @abstractmethod
    def is_nested_attribute(self) -> bool:
        """Check if this is a nested attribute."""
        pass

    @abstractmethod
    def set_attribute(self, target_string: str, transaction: "MockTransaction", rule: Rule) -> "MockTransaction":
        """Set the attribute value on a transaction."""
        pass

    @staticmethod
    def create(attribute_name: TransactionField) -> "Attribute":
        """Create the appropriate Attribute subclass based on the name."""
        if not isinstance(attribute_name, str):
            raise ValueError("Attribute name must be a string")
        if "." in attribute_name:
            return NestedAttribute(attribute_name)
        return SimpleAttribute(attribute_name)


class SimpleAttribute(Attribute):
    """Attribute handler for non-nested attributes."""

    def __init__(self, attribute_name: TransactionField):
        self.attribute_name = attribute_name

    def is_nested_attribute(self) -> bool:
        return False

    def set_attribute(self, target_string: str, transaction: "MockTransaction", rule: Rule) -> "MockTransaction":
        setattr(transaction, self.attribute_name, target_string)
        if rule.value:
            if not isinstance(rule.value, list):
                raise ValueError("Rule value must be a list")
        else:
            rule.value = []
        rule.value.append(target_string)
        if rule.field:
            if not isinstance(rule.field, list):
                raise ValueError("Rule field must be a list")
        else:
            rule.field = []
        rule.field.append(self.attribute_name)
        return transaction


class NestedAttribute(Attribute):
    """Attribute handler for nested attributes like 'counterparty.name'."""

    def __init__(self, attribute_name: str):
        if "." not in attribute_name:
            raise ValueError("Field must contain '.'")
        if attribute_name.count(".") > 1:
            raise ValueError("Field cannot have more than 1 '.'")
        self.attribute_name = attribute_name

    def is_nested_attribute(self) -> bool:
        return True

    def set_attribute(self, target_string: str, transaction: "MockTransaction", rule: Rule) -> "MockTransaction":
        first_part, second_part = self.attribute_name.split(".")
        first_part_obj = getattr(transaction, first_part)
        setattr(first_part_obj, second_part, target_string)
        setattr(transaction, first_part, first_part_obj)
        if rule.value:
            if not isinstance(rule.value, list):
                raise ValueError("Rule value must be a list")
            else:
                rule.value = []
        rule.value.append(target_string)
        if rule.field:
            if not isinstance(rule.field, list):
                raise ValueError("Rule field must be a list")
            else:
                rule.field = []
        rule.field.append(self.attribute_name)
        return transaction


class MockCounterparty:
    """Mock counterparty object for testing."""

    def __init__(self):
        self.name = ""
        self.account_number = ""


class MockBankAccount:
    """Mock bank account object for testing."""

    def __init__(self):
        self.account_number = ""


class MockTransaction:
    """Mock transaction object for testing rule evaluation."""

    def __init__(self):
        self.communications = ""
        self.transaction = ""
        self.currency = ""
        self.country_code = ""
        self.counterparty = MockCounterparty()
        self.bank_account = MockBankAccount()
        self.amount = 0.0


class RuleAndTransactionPreparer:
    """Prepares a rule and transaction pair for testing evaluation."""

    def __init__(self, transaction: MockTransaction, rule: Rule):
        self.rule = rule
        self.operator = rule.operator
        self.fields = rule.field
        self.value_match_type = rule.value_match_type
        self.target_strings = rule.value
        self.transaction = transaction

    def _select_fields(self) -> Union[TransactionField, List[TransactionField]]:
        return random.choice(self.fields)

    def _select_target_strings(self) -> Union[str, List[str]]:
        if self.value_match_type == ALL_OF:
            return self.target_strings.copy()
        elif self.value_match_type == ANY_OF:
            return random.choice(self.target_strings)
        else:
            raise ValueError("Value match type not supported")

    def _create_fake_text(self, selected_target_string: str) -> str:
        random.seed(0)

        if self.operator == CONTAINS_STRING_OP:
            fake_text = " ".join(faker.words(nb=random.randint(1, 10)))
            position = random.randint(0, len(fake_text))
            return fake_text[:position] + selected_target_string + fake_text[position:]
        elif self.operator == MATCH_STRING_OP:
            return selected_target_string
        else:
            raise ValueError("Operator not supported")

    def run(self) -> Tuple[Rule, MockTransaction]:
        self.selected_fields = self._select_fields()
        self.selected_target_strings = self._select_target_strings()
        if isinstance(self.selected_fields, str):
            if isinstance(self.selected_target_strings, str):
                fake_text = self._create_fake_text(self.selected_target_strings)
                attribute = Attribute.create(self.selected_fields)
                return self.rule, attribute.set_attribute(fake_text, self.transaction, self.rule)
            elif isinstance(self.selected_target_strings, list):
                fake_texts = []
                for target_string in self.selected_target_strings:
                    fake_texts.append(self._create_fake_text(target_string))
                attribute = Attribute.create(self.selected_fields)
                self.transaction = attribute.set_attribute(" ".join(fake_texts), self.transaction, self.rule)
                return self.rule, self.transaction
            else:
                raise ValueError("Field type not supported")
        elif isinstance(self.selected_fields, list):
            for field in self.selected_fields:
                if isinstance(self.selected_target_strings, str):
                    fake_text = self._create_fake_text(self.selected_target_strings)
                    attribute = Attribute.create(field)
                    self.transaction = attribute.set_attribute(fake_text, self.transaction, self.rule)
                elif isinstance(self.selected_target_strings, list):
                    for target_string in self.selected_target_strings:
                        fake_text = self._create_fake_text(target_string)
                        attribute = Attribute.create(field)
                        self.transaction = attribute.set_attribute(fake_text, self.transaction, self.rule)
                else:
                    raise ValueError("Field type not supported")
            return self.rule, self.transaction
        else:
            raise ValueError("Field type not supported")


class CreateTestCasesStringMixin:
    """Mixin to create test cases for string-based rules."""

    def create_test_cases_string(self, operator: RuleOperator, value_match_type: RuleMatchType) -> list:
        """Create test cases for a given operator and match type."""
        fake = Faker()
        random.seed(0)
        cases = []
        for _ in range(100):
            value_list_length = random.randint(1, 5)
            value_list = [" ".join(fake.words(nb=random.randint(1, 10))) for _ in range(value_list_length)]

            rule = StringRuleFactory.build(value=value_list, operator=operator, value_match_type=value_match_type)
            transaction = MockTransaction()
            cases.append({"rule": rule, "transaction": transaction})
        return cases


# =============================================================================
# Test Classes
# =============================================================================


class TestRuleEvaluation(CreateTestCasesStringMixin):
    """Tests for Rule evaluation (ported from Django's RuleTests)."""

    def test_evaluate_string_contains_any_of(self):
        """Test evaluating rules with contains operator and any-of match type."""
        for item in self.create_test_cases_string(CONTAINS_STRING_OP, ANY_OF):
            rule = item["rule"]
            transaction = item["transaction"]
            rule, transaction = RuleAndTransactionPreparer(transaction, rule).run()
            assert rule.evaluate(transaction) is True

    def test_evaluate_string_contains_all_of(self):
        """Test evaluating rules with contains operator and all-of match type."""
        data = self.create_test_cases_string(CONTAINS_STRING_OP, ALL_OF)
        for item in data:
            rule = item["rule"]
            transaction = item["transaction"]
            rule, transaction = RuleAndTransactionPreparer(transaction, rule).run()
            evaluate = rule.evaluate(transaction)
            assert evaluate is True

    def test_evaluate_string_exact_match_any_of(self):
        """Test evaluating rules with exact match operator and any-of match type."""
        for item in self.create_test_cases_string(MATCH_STRING_OP, ANY_OF):
            rule = item["rule"]
            transaction = item["transaction"]
            rule, transaction = RuleAndTransactionPreparer(transaction, rule).run()
            assert rule.evaluate(transaction) is True

    def test_evaluate_string_exact_match_all_of_fails(self):
        """Test that creating a rule with exact match and all-of raises an error."""
        with pytest.raises(ValueError):
            self.create_test_cases_string(MATCH_STRING_OP, ALL_OF)


class TestRuleSerializerPydantic:
    """Tests for Rule serialization/deserialization with Pydantic (ported from RuleSerializerTest)."""

    @pytest.mark.parametrize(
        "operator,value_match_type",
        [
            (CONTAINS_STRING_OP, ALL_OF),
            (CONTAINS_STRING_OP, ANY_OF),
        ],
    )
    def test_serialize_deserialize(self, operator: RuleOperator, value_match_type: RuleMatchType):
        """Test that rules can be serialized and deserialized correctly."""
        fake = Faker()
        random.seed(0)

        for _ in range(10):  # Reduced from 100 for faster tests
            value_list_length = random.randint(1, 5)
            value_list = [" ".join(fake.words(nb=random.randint(1, 10))) for _ in range(value_list_length)]

            rule = StringRuleFactory.build(value=value_list, operator=operator, value_match_type=value_match_type)

            # Serialize to dict
            serialized_data = rule.model_dump()

            # Deserialize back
            deserialized_obj = Rule.model_validate(serialized_data)

            assert rule == deserialized_obj


class TestRuleSetSerializerPydantic:
    """Tests for RuleSet serialization/deserialization with Pydantic (ported from RuleSetSerializerTest)."""

    @pytest.mark.parametrize(
        "rule_set_generator",
        [
            create_random_rule_set,
            lambda: create_random_rule_set_deep(depth=3),
        ],
        ids=["simple_rule_set", "deep_rule_set"],
    )
    def test_serialize_deserialize(self, rule_set_generator):
        """Test that rule sets can be serialized and deserialized correctly."""
        rule_set = rule_set_generator()

        # Serialize to dict
        serialized_data = rule_set.model_dump()

        # Deserialize back
        deserialized_obj = RuleSet.model_validate(serialized_data)

        assert rule_set == deserialized_obj


class TestRuleSetWrapperSerializerPydantic:
    """Tests for RuleSetWrapper serialization (ported from RuleSetWrapperSerializerTest).

    Note: The actual database persistence tests are in test_rule_set_wrapper_model.py.
    This class tests the Pydantic serialization aspects.
    """

    @pytest.mark.parametrize(
        "rule_set_generator",
        [
            create_random_rule_set,
            lambda: create_random_rule_set_deep(depth=3),
        ],
        ids=["simple_rule_set", "deep_rule_set"],
    )
    def test_rule_set_json_roundtrip(self, rule_set_generator):
        """Test that rule sets can be stored and retrieved from RuleSetWrapper."""
        rule_set = rule_set_generator()

        # Create a wrapper and set the rule set
        wrapper = RuleSetWrapper(category_id=None)
        wrapper.set_rule_set(rule_set)

        # Get the rule set back
        retrieved_rule_set = wrapper.get_rule_set()

        assert retrieved_rule_set is not None
        assert rule_set == retrieved_rule_set

    def test_empty_rule_set_returns_none(self):
        """Test that an empty rule set returns None."""
        wrapper = RuleSetWrapper(category_id=None, rule_set_json="{}")
        assert wrapper.get_rule_set() is None

    def test_invalid_json_returns_none(self):
        """Test that invalid JSON returns None."""
        wrapper = RuleSetWrapper(category_id=None, rule_set_json="invalid json")
        assert wrapper.get_rule_set() is None


class TestRuleFactories:
    """Tests for the rule factory classes."""

    def test_string_rule_factory_builds_valid_rule(self):
        """Test that StringRuleFactory produces valid Rule objects."""
        rule = StringRuleFactory.build()
        assert isinstance(rule, Rule)
        assert rule.field_type == "string"
        assert rule.clazz == "Rule"

    def test_rule_set_factory_builds_valid_rule_set(self):
        """Test that RuleSetFactory produces valid RuleSet objects."""
        rule_set = RuleSetFactory.build()
        assert isinstance(rule_set, RuleSet)
        assert rule_set.clazz == "RuleSet"
        assert rule_set.condition in ["AND", "OR"]

    def test_create_random_rule_set_has_nested_structure(self):
        """Test that create_random_rule_set produces nested rule sets."""
        rule_set = create_random_rule_set()
        assert isinstance(rule_set, RuleSet)
        # Should have at least one nested RuleSet
        has_nested = any(isinstance(r, RuleSet) for r in rule_set.rules)
        assert has_nested

    def test_create_random_rule_set_deep_has_correct_depth(self):
        """Test that create_random_rule_set_deep produces deeply nested rule sets."""
        depth = 2
        rule_set = create_random_rule_set_deep(depth=depth)
        assert isinstance(rule_set, RuleSet)

        # Verify depth by traversing
        current = rule_set
        for level in range(depth):
            assert len(current.rules) > 0
            # All rules at non-leaf levels should be RuleSets
            if level < depth - 1:
                assert all(isinstance(r, RuleSet) for r in current.rules)
                current = current.rules[0]


class TestRuleMatchType:
    """Tests for RuleMatchType."""

    def test_from_name_any_of(self):
        match_type = RuleMatchType.from_name("any of")
        assert match_type.name == "any of"
        assert match_type.value == "any of"
        assert match_type == ANY_OF

    def test_from_name_all_of(self):
        match_type = RuleMatchType.from_name("all of")
        assert match_type.name == "all of"
        assert match_type.value == "all of"
        assert match_type == ALL_OF

    def test_from_name_invalid(self):
        with pytest.raises(ValueError, match="Invalid name"):
            RuleMatchType.from_name("invalid")

    def test_equality(self):
        m1 = RuleMatchType(name="any of", value="any of")
        m2 = RuleMatchType(name="any of", value="any of")
        assert m1 == m2

    def test_hash(self):
        m1 = RuleMatchType(name="any of", value="any of")
        m2 = RuleMatchType(name="any of", value="any of")
        assert hash(m1) == hash(m2)


class TestRuleOperator:
    """Tests for RuleOperator."""

    def test_create_contains_string(self):
        op = RuleOperator.create("contains", "string")
        assert op.name == "contains"
        assert op.value == "contains"
        assert op.type == "string"
        assert op == CONTAINS_STRING_OP

    def test_create_exact_match_string(self):
        op = RuleOperator.create("exact match", "string")
        assert op == MATCH_STRING_OP

    def test_create_exact_match_number(self):
        op = RuleOperator.create("exact match", "number")
        assert op == MATCH_NUMBER_OP

    def test_equality(self):
        o1 = RuleOperator(name="contains", value="contains", type="string")
        o2 = RuleOperator(name="contains", value="contains", type="string")
        assert o1 == o2

    def test_hash(self):
        o1 = RuleOperator(name="contains", value="contains", type="string")
        o2 = RuleOperator(name="contains", value="contains", type="string")
        assert hash(o1) == hash(o2)


class TestRule:
    """Tests for Rule."""

    def test_create_valid_rule(self):
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["test"],
            value_match_type=ANY_OF,
            operator=CONTAINS_STRING_OP,
            clazz="Rule",
            type=TransactionTypeEnum.EXPENSES,
        )
        assert rule.field == ["communications"]
        assert rule.field_type == "string"
        assert rule.value == ["test"]
        assert rule.get_clazz() == "Rule"

    def test_rule_validation_invalid_field(self):
        """Test that an invalid field value is rejected by the Literal type."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Rule(
                field=["a.b.c"],  # Invalid field - not in TransactionField Literal
                field_type="string",
                value=["test"],
                value_match_type=ANY_OF,
                operator=CONTAINS_STRING_OP,
                clazz="Rule",
                type=TransactionTypeEnum.EXPENSES,
            )

    def test_rule_validation_number_field_type_with_string_values(self):
        with pytest.raises(ValueError, match="numbers"):
            Rule(
                field=["amount"],
                field_type="number",
                value=["not_a_number"],
                value_match_type=ANY_OF,
                operator=MATCH_NUMBER_OP,
                clazz="Rule",
                type=TransactionTypeEnum.EXPENSES,
            )

    def test_rule_validation_string_field_type_with_number_values(self):
        with pytest.raises(ValueError, match="strings"):
            Rule(
                field=["communications"],
                field_type="string",
                value=[123],
                value_match_type=ANY_OF,
                operator=CONTAINS_STRING_OP,
                clazz="Rule",
                type=TransactionTypeEnum.EXPENSES,
            )

    def test_rule_validation_invalid_operator_for_number(self):
        with pytest.raises(ValueError, match="Invalid operator for number"):
            Rule(
                field=["amount"],
                field_type="number",
                value=[100.0],
                value_match_type=ANY_OF,
                operator=CONTAINS_STRING_OP,
                clazz="Rule",
                type=TransactionTypeEnum.EXPENSES,
            )

    def test_rule_validation_exact_match_with_all_of(self):
        with pytest.raises(ValueError, match="any of"):
            Rule(
                field=["communications"],
                field_type="string",
                value=["test"],
                value_match_type=ALL_OF,
                operator=MATCH_STRING_OP,
                clazz="Rule",
                type=TransactionTypeEnum.EXPENSES,
            )

    def test_set_type(self):
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["test"],
            value_match_type=ANY_OF,
            operator=CONTAINS_STRING_OP,
            clazz="Rule",
            type=TransactionTypeEnum.EXPENSES,
        )
        rule.set_type(TransactionTypeEnum.REVENUE)
        assert rule.type == TransactionTypeEnum.REVENUE


class TestRuleSet:
    """Tests for RuleSet."""

    def test_create_valid_rule_set(self):
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["test"],
            value_match_type=ANY_OF,
            operator=CONTAINS_STRING_OP,
            clazz="Rule",
            type=TransactionTypeEnum.EXPENSES,
        )
        rule_set = RuleSet(
            condition="OR",
            rules=[rule],
            is_child=False,
            clazz="RuleSet",
            type=TransactionTypeEnum.EXPENSES,
        )
        assert rule_set.condition == "OR"
        assert len(rule_set.rules) == 1
        assert rule_set.get_clazz() == "RuleSet"

    def test_rule_set_set_type_propagates(self):
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["test"],
            value_match_type=ANY_OF,
            operator=CONTAINS_STRING_OP,
            clazz="Rule",
            type=TransactionTypeEnum.EXPENSES,
        )
        rule_set = RuleSet(
            condition="OR",
            rules=[rule],
            is_child=False,
            clazz="RuleSet",
            type=TransactionTypeEnum.EXPENSES,
        )
        rule_set.set_type(TransactionTypeEnum.REVENUE)
        assert rule_set.type == TransactionTypeEnum.REVENUE
        assert rule_set.rules[0].type == TransactionTypeEnum.REVENUE

    def test_rule_set_equality(self):
        rule1 = Rule(
            field=["communications"],
            field_type="string",
            value=["test"],
            value_match_type=ANY_OF,
            operator=CONTAINS_STRING_OP,
            clazz="Rule",
            type=TransactionTypeEnum.EXPENSES,
        )
        rule2 = Rule(
            field=["communications"],
            field_type="string",
            value=["test"],
            value_match_type=ANY_OF,
            operator=CONTAINS_STRING_OP,
            clazz="Rule",
            type=TransactionTypeEnum.EXPENSES,
        )
        rs1 = RuleSet(
            condition="OR",
            rules=[rule1],
            is_child=False,
            clazz="RuleSet",
            type=TransactionTypeEnum.EXPENSES,
        )
        rs2 = RuleSet(
            condition="OR",
            rules=[rule2],
            is_child=False,
            clazz="RuleSet",
            type=TransactionTypeEnum.EXPENSES,
        )
        assert rs1 == rs2

    def test_rule_set_from_dict(self):
        """Test that RuleSet can be created from a dictionary (JSON deserialization)."""
        data = {
            "condition": "OR",
            "rules": [
                {
                    "field": ["communications"],
                    "field_type": "string",
                    "value": ["test"],
                    "value_match_type": {"name": "any of", "value": "any of"},
                    "operator": {
                        "name": "contains",
                        "value": "contains",
                        "type": "string",
                    },
                    "clazz": "Rule",
                    "type": "EXPENSES",
                }
            ],
            "is_child": False,
            "clazz": "RuleSet",
            "type": "EXPENSES",
        }
        rule_set = RuleSet.model_validate(data)
        assert rule_set.condition == "OR"
        assert len(rule_set.rules) == 1
        assert isinstance(rule_set.rules[0], Rule)

    def test_nested_rule_set_from_dict(self):
        """Test that nested RuleSets can be created from dictionaries."""
        data = {
            "condition": "AND",
            "rules": [
                {
                    "condition": "OR",
                    "rules": [
                        {
                            "field": ["communications"],
                            "field_type": "string",
                            "value": ["test"],
                            "value_match_type": {"name": "any of", "value": "any of"},
                            "operator": {
                                "name": "contains",
                                "value": "contains",
                                "type": "string",
                            },
                            "clazz": "Rule",
                            "type": "EXPENSES",
                        }
                    ],
                    "is_child": True,
                    "clazz": "RuleSet",
                    "type": "EXPENSES",
                }
            ],
            "is_child": False,
            "clazz": "RuleSet",
            "type": "EXPENSES",
        }
        rule_set = RuleSet.model_validate(data)
        assert rule_set.condition == "AND"
        assert len(rule_set.rules) == 1
        assert isinstance(rule_set.rules[0], RuleSet)
        assert rule_set.rules[0].condition == "OR"

    def test_rule_set_serialization_roundtrip(self):
        """Test that RuleSet can be serialized and deserialized correctly."""
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["test"],
            value_match_type=ANY_OF,
            operator=CONTAINS_STRING_OP,
            clazz="Rule",
            type=TransactionTypeEnum.EXPENSES,
        )
        rule_set = RuleSet(
            condition="OR",
            rules=[rule],
            is_child=False,
            clazz="RuleSet",
            type=TransactionTypeEnum.EXPENSES,
        )

        # Serialize to dict
        data = rule_set.model_dump()

        # Deserialize back
        restored = RuleSet.model_validate(data)

        assert rule_set == restored


# =============================================================================
# Number evaluation tests (Task 0b)
# =============================================================================


class TestNumberEvaluation:
    """Tests for number field evaluation."""

    def _make_number_rule(self, operator, value, value_match_type=ANY_OF):
        return Rule(
            field=["amount"],
            field_type="number",
            value=value,
            value_match_type=value_match_type,
            operator=operator,
            clazz="Rule",
            type=TransactionTypeEnum.EXPENSES,
        )

    def test_evaluate_number_equals(self):
        rule = self._make_number_rule(EQUALS_NUMBER_OP, [100.0])
        txn = MockTransaction()
        txn.amount = 100.0
        assert rule.evaluate(txn) is True
        txn.amount = 99.0
        assert rule.evaluate(txn) is False

    def test_evaluate_number_greater_than(self):
        rule = self._make_number_rule(GT_NUMBER_OP, [50.0])
        txn = MockTransaction()
        txn.amount = 75.0
        assert rule.evaluate(txn) is True
        txn.amount = 30.0
        assert rule.evaluate(txn) is False

    def test_evaluate_number_less_than_or_equals(self):
        rule = self._make_number_rule(LTE_NUMBER_OP, [200.0])
        txn = MockTransaction()
        txn.amount = 200.0
        assert rule.evaluate(txn) is True
        txn.amount = 150.0
        assert rule.evaluate(txn) is True
        txn.amount = 201.0
        assert rule.evaluate(txn) is False

    def test_evaluate_number_not_equals(self):
        rule = self._make_number_rule(NOT_EQUALS_NUMBER_OP, [0.0])
        txn = MockTransaction()
        txn.amount = 50.0
        assert rule.evaluate(txn) is True
        txn.amount = 0.0
        assert rule.evaluate(txn) is False

    def test_evaluate_number_any_of_equals(self):
        rule = self._make_number_rule(EQUALS_NUMBER_OP, [10, 20, 30], ANY_OF)
        txn = MockTransaction()
        txn.amount = 20
        assert rule.evaluate(txn) is True
        txn.amount = 5
        assert rule.evaluate(txn) is False

    def test_evaluate_number_invalid_type(self):
        rule = self._make_number_rule(EQUALS_NUMBER_OP, [100.0])
        txn = MockTransaction()
        txn.amount = "not_a_number"
        with pytest.raises(ValueError, match="not a number"):
            rule.evaluate(txn)


# =============================================================================
# Fuzzy match tests (Task 0c)
# =============================================================================


class TestFuzzyMatch:
    """Tests for fuzzy match string evaluation."""

    def _make_fuzzy_rule(self, value, value_match_type=ANY_OF):
        return Rule(
            field=["communications"],
            field_type="string",
            value=value,
            value_match_type=value_match_type,
            operator=FUZZY_MATCH_STRING_OP,
            clazz="Rule",
            type=TransactionTypeEnum.EXPENSES,
        )

    def test_fuzzy_match_close_string(self):
        rule = self._make_fuzzy_rule(["Carrefour"])
        txn = MockTransaction()
        txn.communications = "Carefour"
        assert rule.evaluate(txn) is True

    def test_fuzzy_match_exact_passes(self):
        rule = self._make_fuzzy_rule(["Carrefour"])
        txn = MockTransaction()
        txn.communications = "Carrefour"
        assert rule.evaluate(txn) is True

    def test_fuzzy_match_no_match(self):
        rule = self._make_fuzzy_rule(["Carrefour"])
        txn = MockTransaction()
        txn.communications = "completely different string xyz"
        assert rule.evaluate(txn) is False

    def test_fuzzy_match_all_of(self):
        rule = self._make_fuzzy_rule(["Carefour", "Carrefour"], ALL_OF)
        txn = MockTransaction()
        txn.communications = "Carrefour"
        assert rule.evaluate(txn) is True
