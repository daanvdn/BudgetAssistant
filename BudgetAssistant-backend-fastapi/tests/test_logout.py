"""Tests for logout functionality with token blocklisting"""

from datetime import datetime, timedelta

import pytest

from auth.security import create_access_token, get_password_hash
from auth.service import blocklist_token, is_token_blocklisted
from models import User
from utils import assert_persisted


@pytest.mark.anyio
async def test_logout_invalidates_token(async_session, client):
    """Test that logout properly invalidates the token"""
    # Create a test user
    user = User(
        name="Logout Test User",
        email="logouttest@example.com",
        password_hash=get_password_hash("SecurePass123"),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    await assert_persisted(async_session, User, "id", user.id, user.model_dump())

    # Login to get a token
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "logouttest@example.com", "password": "SecurePass123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify token works - get current user
    me_response = await client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "logouttest@example.com"

    # Logout - this should blocklist the token
    logout_response = await client.post("/api/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Successfully logged out"

    # Try to use the same token again - should fail
    me_response_after_logout = await client.get("/api/auth/me", headers=headers)
    assert me_response_after_logout.status_code == 401


@pytest.mark.anyio
async def test_logout_without_token_fails(client):
    """Test that logout without a token returns 401"""
    logout_response = await client.post("/api/auth/logout")
    assert logout_response.status_code == 401


@pytest.mark.anyio
async def test_login_after_logout_works(async_session, client):
    """Test that users can login again after logging out"""
    # Create a test user
    user = User(
        name="Relogin Test User",
        email="relogintest@example.com",
        password_hash=get_password_hash("SecurePass123"),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    # Login to get first token
    login_response1 = await client.post(
        "/api/auth/login",
        json={"email": "relogintest@example.com", "password": "SecurePass123"},
    )
    assert login_response1.status_code == 200
    token1 = login_response1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Logout with first token
    logout_response = await client.post("/api/auth/logout", headers=headers1)
    assert logout_response.status_code == 200

    # First token should no longer work
    me_response_old_token = await client.get("/api/auth/me", headers=headers1)
    assert me_response_old_token.status_code == 401

    # Login again to get a new token
    login_response2 = await client.post(
        "/api/auth/login",
        json={"email": "relogintest@example.com", "password": "SecurePass123"},
    )
    assert login_response2.status_code == 200
    token2 = login_response2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # New token should work
    me_response_new_token = await client.get("/api/auth/me", headers=headers2)
    assert me_response_new_token.status_code == 200
    assert me_response_new_token.json()["email"] == "relogintest@example.com"


@pytest.mark.anyio
async def test_token_blocklist_service(async_session):
    """Test the blocklist service functions directly"""
    # Create a valid token
    token = create_access_token({"sub": "test@example.com"}, timedelta(hours=1))

    # Token should not be blocklisted initially
    is_blocked = await is_token_blocklisted(async_session, token)
    assert is_blocked is False

    # Blocklist the token
    result = await blocklist_token(async_session, token)
    assert result is True

    # Token should now be blocklisted
    is_blocked = await is_token_blocklisted(async_session, token)
    assert is_blocked is True

    # Blocklisting again should return True (already blocklisted)
    result = await blocklist_token(async_session, token)
    assert result is True
