"""Tests for common schemas."""

from datetime import date, datetime

import pytest
from enums import RecurrenceType, TransactionTypeEnum
from schemas.common import (
    CountResponse,
    DateRangeShortcut,
    ErrorResponse,
    Grouping,
    PageTransactionsRequest,
    PaginatedResponse,
    PaginationParams,
    RegisterUserRequest,
    ResolvedDateRange,
    RevenueExpensesQuery,
    SortOrder,
    SuccessResponse,
    TokenResponse,
    TransactionQuery,
    TransactionSortProperty,
    UploadTransactionsResponse,
)


class TestPaginatedResponse:
    """Tests for PaginatedResponse."""

    def test_create_paginated_response(self):
        """Test creating a paginated response."""
        content = [{"id": 1}, {"id": 2}]
        response = PaginatedResponse.create(
            content=content,
            page=0,
            size=10,
            total_elements=25,
        )

        assert response.content == content
        assert response.page == 0
        assert response.size == 10
        assert response.total_elements == 25
        assert response.total_pages == 3

    def test_paginated_response_total_pages_calculation(self):
        """Test total pages calculation."""
        # Exactly divisible
        response = PaginatedResponse.create(
            content=[],
            page=0,
            size=10,
            total_elements=30,
        )
        assert response.total_pages == 3

        # Not divisible
        response = PaginatedResponse.create(
            content=[],
            page=0,
            size=10,
            total_elements=31,
        )
        assert response.total_pages == 4

        # Empty
        response = PaginatedResponse.create(
            content=[],
            page=0,
            size=10,
            total_elements=0,
        )
        assert response.total_pages == 0


class TestPaginationParams:
    """Tests for PaginationParams."""

    def test_default_values(self):
        """Test default pagination values."""
        params = PaginationParams()
        assert params.page == 0
        assert params.size == 10
        assert params.sort_order == SortOrder.ASC
        assert params.sort_property == TransactionSortProperty.TRANSACTION_ID

    def test_custom_values(self):
        """Test custom pagination values."""
        params = PaginationParams(
            page=2,
            size=25,
            sort_order=SortOrder.DESC,
            sort_property=TransactionSortProperty.BOOKING_DATE,
        )
        assert params.page == 2
        assert params.size == 25
        assert params.sort_order == SortOrder.DESC
        assert params.sort_property == TransactionSortProperty.BOOKING_DATE


class TestTransactionQuery:
    """Tests for TransactionQuery."""

    def test_default_values(self):
        """Test default transaction query values."""
        query = TransactionQuery()
        assert query.transaction_type is None
        assert query.counterparty_name is None
        assert query.min_amount is None
        assert query.max_amount is None
        assert query.account_number is None
        assert query.manually_assigned_category is False

    def test_full_query(self):
        """Test transaction query with all fields."""
        start = date(2023, 1, 1)
        end = date(2023, 12, 31)
        timestamp = datetime.now()

        query = TransactionQuery(
            transaction_type=TransactionTypeEnum.EXPENSES,
            counterparty_name="Test",
            min_amount=-1000.0,
            max_amount=-10.0,
            account_number="12345",
            category_id=5,
            transaction_or_communication="groceries",
            counterparty_account_number="ACC001",
            start_date=start,
            end_date=end,
            upload_timestamp=timestamp,
            manually_assigned_category=True,
        )

        assert query.transaction_type == TransactionTypeEnum.EXPENSES
        assert query.counterparty_name == "Test"
        assert query.min_amount == -1000.0
        assert query.max_amount == -10.0
        assert query.account_number == "12345"
        assert query.category_id == 5
        assert query.manually_assigned_category is True


class TestPageTransactionsRequest:
    """Tests for PageTransactionsRequest."""

    def test_with_query(self):
        """Test page transactions request with query."""
        query = TransactionQuery(
            transaction_type=TransactionTypeEnum.REVENUE,
            account_number="12345",
        )
        request = PageTransactionsRequest(
            page=1,
            size=20,
            query=query,
        )

        assert request.page == 1
        assert request.size == 20
        assert request.query is not None
        assert request.query.transaction_type == TransactionTypeEnum.REVENUE

    def test_without_query(self):
        """Test page transactions request without query."""
        request = PageTransactionsRequest()
        assert request.query is None


