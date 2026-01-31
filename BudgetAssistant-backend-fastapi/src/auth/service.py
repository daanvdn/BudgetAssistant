import hashlib
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas import Token, UserLogin, UserRegister
from auth.security import create_access_token, decode_access_token, get_password_hash, verify_password
from common.logging_utils import LoggerFactory
from config.settings import settings
from models.password_reset_token import PasswordResetToken
from models.token_blocklist import TokenBlocklist
from models.user import User

logger = LoggerFactory.for_caller()


def _get_token_jti(token: str) -> str:
    """Get the unique identifier for a token

    Uses the embedded jti claim if present, otherwise falls back to a hash of the token.
    """
    # Try to extract jti from token payload first
    payload = decode_access_token(token)
    if payload and "jti" in payload:
        return payload["jti"]
    # Fall back to hash for tokens without embedded jti
    return hashlib.sha256(token.encode()).hexdigest()


async def blocklist_token(db: AsyncSession, token: str) -> bool:
    """Add a token to the blocklist

    Returns True if token was blocklisted, False if already blocklisted or invalid
    """
    # Decode the token to get expiration
    payload = decode_access_token(token)
    if payload is None:
        logger.warning("Attempted to blocklist an invalid token")
        return False

    # Get expiration from token
    exp_timestamp = payload.get("exp")
    if exp_timestamp is None:
        logger.warning("Token has no expiration claim")
        return False

    expires_at = datetime.utcfromtimestamp(exp_timestamp)

    # Generate JTI (JWT ID) from token hash
    jti = _get_token_jti(token)

    # Check if already blocklisted
    result = await db.execute(select(TokenBlocklist).filter(TokenBlocklist.jti == jti))
    existing = result.scalar_one_or_none()
    if existing:
        logger.debug("Token already blocklisted")
        return True  # Already blocklisted, consider it success

    # Add to blocklist
    blocklist_entry = TokenBlocklist(jti=jti, token=token, expires_at=expires_at, created_at=datetime.utcnow())

    db.add(blocklist_entry)
    await db.commit()

    logger.info(f"Token blocklisted, expires at {expires_at}")
    return True


async def is_token_blocklisted(db: AsyncSession, token: str) -> bool:
    """Check if a token is in the blocklist"""
    jti = _get_token_jti(token)
    result = await db.execute(select(TokenBlocklist).filter(TokenBlocklist.jti == jti))
    return result.scalar_one_or_none() is not None


async def cleanup_expired_blocklist_tokens(db: AsyncSession) -> int:
    """Remove expired tokens from the blocklist

    Returns the number of tokens removed
    """
    from sqlalchemy import delete

    stmt = delete(TokenBlocklist).where(TokenBlocklist.expires_at < datetime.utcnow())
    result = await db.execute(stmt)
    await db.commit()
    # For async SQLAlchemy, rowcount may not always be available, return 0 if not
    try:
        return result.rowcount or 0
    except AttributeError:
        return 0


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    return True, "Password is valid"


async def register_user(db: AsyncSession, user_data: UserRegister) -> User:
    """Register a new user"""
    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ValueError("Email already registered")

    # Validate password strength
    is_valid, message = validate_password_strength(user_data.password)
    if not is_valid:
        raise ValueError(message)

    # Create new user
    logger.debug(f"Hashing password for new user: {user_data.email}")
    hashed_password = get_password_hash(user_data.password)
    logger.debug(f"Password hashed successfully for user: {user_data.email}")
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        is_active=True,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def authenticate_user(db: AsyncSession, login_data: UserLogin) -> Optional[User]:
    """Authenticate a user with email and password"""
    result = await db.execute(select(User).filter(User.email == login_data.email))
    user = result.scalar_one_or_none()
    if not user:
        return None

    if not verify_password(login_data.password, user.password_hash):
        return None

    return user


def create_user_token(user: User) -> Token:
    """Create access token for user"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


async def create_password_reset_token(db: AsyncSession, email: str) -> Optional[PasswordResetToken]:
    """Create a password reset token for a user"""
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None

    # Generate secure random token
    token = secrets.token_urlsafe(32)

    # Set expiration time
    expires_at = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)

    # Create reset token record
    reset_token = PasswordResetToken(
        user_id=user.id, token=token, expires_at=expires_at, used=False, created_at=datetime.utcnow()
    )

    db.add(reset_token)
    await db.commit()
    await db.refresh(reset_token)

    return reset_token


async def reset_password_with_token(db: AsyncSession, token: str, new_password: str) -> bool:
    """Reset user password using a reset token"""
    # Find the reset token
    result = await db.execute(select(PasswordResetToken).filter(PasswordResetToken.token == token))
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        raise ValueError("Invalid reset token")

    # Check if token is already used
    if reset_token.used:
        raise ValueError("Reset token has already been used")

    # Check if token is expired
    if reset_token.expires_at < datetime.utcnow():
        raise ValueError("Reset token has expired")

    # Validate new password
    is_valid, message = validate_password_strength(new_password)
    if not is_valid:
        raise ValueError(message)

    # Get the user
    user_result = await db.execute(select(User).filter(User.id == reset_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    # Update password
    user.password_hash = get_password_hash(new_password)

    # Mark token as used
    reset_token.used = True

    await db.commit()

    return True
