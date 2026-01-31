"""Tests for rules router."""

import pytest
from httpx import ASGITransport, AsyncClient
from main import app


class TestRulesEndpointsUnauthenticated:
    """Tests for rules endpoints without authentication."""

    @pytest.mark.asyncio
    async def test_get_or_create_rule_set_without_auth(self):
        """Test getting/creating rule set without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/rules/get-or-create",
                json={
                    "category_qualified_name": "expenses/groceries",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_save_rule_set_without_auth(self):
        """Test saving rule set without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/rules/save",
                json={
                    "category_id": 1,
                    "rule_set": {"rules": []},
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_rule_set_without_auth(self):
        """Test updating rule set without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/rules/1",
                json={
                    "rule_set": {"rules": []},
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_rule_set_without_auth(self):
        """Test getting rule set without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/rules/1")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_categorize_transactions_without_auth(self):
        """Test categorizing transactions without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/rules/categorize-transactions",
                params={
                    "bank_account": "BE68539007547034",
                    "transaction_type": "EXPENSES",
                },
            )

            assert response.status_code == 401


class TestRulesEndpointsAuthenticated:
    """Tests for rules endpoints with authentication."""

    @pytest.mark.asyncio
    async def test_get_or_create_rule_set_with_auth_not_found(
        self, authenticated_client
    ):
        """Test getting/creating rule set for non-existent category."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.post(
            "/api/rules/get-or-create",
            json={
                "category_qualified_name": "nonexistent/category",
                "type": "EXPENSES",
            },
            headers=headers,
        )

        # Should be 404 (not found) for non-existent category
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_or_create_rule_set_with_auth_valid(self, authenticated_client):
        """Test getting/creating rule set for valid category."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        # First get available categories
        categories_response = await client.get("/api/categories", headers=headers)

        if categories_response.status_code == 200:
            categories = categories_response.json()
            if categories and len(categories) > 0:
                # Find a non-root category with qualified name
                for cat in categories:
                    if cat.get("qualified_name") and not cat.get("is_root"):
                        response = await client.post(
                            "/api/rules/get-or-create",
                            json={
                                "category_qualified_name": cat["qualified_name"],
                            },
                            headers=headers,
                        )

                        assert response.status_code in [200, 404]
                        if response.status_code == 200:
                            data = response.json()
                            assert "id" in data
                            assert "category_id" in data
                            assert "rule_set" in data
                        break

    @pytest.mark.asyncio
    async def test_save_rule_set_with_auth_invalid_category(self, authenticated_client):
        """Test saving rule set with invalid category ID."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.post(
            "/api/rules/save",
            json={
                "category_id": 999999,
                "rule_set": {"rules": []},
            },
            headers=headers,
        )

        # Should be 404 (not found) for non-existent category
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_rule_set_with_auth_not_found(self, authenticated_client):
        """Test updating rule set that doesn't exist."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.patch(
            "/api/rules/999999",
            json={
                "rule_set": {"rules": []},
            },
            headers=headers,
        )

        # Should be 404 (not found)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_rule_set_with_auth_not_found(self, authenticated_client):
        """Test getting rule set that doesn't exist."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/rules/999999",
            headers=headers,
        )

        # Should be 404 (not found)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_categorize_transactions_with_auth(
        self, authenticated_client, seed_bank_account
    ):
        """Test categorizing transactions with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}
        bank_account = seed_bank_account

        response = await client.post(
            "/api/rules/categorize-transactions",
            params={
                "bank_account": bank_account,
                "transaction_type": "EXPENSES",
            },
            headers=headers,
        )

        # Should succeed (returns placeholder response)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "with_category_count" in data
        assert "without_category_count" in data


class TestRulesValidation:
    """Tests for rules endpoint validation."""

    @pytest.mark.asyncio
    async def test_get_or_create_rule_set_missing_category(self):
        """Test getting/creating rule set with missing category name."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/rules/get-or-create",
                json={},
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_save_rule_set_missing_category_id(self):
        """Test saving rule set with missing category ID."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/rules/save",
                json={
                    "rule_set": {"rules": []},
                },
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_categorize_transactions_invalid_type(self):
        """Test categorizing transactions with invalid transaction type."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/rules/categorize-transactions",
                params={
                    "bank_account": "BE68539007547034",
                    "transaction_type": "INVALID",
                },
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]
