from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TokenBlocklist(SQLModel, table=True):
    """Blocklisted JWT tokens for logout functionality

    Tokens are stored here when a user logs out. The token remains in the blocklist
    until it naturally expires (based on expires_at), at which point it can be cleaned up.
    """

    __tablename__ = "token_blocklist"

    id: Optional[int] = Field(default=None, primary_key=True)
    jti: str = Field(unique=True, index=True, nullable=False)  # JWT ID or token hash
    token: str = Field(nullable=False)  # Full token for reference
    expires_at: datetime = Field(nullable=False)  # When the token naturally expires
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
