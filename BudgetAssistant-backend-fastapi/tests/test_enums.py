"""Tests for enums module."""

import pytest
from enums import RecurrenceType, TransactionTypeEnum


class TestTransactionTypeEnum:
    """Test cases for TransactionTypeEnum."""

    def test_enum_values(self):
        """Test that enum has correct values."""
        assert TransactionTypeEnum.REVENUE == "REVENUE"
        assert TransactionTypeEnum.EXPENSES == "EXPENSES"
        assert TransactionTypeEnum.BOTH == "BOTH"

    def test_from_value_revenue(self):
        """Test from_value for REVENUE."""
        result = TransactionTypeEnum.from_value("revenue")
        assert result == TransactionTypeEnum.REVENUE

        result = TransactionTypeEnum.from_value("REVENUE")
        assert result == TransactionTypeEnum.REVENUE

    def test_from_value_expenses(self):
        """Test from_value for EXPENSES."""
        result = TransactionTypeEnum.from_value("expenses")
        assert result == TransactionTypeEnum.EXPENSES

        result = TransactionTypeEnum.from_value("EXPENSES")
        assert result == TransactionTypeEnum.EXPENSES

    def test_from_value_both(self):
        """Test from_value for BOTH."""
        result = TransactionTypeEnum.from_value("both")
        assert result == TransactionTypeEnum.BOTH

        result = TransactionTypeEnum.from_value("BOTH")
        assert result == TransactionTypeEnum.BOTH

    def test_from_value_invalid(self):
        """Test from_value raises error for invalid value."""
        with pytest.raises(ValueError) as exc_info:
            TransactionTypeEnum.from_value("invalid")
        assert "Invalid TransactionType value" in str(exc_info.value)

    def test_enum_is_str_enum(self):
        """Test that enum values can be used as strings."""
        assert str(TransactionTypeEnum.REVENUE) == "REVENUE"
        assert f"Type: {TransactionTypeEnum.EXPENSES}" == "Type: EXPENSES"


class TestRecurrenceType:
    """Test cases for RecurrenceType."""

    def test_enum_values(self):
        """Test that enum has correct values."""
        assert RecurrenceType.RECURRENT == "RECURRENT"
        assert RecurrenceType.NON_RECURRENT == "NON_RECURRENT"
        assert RecurrenceType.BOTH == "BOTH"

    def test_enum_is_str_enum(self):
        """Test that enum values can be used as strings."""
        assert str(RecurrenceType.RECURRENT) == "RECURRENT"
        assert (
            f"Recurrence: {RecurrenceType.NON_RECURRENT}" == "Recurrence: NON_RECURRENT"
        )
