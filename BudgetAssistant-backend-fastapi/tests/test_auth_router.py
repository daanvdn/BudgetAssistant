"""Tests for authentication router."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from routers.auth import get_password_hash, verify_password, create_access_token


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_and_verify_password(self):
        """Test that password hashing and verification works."""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "securepassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_hash_is_bcrypt_format(self):
        """Test that the hash is in bcrypt format."""
        password = "test"
        hashed = get_password_hash(password)
        # Bcrypt hashes start with $2a$, $2b$, or $2y$
        assert hashed.startswith("$2")


class TestJWTTokens:
    """Tests for JWT token creation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        token = create_access_token(data={"sub": "testuser"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_subject(self):
        """Test that access token can be decoded to get subject."""
        from jose import jwt
        from routers.auth import SECRET_KEY, ALGORITHM

        token = create_access_token(data={"sub": "testuser"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert payload["sub"] == "testuser"
        assert payload["type"] == "access"
        assert "exp" in payload


class TestAuthEndpoints:
    """Integration tests for auth endpoints."""

    @pytest.mark.asyncio
    async def test_register_user_password_too_short(self):
        """Test registration with password that's too short."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/register",
                json={
                    "username": "newuser",
                    "password": "short",  # Too short
                    "email": "newuser@example.com",
                },
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_without_credentials(self):
        """Test login without credentials."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/token",
                data={},  # No credentials
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/auth/me")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer invalidtoken"},
            )

            assert response.status_code == 401


class TestLogout:
    """Tests for logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_without_auth(self):
        """Test logout without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/auth/logout")

            assert response.status_code == 401

