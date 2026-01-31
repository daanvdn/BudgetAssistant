"""Pydantic schemas for User API operations."""

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    password: str
    first_name: str = ""
    last_name: str = ""


class UserRead(BaseModel):
    """Schema for reading user data (response)."""

    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Schema for updating user data."""

    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    password: str | None = None
