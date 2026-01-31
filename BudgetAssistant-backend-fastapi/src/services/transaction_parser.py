"""Transaction parsing service for CSV file uploads."""

import csv
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.logging_utils import LoggerFactory
from models import BankAccount, Counterparty, Transaction, User
from models.associations import UserBankAccountLink, UserCounterpartyLink

logger = LoggerFactory.for_caller()


@dataclass
class ParseResult:
    """Result of parsing transaction file."""

    transactions: List[Transaction]
    created: int
    updated: int


class AbstractTransactionParser(ABC):
    """Abstract base class for transaction parsers."""

    @abstractmethod
    async def parse(self, lines: List[str], user: User, session: AsyncSession) -> ParseResult:
        """Parse transaction lines and return ParseResult."""
        ...

    @abstractmethod
    def get_type(self) -> str:
        """Get parser type identifier."""
        ...


class BelfiusTransactionParser(AbstractTransactionParser):
    """Parser for Belfius bank CSV transaction exports."""

    HEADERS = [
        "Rekening",
        "Boekingsdatum",
        "Rekeninguittrekselnummer",
        "Transactienummer",
        "Rekening tegenpartij",
        "Naam tegenpartij bevat",
        "Straat en nummer",
        "Postcode en plaats",
        "Transactie",
        "Valutadatum",
        "Bedrag",
        "Devies",
        "BIC",
        "Landcode",
        "Mededelingen",
    ]
    COLUMN_COUNT = len(HEADERS)
    SKIP_LINES = 12

    async def _get_or_create_bank_account(
        self,
        account_number: str,
        user: User,
        session: AsyncSession,
    ) -> BankAccount:
        """Get or create a bank account and associate it with the user."""
        normalized = BankAccount.normalize_account_number(account_number)

        # Check if bank account exists
        result = await session.execute(select(BankAccount).where(BankAccount.account_number == normalized))
        bank_account = result.scalar_one_or_none()

        if not bank_account:
            bank_account = BankAccount(account_number=normalized)
            session.add(bank_account)
            await session.flush()

        # Check if user is associated with this bank account
        link_result = await session.execute(
            select(UserBankAccountLink).where(
                UserBankAccountLink.user_id == user.id,
                UserBankAccountLink.bank_account_number == normalized,
            )
        )
        if not link_result.scalar_one_or_none():
            link = UserBankAccountLink(user_id=user.id, bank_account_number=normalized)
            session.add(link)

        return bank_account

    async def _get_or_create_counterparty(
        self,
        name: str,
        account_number: str,
        street_and_number: Optional[str],
        zip_code_and_city: Optional[str],
        user: User,
        session: AsyncSession,
    ) -> Counterparty:
        """Get or create a counterparty and associate it with the user."""
        # Normalize the name (use as-is but strip)
        name = name.strip() if name else "Unknown"

        # Check if counterparty exists
        result = await session.execute(select(Counterparty).where(Counterparty.name == name))
        counterparty = result.scalar_one_or_none()

        if not counterparty:
            counterparty = Counterparty(
                name=name,
                account_number=account_number or "",
                street_and_number=street_and_number,
                zip_code_and_city=zip_code_and_city,
            )
            session.add(counterparty)
            await session.flush()
        else:
            # Update counterparty if new info is available
            if account_number and not counterparty.account_number:
                counterparty.account_number = account_number
            if street_and_number and not counterparty.street_and_number:
                counterparty.street_and_number = street_and_number
            if zip_code_and_city and not counterparty.zip_code_and_city:
                counterparty.zip_code_and_city = zip_code_and_city

        # Check if user is associated with this counterparty
        link_result = await session.execute(
            select(UserCounterpartyLink).where(
                UserCounterpartyLink.user_id == user.id,
                UserCounterpartyLink.counterparty_name == name,
            )
        )
        if not link_result.scalar_one_or_none():
            link = UserCounterpartyLink(user_id=user.id, counterparty_name=name)
            session.add(link)

        return counterparty

    def _parse_date(self, date_str: str) -> date:
        """Parse date from string (DD/MM/YYYY format)."""
        try:
            return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
        except ValueError:
            # Try alternative format
            try:
                return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return date.today()

    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount from string (handles European number format)."""
        # Replace comma with dot for decimal, remove spaces
        cleaned = amount_str.strip().replace(",", ".").replace(" ", "")
        # Remove any thousand separators (in case of different formats)
        # Handle format like 1.234,56 -> 1234.56
        parts = cleaned.split(".")
        if len(parts) > 2:
            # Assume last part is decimal
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        return float(cleaned)

    async def _get_or_create_transaction(
        self,
        transaction_id: str,
        data: dict,
        upload_timestamp: datetime,
        session: AsyncSession,
    ) -> Tuple[Transaction, bool]:
        """Get or create a transaction. Returns (transaction, created)."""
        result = await session.execute(select(Transaction).where(Transaction.transaction_id == transaction_id))
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing transaction
            for key, value in data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            return existing, False

        # Create new transaction
        transaction = Transaction(
            transaction_id=transaction_id,
            upload_timestamp=upload_timestamp,
            **data,
        )
        session.add(transaction)
        return transaction, True

    async def parse(
        self,
        lines: List[str],
        user: User,
        session: AsyncSession,
        upload_timestamp: Optional[datetime] = None,
    ) -> ParseResult:
        """Parse Belfius CSV lines into transactions."""
        if upload_timestamp is None:
            upload_timestamp = datetime.now()

        # Skip header lines
        lines = lines[self.SKIP_LINES :]

        # Use CSV reader
        reader = csv.DictReader(lines, delimiter=";")

        # Validate headers
        actual_headers = reader.fieldnames
        if actual_headers and set(actual_headers) != set(self.HEADERS):
            logger.warning(f"Headers mismatch. Expected: {self.HEADERS}, Got: {actual_headers}")
            # Continue anyway if we have enough columns

        transactions = []
        created = 0
        updated = 0

        for row in reader:
            try:
                # Extract data from row
                bank_account_str = row.get("Rekening", "")
                bank_account = await self._get_or_create_bank_account(bank_account_str, user, session)

                counterparty_name = row.get("Naam tegenpartij bevat", "Unknown")
                counterparty_account = row.get("Rekening tegenpartij", "")
                street_and_number = row.get("Straat en nummer")
                zip_code_and_city = row.get("Postcode en plaats")

                counterparty = await self._get_or_create_counterparty(
                    counterparty_name,
                    counterparty_account,
                    street_and_number,
                    zip_code_and_city,
                    user,
                    session,
                )

                booking_date = self._parse_date(row.get("Boekingsdatum", ""))
                statement_number = row.get("Rekeninguittrekselnummer", "")
                transaction_number = row.get("Transactienummer", "")
                transaction_desc = row.get("Transactie", "")
                currency_date = self._parse_date(row.get("Valutadatum", ""))
                amount = self._parse_amount(row.get("Bedrag", "0"))
                currency = row.get("Devies", "EUR")
                bic = row.get("BIC")
                country_code = row.get("Landcode", "")
                communications = row.get("Mededelingen")

                # Create transaction ID
                transaction_id = Transaction.create_transaction_id(transaction_number, bank_account.account_number)

                data = {
                    "bank_account_id": bank_account.account_number,
                    "booking_date": booking_date,
                    "statement_number": statement_number,
                    "transaction_number": transaction_number,
                    "counterparty_id": counterparty.name,
                    "transaction": transaction_desc,
                    "currency_date": currency_date,
                    "amount": amount,
                    "currency": currency,
                    "bic": bic,
                    "country_code": country_code,
                    "communications": communications,
                }

                transaction, was_created = await self._get_or_create_transaction(
                    transaction_id, data, upload_timestamp, session
                )

                transactions.append(transaction)
                if was_created:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                logger.error(f"Error parsing row: {e}")
                continue

        await session.commit()

        logger.info(f"Parsed {len(transactions)} transactions")
        return ParseResult(transactions=transactions, created=created, updated=updated)

    def get_type(self) -> str:
        return "BELFIUS"


# Singleton instance
belfius_parser = BelfiusTransactionParser()
