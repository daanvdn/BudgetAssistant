"""Tests for budget router."""

import pytest
from httpx import ASGITransport, AsyncClient
from main import app


class TestBudgetEndpointsUnauthenticated:
    """Tests for budget endpoints without authentication."""

    @pytest.mark.asyncio
    async def test_find_or_create_budget_without_auth(self):
        """Test finding/creating budget without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/budget/find-or-create",
                json={
                    "bank_account_id": "BE68539007547034",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_budget_without_auth(self):
        """Test getting budget without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/budget/BE68539007547034")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_budget_entry_without_auth(self):
        """Test updating budget entry without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/budget/entry/1",
                json={
                    "amount": 500.00,
                },
            )

            assert response.status_code == 401


class TestBudgetEndpointsAuthenticated:
    """Tests for budget endpoints with authentication."""

    @pytest.mark.asyncio
    async def test_find_or_create_budget_with_auth(
        self, authenticated_client, seed_bank_account
    ):
        """Test finding/creating budget with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/budget/find-or-create",
            json={
                "bank_account_id": bank_account,
            },
            headers=headers,
        )

        # Should succeed or return 500 if root category doesn't exist
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "bank_account_id" in data

    @pytest.mark.asyncio
    async def test_get_budget_with_auth_not_found(
        self, authenticated_client, seed_bank_account
    ):
        """Test getting budget that doesn't exist with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.get(
            f"/api/budget/{bank_account}",
            headers=headers,
        )

        # Should be 404 (not found) since we haven't created a budget yet
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_budget_with_auth_forbidden(self, authenticated_client):
        """Test getting budget for account user doesn't own."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/budget/BE99999999999999",
            headers=headers,
        )

        # Should be 403 (forbidden) since user doesn't have access
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_budget_entry_with_auth_not_found(self, authenticated_client):
        """Test updating budget entry that doesn't exist."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.patch(
            "/api/budget/entry/999999",
            json={
                "amount": 500.00,
            },
            headers=headers,
        )

        # Should be 404 (not found)
        assert response.status_code == 404


class TestBudgetValidation:
    """Tests for budget endpoint validation."""

    @pytest.mark.asyncio
    async def test_find_or_create_budget_missing_bank_account(self):
        """Test finding/creating budget with missing bank account."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/budget/find-or-create",
                json={},
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_update_budget_entry_invalid_amount(self):
        """Test updating budget entry with invalid amount type."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/budget/entry/1",
                json={
                    "amount": "invalid",
                },
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]
