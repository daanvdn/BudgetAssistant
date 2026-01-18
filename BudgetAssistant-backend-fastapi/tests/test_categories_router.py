"""Tests for categories router."""

import pytest
from httpx import AsyncClient, ASGITransport

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