class TestRevenueExpensesQuery:
    """Tests for RevenueExpensesQuery."""

    def test_is_empty_returns_true_for_empty_account(self):
        """Test is_empty returns True when account number is empty."""
        query = RevenueExpensesQuery(
            account_number="",
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=datetime.now(),
            end=datetime.now(),
            grouping=Grouping.MONTH,
        )
        assert query.is_empty() is True

    def test_is_empty_returns_false_for_valid_query(self):
        """Test is_empty returns False for valid query."""
        query = RevenueExpensesQuery(
            account_number="12345",
            transaction_type=TransactionTypeEnum.EXPENSES,
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31),
            grouping=Grouping.MONTH,
        )
        assert query.is_empty() is False

    def test_with_recurrence_filters(self):
        """Test query with recurrence filters."""
        query = RevenueExpensesQuery(
            account_number="12345",
            transaction_type=TransactionTypeEnum.BOTH,
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31),
            grouping=Grouping.QUARTER,
            revenue_recurrence=RecurrenceType.RECURRENT,
            expenses_recurrence=RecurrenceType.NON_RECURRENT,
        )

        assert query.revenue_recurrence == RecurrenceType.RECURRENT
        assert query.expenses_recurrence == RecurrenceType.NON_RECURRENT


class TestResponseSchemas:
    """Tests for response schemas."""

    def test_success_response(self):
        """Test SuccessResponse."""
        response = SuccessResponse(message="Operation successful")
        assert response.message == "Operation successful"
        assert response.status_code == 200

    def test_success_response_custom_status(self):
        """Test SuccessResponse with custom status."""
        response = SuccessResponse(message="Created", status_code=201)
        assert response.status_code == 201

    def test_error_response(self):
        """Test ErrorResponse."""
        response = ErrorResponse(error="Something went wrong", detail="More info")
        assert response.error == "Something went wrong"
        assert response.detail == "More info"
        assert response.status_code == 400

    def test_count_response(self):
        """Test CountResponse."""
        response = CountResponse(count=42)
        assert response.count == 42

    def test_upload_transactions_response(self):
        """Test UploadTransactionsResponse."""
        now = datetime.now()
        response = UploadTransactionsResponse(
            created=10,
            updated=5,
            upload_timestamp=now,
        )
        assert response.created == 10
        assert response.updated == 5
        assert response.upload_timestamp == now


class TestAuthSchemas:
    """Tests for authentication schemas."""

    def test_register_user_request(self):
        """Test RegisterUserRequest."""
        request = RegisterUserRequest(
            username="testuser",
            password="securepassword123",
            email="test@example.com",
        )
        assert request.username == "testuser"
        assert request.password == "securepassword123"
        assert request.email == "test@example.com"

    def test_register_user_request_validation(self):
        """Test RegisterUserRequest validation."""
        # Username too short
        with pytest.raises(ValueError):
            RegisterUserRequest(
                username="ab",  # Too short
                password="securepassword123",
                email="test@example.com",
            )

        # Password too short
        with pytest.raises(ValueError):
            RegisterUserRequest(
                username="testuser",
                password="short",  # Too short
                email="test@example.com",
            )

    def test_token_response(self):
        """Test TokenResponse."""
        response = TokenResponse(
            access_token="access123",
            refresh_token="refresh456",
        )
        assert response.access_token == "access123"
        assert response.refresh_token == "refresh456"
        assert response.token_type == "bearer"


class TestEnums:
    """Tests for enum schemas."""

    def test_sort_order_values(self):
        """Test SortOrder enum values."""
        assert SortOrder.ASC == "asc"
        assert SortOrder.DESC == "desc"

    def test_grouping_values(self):
        """Test Grouping enum values."""
        assert Grouping.DAY == "DAY"
        assert Grouping.WEEK == "WEEK"
        assert Grouping.MONTH == "MONTH"
        assert Grouping.QUARTER == "QUARTER"
        assert Grouping.YEAR == "YEAR"

    def test_date_range_shortcut_values(self):
        """Test DateRangeShortcut enum values."""
        assert DateRangeShortcut.CURRENT_MONTH == "current month"
        assert DateRangeShortcut.PREVIOUS_MONTH == "previous month"
        assert DateRangeShortcut.CURRENT_YEAR == "current year"
        assert DateRangeShortcut.ALL == "all"

    def test_transaction_sort_property_values(self):
        """Test TransactionSortProperty enum values."""
        assert TransactionSortProperty.TRANSACTION_ID == "transaction_id"
        assert TransactionSortProperty.BOOKING_DATE == "booking_date"
        assert TransactionSortProperty.AMOUNT == "amount"


class TestResolvedDateRange:
    """Tests for ResolvedDateRange."""

    def test_resolved_date_range(self):
        """Test ResolvedDateRange."""
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        resolved = ResolvedDateRange(
            start=start,
            end=end,
            shortcut="current year",
        )

        assert resolved.start == start
        assert resolved.end == end
        assert resolved.shortcut == "current year"
