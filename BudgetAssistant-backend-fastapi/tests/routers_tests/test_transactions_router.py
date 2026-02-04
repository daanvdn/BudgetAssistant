"""Tests for transactions router."""

import importlib.resources
from datetime import date

import factory
import pytest
from factory.alchemy import SQLAlchemyModelFactory
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from common.enums import TransactionTypeEnum
from main import app
from models import BankAccount, Category, Counterparty, Transaction, User
from models.associations import UserBankAccountLink


class BankAccountFactory(SQLAlchemyModelFactory):
    class Meta:
        model = BankAccount
        sqlalchemy_session = None

    account_number = factory.Sequence(lambda n: f"be{10000 + n}")
    alias = factory.Faker("word")


class CounterpartyFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Counterparty
        sqlalchemy_session = None

    name = factory.Sequence(lambda n: f"Counterparty {n}")
    account_number = factory.Sequence(lambda n: f"CP-{1000 + n}")


class CategoryFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Category
        sqlalchemy_session = None

    name = factory.Sequence(lambda n: f"Category {n}")
    qualified_name = factory.LazyAttribute(lambda obj: obj.name)
    type = TransactionTypeEnum.EXPENSES


class TransactionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Transaction
        sqlalchemy_session = None

    booking_date = date(2023, 1, 15)
    statement_number = factory.Sequence(lambda n: f"stmt-{n:03d}")
    transaction_number = factory.Sequence(lambda n: f"txn-{n:03d}")
    transaction = factory.Faker("sentence", nb_words=3)
    currency_date = date(2023, 1, 15)
    amount = factory.Sequence(lambda n: -10.0 - float(n))
    currency = "EUR"
    country_code = "BE"
    communications = factory.Faker("word")
    manually_assigned_category = False
    is_recurring = False
    is_advance_shared_account = False
    is_manually_reviewed = False

    transaction_id = factory.LazyAttribute(
        lambda obj: Transaction.create_transaction_id(
            obj.transaction_number,
            obj.bank_account_id,
        )
    )


async def seed_transaction_data(test_session_maker) -> dict:
    """Seed transactions with related entities and return lookup data."""
    account_number = "be12345"
    counterparty_name = "Acme Corp"
    counterparty_account = "CP-123"
    total_transactions = 20

    async with test_session_maker() as session:
        user_result = await session.execute(select(User).where(User.email == "testuser@example.com"))
        user = user_result.scalar_one()

        bank_account = BankAccountFactory.build(account_number=account_number, alias="Test Account")
        counterparty = CounterpartyFactory.build(
            name=counterparty_name,
            account_number=counterparty_account,
        )
        category = CategoryFactory.build(
            name="Food",
            qualified_name="Food",
            type=TransactionTypeEnum.EXPENSES,
        )

        session.add_all([bank_account, counterparty, category])
        await session.flush()

        session.add(
            UserBankAccountLink(
                user_id=user.id,
                bank_account_number=account_number,
            )
        )

        transactions = TransactionFactory.build_batch(
            total_transactions,
            bank_account_id=account_number,
            counterparty_id=counterparty.name,
            category_id=category.id,
        )

        session.add_all(transactions)
        await session.commit()

        return {
            "account_number": account_number,
            "category_id": category.id,
            "counterparty_name": counterparty_name,
            "counterparty_account": counterparty_account,
            "transaction_ids": [t.transaction_id for t in transactions],
            "count": total_transactions,
        }


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


