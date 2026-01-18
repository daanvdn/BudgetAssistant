"""Common enums and types used across the application."""

from enum import StrEnum


class TransactionTypeEnum(StrEnum):
    """Enum for transaction types."""

    REVENUE = "REVENUE"
    EXPENSES = "EXPENSES"
    BOTH = "BOTH"

    @staticmethod
    def from_value(value: str) -> "TransactionTypeEnum":
        """Convert a string value to TransactionTypeEnum."""
        value_lower = value.lower()
        if value_lower == "revenue":
            return TransactionTypeEnum.REVENUE
        elif value_lower == "expenses":
            return TransactionTypeEnum.EXPENSES
        elif value_lower == "both":
            return TransactionTypeEnum.BOTH
        else:
            raise ValueError(f"Invalid TransactionType value {value}")


class RecurrenceType(StrEnum):
    """Enum for recurrence types."""

    RECURRENT = "RECURRENT"
    NON_RECURRENT = "NON_RECURRENT"
    BOTH = "BOTH"

