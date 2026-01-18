"""Tests for bank accounts router."""

import pytest
from httpx import AsyncClient, ASGITransport

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

