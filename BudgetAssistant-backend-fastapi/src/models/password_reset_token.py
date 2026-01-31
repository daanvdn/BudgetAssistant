from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class PasswordResetToken(SQLModel, table=True):
    """Password reset token model"""

    __tablename__ = "password_reset_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    token: str = Field(unique=True, index=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    used: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
