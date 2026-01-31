"""Tests for authentication router."""

import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from routers.auth import create_access_token, get_password_hash, verify_password


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
        from routers.auth import ALGORITHM, SECRET_KEY

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


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_token_refresh_without_token(self):
        """Test token refresh without providing a refresh token."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/auth/token/refresh")

            # Should fail validation (422) - missing required parameter
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_token_refresh_with_invalid_token(self):
        """Test token refresh with invalid refresh token."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/token/refresh",
                params={"refresh_token": "invalid-token"},
            )

            assert response.status_code == 401


class TestUpdateMe:
    """Tests for PATCH /me endpoint."""

    @pytest.mark.asyncio
    async def test_update_me_without_auth(self):
        """Test updating user profile without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/auth/me",
                json={
                    "email": "newemail@example.com",
                },
            )

            assert response.status_code == 401


class TestPasswordReset:
    """Tests for password reset endpoints."""

    @pytest.mark.asyncio
    async def test_password_reset_request(self, authenticated_client):
        """Test requesting a password reset (public endpoint)."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/auth/password-reset",
            json={
                "email": "test@example.com",
            },
        )

        # Should succeed (returns generic message to prevent email enumeration)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_password_reset_request_invalid_email(self, authenticated_client):
        """Test password reset with invalid email format.

        Note: The endpoint returns 200 even for invalid emails to prevent
        email enumeration attacks.
        """
        client, _ = authenticated_client
        response = await client.post(
            "/api/auth/password-reset",
            json={
                "email": "invalid-email",
            },
        )

        # Returns 200 to prevent email enumeration (doesn't reveal if email exists/is valid)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_password_reset_confirm_not_implemented(self):
        """Test password reset confirmation returns 501 Not Implemented."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/password-reset-confirm",
                json={
                    "token": "some-token",
                    "new_password": "newpassword123",
                },
            )

            # Should return 501 Not Implemented
            assert response.status_code == 501


class TestValidateResetToken:
    """Tests for validate_reset_token endpoint."""

    @pytest.mark.asyncio
    async def test_validate_reset_token_invalid_uidb64(self):
        """Test validation with invalid base64 user ID."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/auth/password-reset-validate/invalid-base64/some-token",
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_reset_token_nonexistent_user(self):
        """Test validation with non-existent user ID."""
        from base64 import urlsafe_b64encode

        # Encode a non-existent user ID
        uidb64 = urlsafe_b64encode(b"999999").decode()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/auth/password-reset-validate/{uidb64}/some-token",
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_reset_token_invalid_token_format(self):
        """Test validation with invalid token format."""
        from base64 import urlsafe_b64encode

        uidb64 = urlsafe_b64encode(b"1").decode()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/auth/password-reset-validate/{uidb64}/invalid-token-no-dash",
            )

            # Token format is invalid (missing dash separator)
            assert response.status_code == 200
            data = response.json()
            # Should return valid=False for invalid format
            assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_reset_token_expired_token(self):
        """Test validation with expired token (timestamp too old)."""
        from base64 import urlsafe_b64encode

        uidb64 = urlsafe_b64encode(b"1").decode()
        # Use a very old timestamp (1 second since epoch)
        old_token = "1-somehash"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/auth/password-reset-validate/{uidb64}/{old_token}",
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False


class TestAuthEndpointsAuthenticated:
    """Tests for auth endpoints with authentication."""

    @pytest.mark.asyncio
    async def test_get_me_with_auth(self, authenticated_client):
        """Test getting current user info with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get("/api/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "id" in data

    @pytest.mark.asyncio
    async def test_update_me_with_auth(self, authenticated_client):
        """Test updating user profile with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.patch(
            "/api/auth/me",
            json={
                "email": "updated@example.com",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == "updated@example.com"

    @pytest.mark.asyncio
    async def test_logout_with_auth(self, authenticated_client):
        """Test logout with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.post("/api/auth/logout", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_token_refresh_with_valid_token(self, authenticated_client):
        """Test token refresh with valid refresh token."""
        client, access_token = authenticated_client

        # First login to get refresh token
        login_response = await client.post(
            "/api/auth/token",
            data={
                "username": "testuser",
                "password": "testpassword123",
            },
        )

        if login_response.status_code == 200:
            tokens = login_response.json()
            refresh_token = tokens.get("refresh_token")

            if refresh_token:
                response = await client.post(
                    "/api/auth/token/refresh",
                    params={"refresh_token": refresh_token},
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "refresh_token" in data
