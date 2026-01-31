from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration"""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

    class Config:
        json_schema_extra = {"example": {"email": "john@example.com", "password": "SecurePass123"}}


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {"example": {"email": "john@example.com", "password": "SecurePass123"}}


class Token(BaseModel):
    """Schema for JWT token response"""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data"""

    email: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response"""

    id: int
    email: str
    is_active: bool

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""

    email: EmailStr

    class Config:
        json_schema_extra = {"example": {"email": "john@example.com"}}


class ForgotPasswordResponse(BaseModel):
    """Schema for forgot password response"""

    message: str
    reset_token: Optional[str] = None  # Only for LAN use without email


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request"""

    token: str
    new_password: str = Field(..., min_length=8, max_length=72)

    class Config:
        json_schema_extra = {"example": {"token": "reset-token-here", "new_password": "NewSecurePass123"}}


class ResetPasswordResponse(BaseModel):
    """Schema for reset password response"""

    message: str


class LogoutResponse(BaseModel):
    """Schema for logout response"""

    message: str
