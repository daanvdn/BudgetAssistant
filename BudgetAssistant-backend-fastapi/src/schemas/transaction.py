"""Pydantic schemas for Transaction API operations."""

from datetime import date, datetime

from pydantic import BaseModel

from enums import TransactionTypeEnum


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""

    bank_account_id: str
    booking_date: date
    statement_number: str
    counterparty_id: str
    transaction_number: str
    transaction: str | None = None
    currency_date: date
    amount: float
    currency: str
    bic: str | None = None
    country_code: str
    communications: str | None = None
    category_id: int | None = None
    manually_assigned_category: bool = False
    is_recurring: bool = False
    is_advance_shared_account: bool = False


class TransactionRead(BaseModel):
    """Schema for reading transaction data (response)."""

    transaction_id: str
    bank_account_id: str
    booking_date: date
    statement_number: str
    counterparty_id: str
    transaction_number: str
    transaction: str | None = None
    currency_date: date
    amount: float
    currency: str
    bic: str | None = None
    country_code: str
    communications: str | None = None
    category_id: int | None = None
    manually_assigned_category: bool
    is_recurring: bool
    is_advance_shared_account: bool
    upload_timestamp: datetime
    is_manually_reviewed: bool

    model_config = {"from_attributes": True}

    def get_transaction_type(self) -> TransactionTypeEnum:
        """Determine transaction type based on amount."""
        if self.amount >= 0.0:
            return TransactionTypeEnum.REVENUE
        return TransactionTypeEnum.EXPENSES


class TransactionUpdate(BaseModel):
    """Schema for updating transaction data."""

    transaction: str | None = None
    category_id: int | None = None
    manually_assigned_category: bool | None = None
    is_recurring: bool | None = None
    is_advance_shared_account: bool | None = None
    is_manually_reviewed: bool | None = None

