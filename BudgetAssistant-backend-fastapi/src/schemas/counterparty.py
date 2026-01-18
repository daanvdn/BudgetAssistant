"""Pydantic schemas for Counterparty API operations."""

from pydantic import BaseModel


class CounterpartyCreate(BaseModel):
    """Schema for creating a new counterparty."""

    name: str
    account_number: str = ""
    street_and_number: str | None = None
    zip_code_and_city: str | None = None
    category_id: int | None = None


class CounterpartyRead(BaseModel):
    """Schema for reading counterparty data (response)."""

    name: str
    account_number: str
    street_and_number: str | None = None
    zip_code_and_city: str | None = None
    category_id: int | None = None

    model_config = {"from_attributes": True}


class CounterpartyUpdate(BaseModel):
    """Schema for updating counterparty data."""

    account_number: str | None = None
    street_and_number: str | None = None
    zip_code_and_city: str | None = None
    category_id: int | None = None

