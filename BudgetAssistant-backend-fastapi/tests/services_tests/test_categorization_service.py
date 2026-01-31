"""Tests for categorization service."""

from common.enums import TransactionTypeEnum
from models.rules import (
    ALL_OF,
    ANY_OF,
    CONTAINS_STRING_OP,
    Rule,
    RuleSet,
)


class TestRuleEvaluation:
    """Tests for the Rule/RuleSet evaluation (ported from RuleEvaluator tests)."""

    def test_any_match_single_match(self):
        """Test _any_match with a single matching value."""
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["test"],
            operator=CONTAINS_STRING_OP,
            value_match_type=ANY_OF,
            type=TransactionTypeEnum.EXPENSES,
        )

        result = rule._any_match(["test"], "This is a test string")
        assert result is True

    def test_any_match_no_match(self):
        """Test _any_match with no matching values."""
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["xyz"],
            operator=CONTAINS_STRING_OP,
            value_match_type=ANY_OF,
            type=TransactionTypeEnum.EXPENSES,
        )

        result = rule._any_match(["xyz"], "This is a test string")
        assert result is False

    def test_any_match_with_spaces(self):
        """Test _any_match handles spaces in patterns."""
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["test string"],
            operator=CONTAINS_STRING_OP,
            value_match_type=ANY_OF,
            type=TransactionTypeEnum.EXPENSES,
        )

        # Pattern "test string" should match "test  string" (multiple spaces)
        result = rule._any_match(["test string"], "This is a test  string")
        assert result is True

    def test_all_match_all_present(self):
        """Test _all_match when all values are present."""
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["test", "string"],
            operator=CONTAINS_STRING_OP,
            value_match_type=ALL_OF,
            type=TransactionTypeEnum.EXPENSES,
        )

        result = rule._all_match(["test", "string"], "This is a test string")
        assert result is True

    def test_all_match_partial(self):
        """Test _all_match when only some values match."""
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["test", "xyz"],
            operator=CONTAINS_STRING_OP,
            value_match_type=ALL_OF,
            type=TransactionTypeEnum.EXPENSES,
        )

        # Should return False because "xyz" doesn't match
        result = rule._all_match(["test", "xyz"], "This is a test string")
        assert result is False

    def test_evaluate_string_contains_any_of(self):
        """Test evaluate_string with contains operator and any of match type."""
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["grocery", "supermarket"],
            operator=CONTAINS_STRING_OP,
            value_match_type=ANY_OF,
            type=TransactionTypeEnum.EXPENSES,
        )

        result = rule.evaluate_string(
            "This is a grocery store", ["grocery", "supermarket"]
        )
        assert result is True

    def test_evaluate_string_contains_no_match(self):
        """Test evaluate_string with contains operator and no match."""
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["grocery", "supermarket"],
            operator=CONTAINS_STRING_OP,
            value_match_type=ANY_OF,
            type=TransactionTypeEnum.EXPENSES,
        )

        result = rule.evaluate_string(
            "This is a clothing store", ["grocery", "supermarket"]
        )
        assert result is False

    def test_evaluate_rule_set_empty(self):
        """Test evaluate_rule_set with empty rules."""
        rule_set = RuleSet(
            condition="AND",
            rules=[],
            is_child=False,
            type=TransactionTypeEnum.EXPENSES,
        )

        # Mock transaction object
        class MockTransaction:
            pass

        result = rule_set.evaluate(MockTransaction())
        assert result is False

    def test_evaluate_rule_simple_string_match(self):
        """Test evaluating a simple string rule."""
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["groceries"],
            operator=CONTAINS_STRING_OP,
            value_match_type=ANY_OF,
            type=TransactionTypeEnum.EXPENSES,
        )

        # Create a mock transaction
        class MockTransaction:
            communications = "Payment for groceries"
            transaction = "Supermarket purchase"

        result = rule.evaluate(MockTransaction())
        assert result is True

    def test_evaluate_rule_no_match(self):
        """Test evaluating a rule with no match."""
        rule = Rule(
            field=["communications"],
            field_type="string",
            value=["groceries"],
            operator=CONTAINS_STRING_OP,
            value_match_type=ANY_OF,
            type=TransactionTypeEnum.EXPENSES,
        )

        class MockTransaction:
            communications = "Payment for utilities"
            transaction = "Electric bill"

        result = rule.evaluate(MockTransaction())
        assert result is False

    def test_evaluate_rule_set_and_condition(self):
        """Test evaluate_rule_set with AND condition."""

        class MockTransaction:
            communications = "Grocery shopping"
            transaction = "Supermarket"

        rule_set = RuleSet(
            condition="AND",
            rules=[
                Rule(
                    field=["communications"],
                    field_type="string",
                    value=["grocery"],
                    operator=CONTAINS_STRING_OP,
                    value_match_type=ANY_OF,
                    type=TransactionTypeEnum.EXPENSES,
                ),
                Rule(
                    field=["transaction"],
                    field_type="string",
                    value=["supermarket"],
                    operator=CONTAINS_STRING_OP,
                    value_match_type=ANY_OF,
                    type=TransactionTypeEnum.EXPENSES,
                ),
            ],
            is_child=False,
            type=TransactionTypeEnum.EXPENSES,
        )

        result = rule_set.evaluate(MockTransaction())
        assert result is True

    def test_evaluate_rule_set_or_condition(self):
        """Test evaluate_rule_set with OR condition."""

        class MockTransaction:
            communications = "Grocery shopping"
            transaction = "Local store"  # Doesn't match "supermarket"

        rule_set = RuleSet(
            condition="OR",
            rules=[
                Rule(
                    field=["communications"],
                    field_type="string",
                    value=["grocery"],
                    operator=CONTAINS_STRING_OP,
                    value_match_type=ANY_OF,
                    type=TransactionTypeEnum.EXPENSES,
                ),
                Rule(
                    field=["transaction"],
                    field_type="string",
                    value=["supermarket"],
                    operator=CONTAINS_STRING_OP,
                    value_match_type=ANY_OF,
                    type=TransactionTypeEnum.EXPENSES,
                ),
            ],
            is_child=False,
            type=TransactionTypeEnum.EXPENSES,
        )

        result = rule_set.evaluate(MockTransaction())
        assert result is True  # "grocery" matches in communications

    def test_evaluate_rule_nested_field(self):
        """Test evaluating a rule with nested field (e.g., counterparty.name)."""
        rule = Rule(
            field=["counterparty.name"],
            field_type="string",
            value=["supermarket"],
            operator=CONTAINS_STRING_OP,
            value_match_type=ANY_OF,
            type=TransactionTypeEnum.EXPENSES,
        )

        # Create mock objects
        class MockCounterparty:
            name = "ABC Supermarket"

        class MockTransaction:
            counterparty = MockCounterparty()

        result = rule.evaluate(MockTransaction())
        assert result is True
