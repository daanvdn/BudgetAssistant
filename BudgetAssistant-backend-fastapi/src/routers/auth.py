"""Authentication router for user registration, login, and password management."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from db.database import get_session
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from models import User
from schemas import (
    ErrorResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordUpdateRequest,
    RegisterUserRequest,
    SuccessResponse,
    TokenResponse,
    UserRead,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Authentication"])

# JWT settings - in production, use environment variables
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(user_id: int, password_hash: str) -> str:
    """Create a password reset token.

    Token format: timestamp-hash
    The hash includes user_id, password_hash (invalidates token on password change),
    timestamp, and secret key.
    """
    from hashlib import sha256

    timestamp = int(datetime.now(timezone.utc).timestamp())
    token_hash = sha256(
        f"{user_id}{password_hash}{timestamp}{SECRET_KEY}".encode()
    ).hexdigest()[:20]
    return f"{timestamp}-{token_hash}"


def create_password_reset_uidb64(user_id: int) -> str:
    """Create base64-encoded user ID for password reset URL."""
    from base64 import urlsafe_b64encode

    return urlsafe_b64encode(str(user_id).encode()).decode()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_session),
) -> User:
    """Get the current authenticated user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return user


# Dependency for routes that require authentication
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/register",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def register(
    request: RegisterUserRequest,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Register a new user."""
    # Check if username already exists
    result = await session.execute(
        select(User).where(User.username == request.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    result = await session.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate password
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Create user
    user = User(
        username=request.username,
        email=request.email,
        password_hash=get_password_hash(request.password),
    )
    session.add(user)
    await session.commit()

    return SuccessResponse(message="User registered successfully", status_code=201)


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Authenticate user and return access and refresh tokens."""
    result = await session.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Refresh an access token using a refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": user.username})

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(current_user: CurrentUser) -> SuccessResponse:
    """Logout the current user.

    Note: With JWT, we can't truly invalidate tokens server-side without
    maintaining a blacklist. Client should discard the token.
    """
    return SuccessResponse(message="Logged out successfully")


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: CurrentUser) -> UserRead:
    """Get current user information."""
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    updates: PasswordUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Update current user's email or password."""
    if updates.email:
        current_user.email = updates.email
    if updates.password:
        current_user.password_hash = get_password_hash(updates.password)

    await session.commit()
    await session.refresh(current_user)

    return UserRead.model_validate(current_user)


@router.post("/password-reset", response_model=SuccessResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Request a password reset email.

    Note: In production, this should send an email with a reset link.
    For now, it just returns a success message.
    """
    result = await session.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if user:
        # TODO: Send password reset email with token
        pass

    return SuccessResponse(
        message="If the email exists, a password reset link will be sent"
    )


@router.get("/password-reset-validate/{uidb64}/{token}", response_model=dict)
async def validate_reset_token(
    uidb64: str,
    token: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Validate the UID and Token sent in the reset email.

    This endpoint checks if the password reset token is valid for the user
    identified by the uidb64 parameter.
    """
    from base64 import urlsafe_b64decode
    from hashlib import sha256
    from datetime import timezone

    try:
        # Decode the user ID from base64
        uid = urlsafe_b64decode(uidb64).decode()
        user_id = int(uid)

        # Find the user
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {"valid": False}

        # Validate the token
        # Token format: timestamp-hash
        # For security, we use a simple token validation scheme
        # In production, consider using itsdangerous or similar
        try:
            parts = token.split("-")
            if len(parts) != 2:
                return {"valid": False}

            timestamp_str, token_hash = parts
            timestamp = int(timestamp_str)

            # Check if token is expired (24 hours)
            current_timestamp = int(datetime.now(timezone.utc).timestamp())
            if current_timestamp - timestamp > 86400:  # 24 hours
                return {"valid": False}

            # Verify the hash
            expected_hash = sha256(
                f"{user.id}{user.password_hash}{timestamp}{SECRET_KEY}".encode()
            ).hexdigest()[:20]

            if token_hash == expected_hash:
                return {"valid": True}
            else:
                return {"valid": False}

        except (ValueError, IndexError):
            return {"valid": False}

    except Exception:
        return {"valid": False}


@router.post("/password-reset-confirm", response_model=SuccessResponse)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Confirm password reset with token.

    Note: In production, validate the reset token.
    """
    # TODO: Validate reset token and update password
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset confirmation not yet implemented",
    )
