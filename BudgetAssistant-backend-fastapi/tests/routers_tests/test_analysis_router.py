"""Tests for analysis router."""

from datetime import date
from unittest.mock import patch

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
                    "start": "2023-01-01",
                    "end": "2023-12-31",
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
                    "start": "2023-01-01",
                    "end": "2023-12-31",
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
                    "start": "2023-01-01",
                    "end": "2023-12-31",
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
                    "start": "2023-01-01",
                    "end": "2023-12-31",
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
                    "start": "2023-01-01",
                    "end": "2023-12-31",
                    "grouping": "INVALID",  # Invalid grouping
                },
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]


class TestAnalysisEndpointsAuthenticated:
    """Tests for analysis endpoints with authentication."""

    @pytest.mark.asyncio
    async def test_revenue_expenses_per_period_with_auth(self, authenticated_client, seed_bank_account):
        """Test getting revenue/expenses per period with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/analysis/revenue-expenses-per-period",
            json={
                "account_number": bank_account,
                "transaction_type": "EXPENSES",
                "start": "2023-01-01",
                "end": "2023-12-31",
                "grouping": "MONTH",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_revenue_expenses_per_period_and_category_with_auth(self, authenticated_client, seed_bank_account):
        """Test getting revenue/expenses per period and category with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/analysis/revenue-expenses-per-period-and-category",
            json={
                "account_number": bank_account,
                "transaction_type": "EXPENSES",
                "start": "2023-01-01",
                "end": "2023-12-31",
                "grouping": "MONTH",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "periods" in data

    @pytest.mark.asyncio
    async def test_category_details_for_period_with_auth(self, authenticated_client, seed_bank_account):
        """Test getting category details with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/analysis/category-details-for-period",
            json={
                "account_number": bank_account,
                "transaction_type": "EXPENSES",
                "start": "2023-01-01",
                "end": "2023-12-31",
                "grouping": "MONTH",
                "category_qualified_name": "expenses",
            },
            headers=headers,
        )

        # Should succeed or return 404 if category not found
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_categories_for_account_with_auth(self, authenticated_client, seed_bank_account):
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
    async def test_track_budget_with_auth(self, authenticated_client, seed_bank_account):
        """Test tracking budget with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/analysis/track-budget",
            json={
                "account_number": bank_account,
                "transaction_type": "EXPENSES",
                "start": "2023-01-01",
                "end": "2023-12-31",
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


class TestResolveDateShortcutEndpoint:
    """Tests for the resolve_start_end_date_shortcut endpoint with all DateRangeShortcut values."""

    # Fixed date for consistent test results: January 15, 2026
    MOCK_TODAY = date(2026, 1, 15)

    @pytest.mark.asyncio
    async def test_resolve_current_month(self, authenticated_client):
        """Test resolving 'current month' returns correct date range."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        with patch("services.period_service.date") as mock_date:
            mock_date.today.return_value = self.MOCK_TODAY
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            response = await client.get(
                "/api/analysis/resolve-date-shortcut",
                params={"shortcut": "current month"},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "start" in data
        assert "end" in data
        assert data["shortcut"] == "current month"

        # Parse the dates and verify they are in January 2026
        start = date.fromisoformat(data["start"].replace("Z", "+00:00").replace("+00:00", ""))
        end = date.fromisoformat(data["end"].replace("Z", "+00:00").replace("+00:00", ""))

        # Start should be January 1, 2026 at start of day
        assert start.year == 2026
        assert start.month == 1
        assert start.day == 1
        # End should be January 31, 2026 at end of day
        assert end.year == 2026
        assert end.month == 1
        assert end.day == 31

    @pytest.mark.asyncio
    async def test_resolve_previous_month(self, authenticated_client):
        """Test resolving 'previous month' returns correct date range."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        with patch("services.period_service.date") as mock_date:
            mock_date.today.return_value = self.MOCK_TODAY
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            response = await client.get(
                "/api/analysis/resolve-date-shortcut",
                params={"shortcut": "previous month"},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["shortcut"] == "previous month"

        start = date.fromisoformat(data["start"].replace("Z", "+00:00").replace("+00:00", ""))
        end = date.fromisoformat(data["end"].replace("Z", "+00:00").replace("+00:00", ""))

        # Previous month (December 2025)
        assert start.year == 2025
        assert start.month == 12
        assert start.day == 1
        assert end.year == 2025
        assert end.month == 12
        assert end.day == 31

    @pytest.mark.asyncio
    async def test_resolve_current_quarter(self, authenticated_client):
        """Test resolving 'current quarter' returns correct date range."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        with patch("services.period_service.date") as mock_date:
            mock_date.today.return_value = self.MOCK_TODAY
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            response = await client.get(
                "/api/analysis/resolve-date-shortcut",
                params={"shortcut": "current quarter"},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["shortcut"] == "current quarter"

        start = date.fromisoformat(data["start"].replace("Z", "+00:00").replace("+00:00", ""))
        end = date.fromisoformat(data["end"].replace("Z", "+00:00").replace("+00:00", ""))

        # Q1 2026 (January - March)
        assert start.year == 2026
        assert start.month == 1
        assert start.day == 1
        assert end.year == 2026
        assert end.month == 3
        assert end.day == 31

    @pytest.mark.asyncio
    async def test_resolve_previous_quarter(self, authenticated_client):
        """Test resolving 'previous quarter' returns correct date range."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        with patch("services.period_service.date") as mock_date:
            mock_date.today.return_value = self.MOCK_TODAY
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            response = await client.get(
                "/api/analysis/resolve-date-shortcut",
                params={"shortcut": "previous quarter"},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["shortcut"] == "previous quarter"

        start = date.fromisoformat(data["start"].replace("Z", "+00:00").replace("+00:00", ""))
        end = date.fromisoformat(data["end"].replace("Z", "+00:00").replace("+00:00", ""))

        # Q4 2025 (October - December)
        assert start.year == 2025
        assert start.month == 10
        assert start.day == 1
        assert end.year == 2025
        assert end.month == 12
        assert end.day == 31

    @pytest.mark.asyncio
    async def test_resolve_current_year(self, authenticated_client):
        """Test resolving 'current year' returns correct date range."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        with patch("services.period_service.date") as mock_date:
            mock_date.today.return_value = self.MOCK_TODAY
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            response = await client.get(
                "/api/analysis/resolve-date-shortcut",
                params={"shortcut": "current year"},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["shortcut"] == "current year"

        start = date.fromisoformat(data["start"].replace("Z", "+00:00").replace("+00:00", ""))
        end = date.fromisoformat(data["end"].replace("Z", "+00:00").replace("+00:00", ""))

        # Year 2026
        assert start.year == 2026
        assert start.month == 1
        assert start.day == 1
        assert end.year == 2026
        assert end.month == 12
        assert end.day == 31

    @pytest.mark.asyncio
    async def test_resolve_previous_year(self, authenticated_client):
        """Test resolving 'previous year' returns correct date range."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        with patch("services.period_service.date") as mock_date:
            mock_date.today.return_value = self.MOCK_TODAY
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            response = await client.get(
                "/api/analysis/resolve-date-shortcut",
                params={"shortcut": "previous year"},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["shortcut"] == "previous year"

        start = date.fromisoformat(data["start"].replace("Z", "+00:00").replace("+00:00", ""))
        end = date.fromisoformat(data["end"].replace("Z", "+00:00").replace("+00:00", ""))

        # Year 2025
        assert start.year == 2025
        assert start.month == 1
        assert start.day == 1
        assert end.year == 2025
        assert end.month == 12
        assert end.day == 31

    @pytest.mark.asyncio
    async def test_resolve_all(self, authenticated_client):
        """Test resolving 'all' returns a wide date range."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/analysis/resolve-date-shortcut",
            params={"shortcut": "all"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["shortcut"] == "all"

        start = date.fromisoformat(data["start"].replace("Z", "+00:00").replace("+00:00", ""))
        end = date.fromisoformat(data["end"].replace("Z", "+00:00").replace("+00:00", ""))

        # 'all' should return a very wide range starting from 2000
        assert start.year == 2000
        assert start.month == 1
        assert start.day == 1
        # End should be today or later
        assert end.year >= 2026

    @pytest.mark.asyncio
    async def test_resolve_date_shortcut_returns_correct_structure(self, authenticated_client):
        """Test that the response structure matches ResolvedDateRange schema."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/analysis/resolve-date-shortcut",
            params={"shortcut": "current month"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        assert "start" in data
        assert "end" in data
        assert "shortcut" in data

        # Verify dates are in ISO format
        date.fromisoformat(data["start"].replace("Z", "+00:00").replace("+00:00", ""))
        date.fromisoformat(data["end"].replace("Z", "+00:00").replace("+00:00", ""))

    @pytest.mark.asyncio
    async def test_start_is_before_end(self, authenticated_client):
        """Test that start date is always before end date for all shortcuts."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        shortcuts = [
            "current month",
            "previous month",
            "current quarter",
            "previous quarter",
            "current year",
            "previous year",
            "all",
        ]

        for shortcut in shortcuts:
            response = await client.get(
                "/api/analysis/resolve-date-shortcut",
                params={"shortcut": shortcut},
                headers=headers,
            )

            assert response.status_code == 200, f"Failed for shortcut: {shortcut}"
            data = response.json()

            start = date.fromisoformat(data["start"].replace("Z", "+00:00").replace("+00:00", ""))
            end = date.fromisoformat(data["end"].replace("Z", "+00:00").replace("+00:00", ""))

            assert start < end, f"Start should be before end for shortcut: {shortcut}"