class TestTransactionsEndpointsAuthenticated:
    """Tests for transactions endpoints with authentication."""

    @pytest.mark.asyncio
    async def test_page_transactions_with_auth(self, authenticated_client_with_session):
        """Test paging transactions with authentication."""
        client, access_token, test_session_maker = authenticated_client_with_session
        headers = {"Authorization": f"Bearer {access_token}"}
        seeded = await seed_transaction_data(test_session_maker)

        response = await client.post(
            "/api/transactions/page",
            json={
                "page": 0,
                "size": 10,
                "sort_order": "asc",
                "sort_property": "transaction_id",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "total_elements" in data
        assert data["total_elements"] == seeded["count"]
        assert len(data["content"]) == 10
        returned_ids = {item["transaction_id"] for item in data["content"]}
        assert returned_ids.issubset(set(seeded["transaction_ids"]))

    @pytest.mark.asyncio
    async def test_page_transactions_in_context_with_auth(self, authenticated_client_with_session):
        """Test paging transactions in context with authentication."""
        client, access_token, test_session_maker = authenticated_client_with_session
        headers = {"Authorization": f"Bearer {access_token}"}
        seeded = await seed_transaction_data(test_session_maker)

        response = await client.post(
            "/api/transactions/page-in-context",
            json={
                "page": 0,
                "size": 10,
                "sort_order": "asc",
                "sort_property": "transaction_id",
                "query": {
                    "bank_account": seeded["account_number"],
                    "period": "2023-01",
                    "transaction_type": "EXPENSES",
                    "category_id": seeded["category_id"],
                },
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["total_elements"] == seeded["count"]
        assert len(data["content"]) == 10
        returned_ids = {item["transaction_id"] for item in data["content"]}
        assert returned_ids.issubset(set(seeded["transaction_ids"]))
        assert all(item["category_id"] == seeded["category_id"] for item in data["content"])

    @pytest.mark.asyncio
    async def test_page_to_manually_review_with_auth(self, authenticated_client_with_session):
        """Test paging transactions to review with authentication."""
        client, access_token, test_session_maker = authenticated_client_with_session
        headers = {"Authorization": f"Bearer {access_token}"}
        seeded = await seed_transaction_data(test_session_maker)

        response = await client.post(
            "/api/transactions/page-to-manually-review",
            json={
                "page": 0,
                "size": 10,
                "bank_account": seeded["account_number"],
                "transaction_type": "EXPENSES",
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["total_elements"] == seeded["count"]
        assert len(data["content"]) == 10
        returned_ids = {item["transaction_id"] for item in data["content"]}
        assert returned_ids.issubset(set(seeded["transaction_ids"]))
        assert all(item["is_manually_reviewed"] is False for item in data["content"])

    @pytest.mark.asyncio
    async def test_count_to_manually_review_with_auth(self, authenticated_client_with_session):
        """Test counting transactions to review with authentication."""
        client, access_token, test_session_maker = authenticated_client_with_session
        headers = {"Authorization": f"Bearer {access_token}"}
        seeded = await seed_transaction_data(test_session_maker)

        response = await client.get(
            "/api/transactions/count-to-manually-review",
            params={"bank_account": seeded["account_number"]},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert data["count"] == seeded["count"]

    @pytest.mark.asyncio
    async def test_distinct_counterparty_names_with_auth(self, authenticated_client_with_session):
        """Test getting distinct counterparty names with authentication."""
        client, access_token, test_session_maker = authenticated_client_with_session
        headers = {"Authorization": f"Bearer {access_token}"}
        seeded = await seed_transaction_data(test_session_maker)

        response = await client.get(
            "/api/transactions/distinct-counterparty-names",
            params={"bank_account": seeded["account_number"]},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert seeded["counterparty_name"] in data

    @pytest.mark.asyncio
    async def test_distinct_counterparty_accounts_with_auth(self, authenticated_client_with_session):
        """Test getting distinct counterparty accounts with authentication."""
        client, access_token, test_session_maker = authenticated_client_with_session
        headers = {"Authorization": f"Bearer {access_token}"}
        seeded = await seed_transaction_data(test_session_maker)

        response = await client.get(
            "/api/transactions/distinct-counterparty-accounts",
            params={"bank_account": seeded["account_number"]},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert seeded["counterparty_account"] in data

    @pytest.mark.asyncio
    async def test_upload_transactions_with_auth(self, authenticated_client_with_session):
        """Test uploading transactions with authentication."""
        client, access_token, test_session_maker = authenticated_client_with_session
        headers = {"Authorization": f"Bearer {access_token}"}
        resource = importlib.resources.files("resources").joinpath("belfius_transactions_2.csv")
        with resource.open(mode="rb") as f:
            csv_content = f.read()
            # convert to string and split lines
            csv_content_lines = csv_content.decode("utf-8").splitlines()
            # remove any empty line from csv_content_lines
            csv_content_lines = [csv_content for csv_content in csv_content_lines if csv_content]
            # remove first line (header)
            csv_content_lines = csv_content_lines[1:]

        response = await client.post(
            "/api/transactions/upload",
            files={"files": ("test.csv", csv_content, "text/csv")},
            headers=headers,
        )

        # Should succeed or return error depending on CSV format validation
        assert response.status_code == 200
        # query the database to ensure that the correct number of transactions were added
        from sqlmodel import select

        from models import Transaction

        async with test_session_maker() as session:
            result = await session.execute(select(Transaction))
            transactions = result.scalars().all()
            assert len(transactions) == len(csv_content_lines)

    @pytest.mark.asyncio
    async def test_save_transaction_with_auth_not_found(self, authenticated_client):
        """Test saving transaction that doesn't exist."""
        client, access_token = authenticated_client
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await client.post(
            "/api/transactions/save",
            params={"transaction_id": "nonexistent-txn-id"},
            json={
                "category_id": 1,
                "manually_assigned_category": True,
            },
            headers=headers,
        )

        # Should be 404 (not found)
        assert response.status_code == 404
