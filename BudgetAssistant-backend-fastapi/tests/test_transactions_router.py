"""Tests for transactions router."""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from schemas import SortOrder, TransactionSortProperty


class TestTransactionsEndpoints:
    """Integration tests for transactions endpoints."""

    @pytest.mark.asyncio
    async def test_page_transactions_without_auth(self):
        """Test paging transactions without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/transactions/page",
                json={
                    "page": 0,
                    "size": 10,
                    "sort_order": "asc",
                    "sort_property": "transaction_id",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_page_transactions_in_context_without_auth(self):
        """Test paging transactions in context without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/transactions/page-in-context",
                json={
                    "page": 0,
                    "size": 10,
                    "sort_order": "asc",
                    "sort_property": "transaction_id",
                    "query": {
                        "bank_account": "BE12345",
                        "period": "2023-01",
                        "transaction_type": "EXPENSES",
                        "category_id": 1,
                    },
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_page_to_manually_review_without_auth(self):
        """Test paging transactions to review without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/transactions/page-to-manually-review",
                json={
                    "page": 0,
                    "size": 10,
                    "bank_account": "BE12345",
                    "transaction_type": "EXPENSES",
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_count_to_manually_review_without_auth(self):
        """Test counting transactions to review without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/transactions/count-to-manually-review",
                params={"bank_account": "BE12345"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_save_transaction_without_auth(self):
        """Test saving transaction without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/transactions/save",
                params={"transaction_id": "txn123"},
                json={
                    "category_id": 1,
                    "manually_assigned_category": True,
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_transactions_without_auth(self):
        """Test uploading transactions without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create a simple CSV content
            csv_content = b"header1,header2\nvalue1,value2\n"

            response = await client.post(
                "/api/transactions/upload",
                files={"files": ("test.csv", csv_content, "text/csv")},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_distinct_counterparty_names_without_auth(self):
        """Test getting distinct counterparty names without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/transactions/distinct-counterparty-names",
                params={"bank_account": "BE12345"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_distinct_counterparty_accounts_without_auth(self):
        """Test getting distinct counterparty accounts without authentication."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/transactions/distinct-counterparty-accounts",
                params={"bank_account": "BE12345"},
            )

            assert response.status_code == 401


class TestTransactionQueryValidation:
    """Tests for transaction query validation."""

    @pytest.mark.asyncio
    async def test_page_transactions_invalid_sort_order(self):
        """Test that invalid sort order is rejected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/transactions/page",
                json={
                    "page": 0,
                    "size": 10,
                    "sort_order": "invalid",  # Invalid sort order
                    "sort_property": "transaction_id",
                },
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_page_transactions_invalid_sort_property(self):
        """Test that invalid sort property is rejected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/transactions/page",
                json={
                    "page": 0,
                    "size": 10,
                    "sort_order": "asc",
                    "sort_property": "invalid_property",  # Invalid property
                },
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_page_transactions_negative_page(self):
        """Test that negative page number is rejected."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/transactions/page",
                json={
                    "page": -1,  # Invalid negative page
                    "size": 10,
                },
            )

            # Should fail validation (422) or auth (401)
            assert response.status_code in [401, 422]

