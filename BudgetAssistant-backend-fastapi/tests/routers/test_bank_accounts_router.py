"""Tests for bank accounts router."""

import pytest
from httpx import ASGITransport, AsyncClient
from main import app


class TestBankAccountsEndpoints:
    """Integration tests for bank accounts endpoints."""

    @pytest.mark.asyncio
    async def test_get_bank_accounts_without_auth(self):
        """Test getting bank accounts without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/bank-accounts")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_bank_account_without_auth(self):
        """Test creating bank account without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/bank-accounts",
                json={
                    "account_number": "BE12345678901234",
                    "alias": "My Savings",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_specific_bank_account_without_auth(self):
        """Test getting specific bank account without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/bank-accounts/BE12345678901234")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_bank_account_without_auth(self):
        """Test updating bank account without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/bank-accounts/BE12345678901234",
                json={
                    "alias": "Updated Alias",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_bank_account_without_auth(self):
        """Test deleting bank account without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/bank-accounts/BE12345678901234")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_save_alias_without_auth(self):
        """Test saving alias without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/bank-accounts/save-alias",
                json={
                    "alias": "New Alias",
                    "bank_account": "BE12345678901234",
                },
            )

            assert response.status_code == 401


class TestBankAccountsEndpointsAuthenticated:
    """Tests for bank accounts endpoints with authentication."""

    @pytest.mark.asyncio
    async def test_get_bank_accounts_with_auth(self, authenticated_client):
        """Test getting bank accounts with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get("/api/bank-accounts", headers=headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_bank_account_with_auth(self, authenticated_client):
        """Test creating bank account with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.post(
            "/api/bank-accounts",
            json={
                "account_number": "BE68539007547034",
                "alias": "My Test Account",
            },
            headers=headers,
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "account_number" in data

    @pytest.mark.asyncio
    async def test_get_specific_bank_account_with_auth(
        self, authenticated_client, seed_bank_account
    ):
        """Test getting specific bank account with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.get(
            f"/api/bank-accounts/{bank_account}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "account_number" in data

    @pytest.mark.asyncio
    async def test_get_specific_bank_account_not_found(self, authenticated_client):
        """Test getting bank account that doesn't exist."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/bank-accounts/BE99999999999999",
            headers=headers,
        )

        # Should be 404 (not found) or 403 (forbidden)
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_update_bank_account_with_auth(
        self, authenticated_client, seed_bank_account
    ):
        """Test updating bank account with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.patch(
            f"/api/bank-accounts/{bank_account}",
            json={
                "alias": "Updated Test Alias",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("alias") == "Updated Test Alias"

    @pytest.mark.asyncio
    async def test_save_alias_with_auth(self, authenticated_client, seed_bank_account):
        """Test saving alias with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/bank-accounts/save-alias",
            json={
                "alias": "New Alias via Save",
                "bank_account": bank_account,
            },
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_bank_account_with_auth(
        self, authenticated_client, seed_bank_account
    ):
        """Test deleting bank account with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.delete(
            f"/api/bank-accounts/{bank_account}",
            headers=headers,
        )

        # Should succeed or return appropriate error
        assert response.status_code in [200, 204, 404]
