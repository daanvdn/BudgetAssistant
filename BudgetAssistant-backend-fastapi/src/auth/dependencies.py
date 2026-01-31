from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas import TokenData
from auth.security import decode_access_token
from auth.service import is_token_blocklisted
from config.settings import settings
from db.database import get_session
from models.user import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User:
    """Get the current authenticated user

    - If DEV_AUTH_BYPASS is enabled and the request contains the DEV_BYPASS_HEADER set to '1',
      return a local dev user (first user or by configured email). If no user exists, create and return
      a dummy dev user.
    - Otherwise validate the JWT token from the Authorization header (Bearer token).
    - Also checks if the token has been blocklisted (logged out).
    """
    # Dev bypass: explicit opt-in only
    if settings.DEV_AUTH_BYPASS:
        header_val = request.headers.get(settings.DEV_BYPASS_HEADER)
        if header_val == "1":
            # Try to find specific user by email if configured
            if settings.DEV_BYPASS_USER_EMAIL:
                print("DEV_AUTH_BYPASS active: returning user with email", settings.DEV_BYPASS_USER_EMAIL)
                result = await db.execute(select(User).filter(User.email == settings.DEV_BYPASS_USER_EMAIL))
                user = result.scalar_one_or_none()
                if user:
                    return user
            # Fallback: return the first user in DB
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if user:
                print("DEV_AUTH_BYPASS active: returning first user in database")
                return user
            # If no user exists, create a dummy dev user and return it
            dummy_user = User(email="dev-bypass@local.com", password_hash="", is_active=True)
            db.add(dummy_user)
            await db.commit()
            await db.refresh(dummy_user)
            print("DEV_AUTH_BYPASS active: created and returned dummy dev user")
            return dummy_user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract Authorization header manually so we control behavior in absence of header
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        raise credentials_exception

    try:
        scheme, token = auth_header.split()
    except ValueError:
        raise credentials_exception

    if scheme.lower() != "bearer":
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Check if token is blocklisted (user logged out)
    if await is_token_blocklisted(db, token):
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    token_data = TokenData(email=email)

    result = await db.execute(select(User).filter(User.email == token_data.email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Type alias for dependency injection - used by other routers
CurrentUser = Annotated[User, Depends(get_current_active_user)]
