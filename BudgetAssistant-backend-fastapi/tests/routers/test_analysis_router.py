"""Tests for analysis router."""

import pytest
from httpx import ASGITransport, AsyncClient
from main import app


class TestAnalysisEndpoints:
    """Integration tests for analysis endpoints."""

    @pytest.mark.asyncio
    async def test_revenue_expenses_per_period_without_auth(self):
        """Test getting revenue/expenses per period without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/analysis/revenue-expenses-per-period",
                json={
                    "account_number": "BE12345",
                    "transaction_type": "EXPENSES",
                    "start": "2023-01-01T00:00:00",
                    "end": "2023-12-31T23:59:59",
                    "grouping": "MONTH",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revenue_expenses_per_period_and_category_without_auth(self):
        """Test getting revenue/expenses per period and category without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/analysis/revenue-expenses-per-period-and-category",
                json={
                    "account_number": "BE12345",
                    "transaction_type": "EXPENSES",
                    "start": "2023-01-01T00:00:00",
                    "end": "2023-12-31T23:59:59",
                    "grouping": "MONTH",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_category_details_for_period_without_auth(self):
        """Test getting category details without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/analysis/category-details-for-period",
                json={
                    "account_number": "BE12345",
                    "transaction_type": "EXPENSES",
                    "start": "2023-01-01T00:00:00",
                    "end": "2023-12-31T23:59:59",
                    "grouping": "MONTH",
                    "category_qualified_name": "expenses/groceries",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_categories_for_account_without_auth(self):
        """Test getting categories for account without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/analysis/categories-for-account",
                params={
                    "bank_account": "BE12345",
                    "transaction_type": "EXPENSES",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_track_budget_without_auth(self):
        """Test tracking budget without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/analysis/track-budget",
                json={
                    "account_number": "BE12345",
                    "transaction_type": "EXPENSES",
                    "start": "2023-01-01T00:00:00",
                    "end": "2023-12-31T23:59:59",
                    "grouping": "MONTH",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_resolve_date_shortcut_without_auth(self):
        """Test resolving date shortcut without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/analysis/resolve-date-shortcut",
                params={"shortcut": "current month"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_resolve_date_shortcut_invalid_shortcut(self):
        """Test resolving invalid date shortcut."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/analysis/resolve-date-shortcut",
                params={"shortcut": "invalid shortcut"},
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]


class TestAnalysisQueryValidation:
    """Tests for analysis query validation."""

    @pytest.mark.asyncio
    async def test_revenue_expenses_query_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/analysis/revenue-expenses-per-period",
                json={
                    # Missing required fields
                    "grouping": "MONTH",
                },
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_revenue_expenses_query_invalid_grouping(self):
        """Test that invalid grouping is rejected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/analysis/revenue-expenses-per-period",
                json={
                    "account_number": "BE12345",
                    "transaction_type": "EXPENSES",
                    "start": "2023-01-01T00:00:00",
                    "end": "2023-12-31T23:59:59",
                    "grouping": "INVALID",  # Invalid grouping
                },
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]


class TestAnalysisEndpointsAuthenticated:
    """Tests for analysis endpoints with authentication."""

    @pytest.mark.asyncio
    async def test_revenue_expenses_per_period_with_auth(
        self, authenticated_client, seed_bank_account
    ):
        """Test getting revenue/expenses per period with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/analysis/revenue-expenses-per-period",
            json={
                "account_number": bank_account,
                "transaction_type": "EXPENSES",
                "start": "2023-01-01T00:00:00",
                "end": "2023-12-31T23:59:59",
                "grouping": "MONTH",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_revenue_expenses_per_period_and_category_with_auth(
        self, authenticated_client, seed_bank_account
    ):
        """Test getting revenue/expenses per period and category with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/analysis/revenue-expenses-per-period-and-category",
            json={
                "account_number": bank_account,
                "transaction_type": "EXPENSES",
                "start": "2023-01-01T00:00:00",
                "end": "2023-12-31T23:59:59",
                "grouping": "MONTH",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "periods" in data

    @pytest.mark.asyncio
    async def test_category_details_for_period_with_auth(
        self, authenticated_client, seed_bank_account
    ):
        """Test getting category details with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/analysis/category-details-for-period",
            json={
                "account_number": bank_account,
                "transaction_type": "EXPENSES",
                "start": "2023-01-01T00:00:00",
                "end": "2023-12-31T23:59:59",
                "grouping": "MONTH",
                "category_qualified_name": "expenses",
            },
            headers=headers,
        )

        # Should succeed or return 404 if category not found
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_categories_for_account_with_auth(
        self, authenticated_client, seed_bank_account
    ):
        """Test getting categories for account with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.get(
            "/api/analysis/categories-for-account",
            params={
                "bank_account": bank_account,
                "transaction_type": "EXPENSES",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data

    @pytest.mark.asyncio
    async def test_track_budget_with_auth(
        self, authenticated_client, seed_bank_account
    ):
        """Test tracking budget with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/analysis/track-budget",
            json={
                "account_number": bank_account,
                "transaction_type": "EXPENSES",
                "start": "2023-01-01T00:00:00",
                "end": "2023-12-31T23:59:59",
                "grouping": "MONTH",
            },
            headers=headers,
        )

        # Should succeed or return appropriate error
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_resolve_date_shortcut_with_auth(self, authenticated_client):
        """Test resolving date shortcut with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/analysis/resolve-date-shortcut",
            params={"shortcut": "current month"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "start" in data
        assert "end" in data

    @pytest.mark.asyncio
    async def test_resolve_date_shortcut_previous_month(self, authenticated_client):
        """Test resolving 'previous month' date shortcut."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/analysis/resolve-date-shortcut",
            params={"shortcut": "previous month"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "start" in data
        assert "end" in data

    @pytest.mark.asyncio
    async def test_resolve_date_shortcut_invalid(self, authenticated_client):
        """Test resolving invalid date shortcut."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/analysis/resolve-date-shortcut",
            params={"shortcut": "invalid shortcut"},
            headers=headers,
        )

        # Should fail validation (422)
        assert response.status_code == 422
