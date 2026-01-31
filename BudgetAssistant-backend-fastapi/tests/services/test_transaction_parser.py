"""Tests for transaction parser service."""

import pytest
from datetime import date
from services.transaction_parser import BelfiusTransactionParser


class TestBelfiusTransactionParser:
    """Tests for BelfiusTransactionParser class."""

    def test_parse_date_standard_format(self):
        """Test parsing date in DD/MM/YYYY format."""
        parser = BelfiusTransactionParser()
        result = parser._parse_date("15/03/2023")

        assert result == date(2023, 3, 15)

    def test_parse_date_iso_format(self):
        """Test parsing date in YYYY-MM-DD format."""
        parser = BelfiusTransactionParser()
        result = parser._parse_date("2023-03-15")

        assert result == date(2023, 3, 15)

    def test_parse_date_invalid_returns_today(self):
        """Test that invalid date returns today's date."""
        parser = BelfiusTransactionParser()
        result = parser._parse_date("invalid-date")

        assert result == date.today()

    def test_parse_amount_standard(self):
        """Test parsing standard amount."""
        parser = BelfiusTransactionParser()
        result = parser._parse_amount("123.45")

        assert result == 123.45

    def test_parse_amount_european_format(self):
        """Test parsing amount with European format (comma as decimal)."""
        parser = BelfiusTransactionParser()
        result = parser._parse_amount("123,45")

        assert result == 123.45

    def test_parse_amount_negative(self):
        """Test parsing negative amount."""
        parser = BelfiusTransactionParser()
        result = parser._parse_amount("-50.00")

        assert result == -50.0

    def test_parse_amount_with_spaces(self):
        """Test parsing amount with spaces."""
        parser = BelfiusTransactionParser()
        result = parser._parse_amount(" 100,50 ")

        assert result == 100.50

    def test_get_type(self):
        """Test get_type returns correct parser type."""
        parser = BelfiusTransactionParser()

        assert parser.get_type() == "BELFIUS"

    def test_headers_defined(self):
        """Test that expected headers are defined."""
        parser = BelfiusTransactionParser()

        assert "Rekening" in parser.HEADERS
        assert "Boekingsdatum" in parser.HEADERS
        assert "Bedrag" in parser.HEADERS
        assert "Naam tegenpartij bevat" in parser.HEADERS
        assert len(parser.HEADERS) == 15

    def test_skip_lines_defined(self):
        """Test that skip lines is defined correctly."""
        parser = BelfiusTransactionParser()

        assert parser.SKIP_LINES == 12


class TestBelfiusTransactionParserAsync:
    """Async tests for BelfiusTransactionParser requiring database."""

    @pytest.mark.asyncio
    async def test_parse_empty_file(self, async_session):
        """Test parsing an empty file after headers."""
        from models import User

        # Create a test user first
        user = User(
            username="testuser", email="test@example.com", password_hash="$2b$12$test"
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        parser = BelfiusTransactionParser()

        # Create empty file content (just 12 skip lines + header)
        lines = [""] * 12 + [
            "Rekening;Boekingsdatum;Rekeninguittrekselnummer;Transactienummer;Rekening tegenpartij;Naam tegenpartij bevat;Straat en nummer;Postcode en plaats;Transactie;Valutadatum;Bedrag;Devies;BIC;Landcode;Mededelingen"
        ]

        result = await parser.parse(lines, user, async_session)

        assert result.created == 0
        assert result.updated == 0
        assert len(result.transactions) == 0

    @pytest.mark.asyncio
    async def test_parse_single_transaction(self, async_session):
        """Test parsing a file with a single transaction."""
        from models import User

        # Create a test user
        user = User(
            username="testuser2", email="test2@example.com", password_hash="$2b$12$test"
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        parser = BelfiusTransactionParser()

        # Create file content with one transaction
        header = "Rekening;Boekingsdatum;Rekeninguittrekselnummer;Transactienummer;Rekening tegenpartij;Naam tegenpartij bevat;Straat en nummer;Postcode en plaats;Transactie;Valutadatum;Bedrag;Devies;BIC;Landcode;Mededelingen"
        transaction = "BE68539007547034;15/03/2023;001;TXN001;BE12345678901234;Test Counterparty;Street 1;1000 Brussels;Test Transaction;15/03/2023;-50,00;EUR;GKCCBEBB;BE;Test communication"

        lines = [""] * 12 + [header, transaction]

        result = await parser.parse(lines, user, async_session)

        assert result.created == 1
        assert result.updated == 0
        assert len(result.transactions) == 1

        txn = result.transactions[0]
        assert txn.amount == -50.0
        assert txn.currency == "EUR"
        assert txn.counterparty_id == "Test Counterparty"
