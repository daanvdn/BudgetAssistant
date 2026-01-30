"""Pydantic schemas for BankAccount API operations."""

from pydantic import BaseModel


class BankAccountCreate(BaseModel):
    """Schema for creating a new bank account."""

    account_number: str
    alias: str | None = None


class BankAccountRead(BaseModel):
    """Schema for reading bank account data (response)."""

    account_number: str
    alias: str | None = None

    model_config = {"from_attributes": True}


class BankAccountUpdate(BaseModel):
    """Schema for updating bank account data."""

    alias: str | None = None
