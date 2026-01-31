"""Tests for Transaction model."""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from common.enums import TransactionTypeEnum
from models import BankAccount, Category, Counterparty, Transaction
from tests.utils import assert_persisted


class TestTransaction:
    """Test cases for the Transaction model."""

    @pytest.mark.asyncio
    async def test_create_transaction_with_valid_data(self, async_session):
        """Test creating a transaction with valid data."""
        # Setup dependencies
        bank_account = BankAccount(account_number="123456", alias="Savings")
        counterparty = Counterparty(name="counterparty1", account_number="ACC001")
        category = Category(
            name="Category1",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="Category1",
        )
        async_session.add_all([bank_account, counterparty, category])
        await async_session.commit()
        await async_session.refresh(category)

        transaction_id = Transaction.create_transaction_id(
            "txn_num_001", bank_account.account_number
        )

        transaction = Transaction(
            transaction_id=transaction_id,
            bank_account_id=bank_account.account_number,
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty_id=counterparty.name,
            transaction_number="txn_num_001",
            transaction="Test Transaction",
            currency_date=date(2023, 10, 1),
            amount=100.0,
            currency="USD",
            bic="BIC123",
            country_code="US",
            communications="Test communication",
            category_id=category.id,
        )

        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        assert transaction.transaction_id == transaction_id
        assert transaction.bank_account_id == bank_account.account_number
        assert transaction.counterparty_id == counterparty.name
        assert transaction.category_id == category.id

        # Re-query from database to verify persistence and foreign key relationships
        await assert_persisted(
            async_session,
            Transaction,
            "transaction_id",
            transaction_id,
            {
                "transaction_id": transaction_id,
                "bank_account_id": bank_account.account_number,
                "counterparty_id": counterparty.name,
                "category_id": category.id,
                "booking_date": date(2023, 10, 1),
                "statement_number": "stmt_001",
                "transaction_number": "txn_num_001",
                "transaction": "Test Transaction",
                "currency_date": date(2023, 10, 1),
                "amount": 100.0,
                "currency": "USD",
                "bic": "BIC123",
                "country_code": "US",
                "communications": "Test communication",
            },
        )

    @pytest.mark.asyncio
    async def test_create_transaction_with_duplicate_transaction_number(
        self, async_session
    ):
        """Test that duplicate transaction numbers raise an error."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        counterparty = Counterparty(name="counterparty1", account_number="ACC001")
        async_session.add_all([bank_account, counterparty])
        await async_session.commit()

        transaction1 = Transaction(
            transaction_id=Transaction.create_transaction_id(
                "txn_num_001", bank_account.account_number
            ),
            bank_account_id=bank_account.account_number,
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty_id=counterparty.name,
            transaction_number="txn_num_001",
            currency_date=date(2023, 10, 1),
            amount=100.0,
            currency="USD",
            country_code="US",
        )
        async_session.add(transaction1)
        await async_session.commit()

        transaction2 = Transaction(
            transaction_id=Transaction.create_transaction_id(
                "txn_num_001", bank_account.account_number
            ),
            bank_account_id=bank_account.account_number,
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty_id=counterparty.name,
            transaction_number="txn_num_001",
            currency_date=date(2023, 10, 1),
            amount=100.0,
            currency="USD",
            country_code="US",
        )
        async_session.add(transaction2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_get_transaction_type_returns_revenue_for_positive_amount(
        self, async_session
    ):
        """Test that positive amounts return REVENUE transaction type."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        counterparty = Counterparty(name="counterparty1", account_number="ACC001")
        async_session.add_all([bank_account, counterparty])
        await async_session.commit()

        transaction = Transaction(
            transaction_id=Transaction.create_transaction_id(
                "txn_num_001", bank_account.account_number
            ),
            bank_account_id=bank_account.account_number,
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty_id=counterparty.name,
            transaction_number="txn_num_001",
            currency_date=date(2023, 10, 1),
            amount=100.0,
            currency="USD",
            country_code="US",
        )

        assert transaction.get_transaction_type() == TransactionTypeEnum.REVENUE

    @pytest.mark.asyncio
    async def test_get_transaction_type_returns_expenses_for_negative_amount(
        self, async_session
    ):
        """Test that negative amounts return EXPENSES transaction type."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        counterparty = Counterparty(name="counterparty1", account_number="ACC001")
        async_session.add_all([bank_account, counterparty])
        await async_session.commit()

        transaction = Transaction(
            transaction_id=Transaction.create_transaction_id(
                "txn_num_001", bank_account.account_number
            ),
            bank_account_id=bank_account.account_number,
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty_id=counterparty.name,
            transaction_number="txn_num_001",
            currency_date=date(2023, 10, 1),
            amount=-100.0,
            currency="USD",
            country_code="US",
        )

        assert transaction.get_transaction_type() == TransactionTypeEnum.EXPENSES

    @pytest.mark.asyncio
    async def test_filter_transactions_by_amount(self, async_session):
        """Test filtering transactions by amount."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        counterparty = Counterparty(name="counterparty1", account_number="ACC001")
        bank_account2 = BankAccount(account_number="123457", alias="Checking")
        counterparty2 = Counterparty(name="counterparty2", account_number="ACC002")
        async_session.add_all(
            [bank_account, counterparty, bank_account2, counterparty2]
        )
        await async_session.commit()

        transaction1 = Transaction(
            transaction_id=Transaction.create_transaction_id(
                "txn_num_001", bank_account.account_number
            ),
            bank_account_id=bank_account.account_number,
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty_id=counterparty.name,
            transaction_number="txn_num_001",
            currency_date=date(2023, 10, 1),
            amount=100.0,
            currency="USD",
            country_code="US",
        )

        transaction2 = Transaction(
            transaction_id=Transaction.create_transaction_id(
                "txn_num_002", bank_account2.account_number
            ),
            bank_account_id=bank_account2.account_number,
            booking_date=date(2023, 10, 1),
            statement_number="stmt_002",
            counterparty_id=counterparty2.name,
            transaction_number="txn_num_002",
            currency_date=date(2023, 10, 1),
            amount=50.0,
            currency="USD",
            country_code="US",
        )

        async_session.add_all([transaction1, transaction2])
        await async_session.commit()

        # Filter transactions with amount >= 100 for bank_account
        result = await async_session.execute(
            select(Transaction).where(
                Transaction.amount >= 100.0,
                Transaction.bank_account_id == bank_account.account_number,
            )
        )
        transactions = result.scalars().all()

        assert len(transactions) == 1
        assert transactions[0].transaction_id == transaction1.transaction_id

    @pytest.mark.asyncio
    async def test_has_category(self, async_session):
        """Test has_category method."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        counterparty = Counterparty(name="counterparty1", account_number="ACC001")
        category = Category(
            name="Category1",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="Category1",
        )
        async_session.add_all([bank_account, counterparty, category])
        await async_session.commit()
        await async_session.refresh(category)

        # Transaction with category
        transaction_with_cat = Transaction(
            transaction_id=Transaction.create_transaction_id(
                "txn_num_001", bank_account.account_number
            ),
            bank_account_id=bank_account.account_number,
            booking_date=date(2023, 10, 1),
            statement_number="stmt_001",
            counterparty_id=counterparty.name,
            transaction_number="txn_num_001",
            currency_date=date(2023, 10, 1),
            amount=100.0,
            currency="USD",
            country_code="US",
            category_id=category.id,
        )

        # Transaction without category
        transaction_without_cat = Transaction(
            transaction_id=Transaction.create_transaction_id(
                "txn_num_002", bank_account.account_number
            ),
            bank_account_id=bank_account.account_number,
            booking_date=date(2023, 10, 1),
            statement_number="stmt_002",
            counterparty_id=counterparty.name,
            transaction_number="txn_num_002",
            currency_date=date(2023, 10, 1),
            amount=50.0,
            currency="USD",
            country_code="US",
        )

        assert transaction_with_cat.has_category() is True
        assert transaction_without_cat.has_category() is False

    def test_create_transaction_id_is_deterministic(self):
        """Test that create_transaction_id produces consistent results."""
        id1 = Transaction.create_transaction_id("txn123", "account456")
        id2 = Transaction.create_transaction_id("txn123", "account456")

        assert id1 == id2
        assert len(id1) == 64  # SHA256 truncated to 64 chars

    def test_create_transaction_id_is_unique_for_different_inputs(self):
        """Test that different inputs produce different transaction IDs."""
        id1 = Transaction.create_transaction_id("txn123", "account456")
        id2 = Transaction.create_transaction_id("txn124", "account456")
        id3 = Transaction.create_transaction_id("txn123", "account457")

        assert id1 != id2
        assert id1 != id3
        assert id2 != id3
