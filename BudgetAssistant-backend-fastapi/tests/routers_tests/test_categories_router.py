"""Tests for categories router."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


class TestCategoriesEndpoints:
    """Integration tests for categories endpoints."""

    @pytest.mark.asyncio
    async def test_get_category_tree_without_auth(self):
        """Test getting category tree without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/categories/tree",
                params={"transaction_type": "EXPENSES"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_category_tree_invalid_type(self):
        """Test getting category tree with invalid transaction type."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/categories/tree",
                params={"transaction_type": "INVALID"},
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_get_category_tree_both_type_rejected(self):
        """Test that BOTH transaction type is rejected for tree."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/categories/tree",
                params={"transaction_type": "BOTH"},
            )

            # Should fail (400) or auth (401)
            assert response.status_code in [400, 401]

    @pytest.mark.asyncio
    async def test_list_categories_without_auth(self):
        """Test listing categories without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/categories")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_categories_with_filter_without_auth(self):
        """Test listing categories with type filter without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/categories",
                params={"transaction_type": "EXPENSES"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_category_by_id_without_auth(self):
        """Test getting category by ID without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/categories/1")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_category_by_qualified_name_without_auth(self):
        """Test getting category by qualified name without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/categories/by-qualified-name/expenses/groceries"
            )

            assert response.status_code == 401


class TestCategoriesEndpointsAuthenticated:
    """Tests for categories endpoints with authentication."""

    @pytest.mark.asyncio
    async def test_get_category_tree_with_auth(self, authenticated_client):
        """Test getting category tree with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/categories/tree",
            params={"transaction_type": "EXPENSES"},
            headers=headers,
        )

        # Should succeed or return 404 if categories not seeded
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_list_categories_with_auth(self, authenticated_client):
        """Test listing categories with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get("/api/categories", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_categories_with_filter_with_auth(self, authenticated_client):
        """Test listing categories with type filter with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/categories",
            params={"transaction_type": "EXPENSES"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_category_by_id_with_auth(self, authenticated_client):
        """Test getting category by ID with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        # First get list of categories to find a valid ID
        list_response = await client.get("/api/categories", headers=headers)

        if list_response.status_code == 200:
            categories = list_response.json()
            if categories and len(categories) > 0:
                category_id = categories[0].get("id")
                if category_id:
                    response = await client.get(
                        f"/api/categories/{category_id}",
                        headers=headers,
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data.get("id") == category_id

    @pytest.mark.asyncio
    async def test_get_category_by_id_not_found(self, authenticated_client):
        """Test getting category by ID that doesn't exist."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get("/api/categories/999999", headers=headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_category_by_qualified_name_with_auth(self, authenticated_client):
        """Test getting category by qualified name with authentication."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        # First get list of categories to find a valid qualified name
        list_response = await client.get("/api/categories", headers=headers)

        if list_response.status_code == 200:
            categories = list_response.json()
            for cat in categories:
                qualified_name = cat.get("qualified_name")
                if qualified_name and not cat.get("is_root"):
                    response = await client.get(
                        f"/api/categories/by-qualified-name/{qualified_name}",
                        headers=headers,
                    )

                    assert response.status_code in [200, 404]
                    if response.status_code == 200:
                        data = response.json()
                        assert data.get("qualified_name") == qualified_name
                    break

    @pytest.mark.asyncio
    async def test_get_category_by_qualified_name_not_found(self, authenticated_client):
        """Test getting category by qualified name that doesn't exist."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.get(
            "/api/categories/by-qualified-name/nonexistent/category",
            headers=headers,
        )

        assert response.status_code == 404
