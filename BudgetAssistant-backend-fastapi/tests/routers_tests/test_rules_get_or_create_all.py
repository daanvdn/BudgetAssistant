"""Tests for the GET /rules/get-or-create-all endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from common.enums import TransactionTypeEnum
from main import app
from models import Category


class TestGetOrCreateAllRuleSetWrappersUnauthenticated:
    """Unauthenticated requests should be rejected."""

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/rules/get-or-create-all")
        assert response.status_code == 401


class TestGetOrCreateAllRuleSetWrappersAuthenticated:
    """Authenticated requests against an empty / seeded database."""

    @pytest.mark.asyncio
    async def test_returns_200_with_empty_db(self, authenticated_client):
        """With no categories the response should still be 200 with empty dicts."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.post("/api/rules/get-or-create-all", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "expenses_rules" in data
        assert "revenue_rules" in data
        assert isinstance(data["expenses_rules"], dict)
        assert isinstance(data["revenue_rules"], dict)

    @pytest.mark.asyncio
    async def test_returns_wrappers_for_seeded_categories(self, authenticated_client_with_session):
        """After seeding categories, endpoint returns matching wrappers."""
        client, access_token, session_maker = authenticated_client_with_session
        headers = {"Authorization": f"Bearer {access_token}"}

        # Seed categories directly in the DB
        async with session_maker() as session:
            root_exp = Category(
                name="Expenses",
                qualified_name="Expenses",
                is_root=True,
                type=TransactionTypeEnum.EXPENSES,
            )
            session.add(root_exp)
            await session.flush()

            groceries = Category(
                name="Groceries",
                qualified_name="Expenses > Groceries",
                is_root=False,
                type=TransactionTypeEnum.EXPENSES,
                parent_id=root_exp.id,
            )
            root_rev = Category(
                name="Revenue",
                qualified_name="Revenue",
                is_root=True,
                type=TransactionTypeEnum.REVENUE,
            )
            session.add_all([groceries, root_rev])
            await session.commit()

        response = await client.post("/api/rules/get-or-create-all", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # 2 expense categories, 1 revenue
        assert len(data["expenses_rules"]) == 2
        assert len(data["revenue_rules"]) == 1

        # Check keys are qualified names
        assert "Expenses" in data["expenses_rules"]
        assert "Expenses > Groceries" in data["expenses_rules"]
        assert "Revenue" in data["revenue_rules"]

    @pytest.mark.asyncio
    async def test_response_wrapper_shape(self, authenticated_client_with_session):
        """Each wrapper in the response contains the expected fields."""
        client, access_token, session_maker = authenticated_client_with_session
        headers = {"Authorization": f"Bearer {access_token}"}

        async with session_maker() as session:
            cat = Category(
                name="TestCat",
                qualified_name="TestCat",
                is_root=True,
                type=TransactionTypeEnum.EXPENSES,
            )
            session.add(cat)
            await session.commit()

        response = await client.post("/api/rules/get-or-create-all", headers=headers)
        assert response.status_code == 200

        wrapper = response.json()["expenses_rules"]["TestCat"]
        assert "id" in wrapper
        assert "category_id" in wrapper
        assert "rule_set" in wrapper
        assert isinstance(wrapper["rule_set"], dict)

    @pytest.mark.asyncio
    async def test_idempotent_call(self, authenticated_client_with_session):
        """Calling the endpoint twice returns the same wrapper IDs."""
        client, access_token, session_maker = authenticated_client_with_session
        headers = {"Authorization": f"Bearer {access_token}"}

        async with session_maker() as session:
            cat = Category(
                name="Idempotent",
                qualified_name="Idempotent",
                is_root=True,
                type=TransactionTypeEnum.EXPENSES,
            )
            session.add(cat)
            await session.commit()

        resp1 = await client.post("/api/rules/get-or-create-all", headers=headers)
        resp2 = await client.post("/api/rules/get-or-create-all", headers=headers)

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        id1 = resp1.json()["expenses_rules"]["Idempotent"]["id"]
        id2 = resp2.json()["expenses_rules"]["Idempotent"]["id"]
        assert id1 == id2
