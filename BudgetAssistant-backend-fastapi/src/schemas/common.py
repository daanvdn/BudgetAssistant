"""Common Pydantic schemas for API operations."""

from datetime import date, datetime
from enum import Enum
from typing import Generic, List, Optional, TypeVar

from enums import RecurrenceType, TransactionTypeEnum
from pydantic import BaseModel, Field

# Generic type for paginated responses
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""

    content: List[T]
    page: int = Field(ge=0, description="Current page number (0-indexed)")
    size: int = Field(ge=1, description="Number of items per page")
    total_elements: int = Field(ge=0, description="Total number of elements")
    total_pages: int = Field(ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls, content: List[T], page: int, size: int, total_elements: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response from content and pagination info."""
        total_pages = (total_elements + size - 1) // size if size > 0 else 0
        return cls(
            content=content,
            page=page,
            size=size,
            total_elements=total_elements,
            total_pages=total_pages,
        )


class SortOrder(str, Enum):
    """Sort order enum."""

    ASC = "asc"
    DESC = "desc"


class TransactionSortProperty(str, Enum):
    """Valid sort properties for transactions."""

    TRANSACTION_ID = "transaction_id"
    BOOKING_DATE = "booking_date"
    AMOUNT = "amount"
    COUNTERPARTY = "counterparty"
    CATEGORY = "category"
    MANUALLY_ASSIGNED_CATEGORY = "manually_assigned_category"
    IS_RECURRING = "is_recurring"
    IS_ADVANCE_SHARED_ACCOUNT = "is_advance_shared_account"
    UPLOAD_TIMESTAMP = "upload_timestamp"
    IS_MANUALLY_REVIEWED = "is_manually_reviewed"
    TRANSACTION = "transaction"


class Grouping(str, Enum):
    """Grouping options for analysis."""

    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"


class PaginationParams(BaseModel):
    """Base pagination parameters."""

    page: int = Field(default=0, ge=0, description="Page number (0-indexed)")
    size: int = Field(default=10, ge=1, le=100, description="Page size")
    sort_order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")
    sort_property: TransactionSortProperty = Field(
        default=TransactionSortProperty.TRANSACTION_ID, description="Sort property"
    )


class TransactionQuery(BaseModel):
    """Query parameters for filtering transactions."""

    transaction_type: Optional[TransactionTypeEnum] = None
    counterparty_name: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    account_number: Optional[str] = None
    category_id: Optional[int] = None
    transaction_or_communication: Optional[str] = None
    counterparty_account_number: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    upload_timestamp: Optional[datetime] = None
    manually_assigned_category: bool = False


class PageTransactionsRequest(PaginationParams):
    """Request schema for paginated transactions."""

    query: Optional[TransactionQuery] = None


class TransactionInContextQuery(BaseModel):
    """Query for transactions in a specific context."""

    bank_account: str
    period: str
    transaction_type: TransactionTypeEnum
    category_id: int


class PageTransactionsInContextRequest(PaginationParams):
    """Request schema for paginated transactions in context."""

    query: TransactionInContextQuery


class PageTransactionsToManuallyReviewRequest(PaginationParams):
    """Request schema for transactions needing manual review."""

    bank_account: str
    transaction_type: TransactionTypeEnum


class RevenueExpensesQuery(BaseModel):
    """Query for revenue and expenses analysis."""

    account_number: str
    transaction_type: TransactionTypeEnum
    start: datetime
    end: datetime
    grouping: Grouping
    revenue_recurrence: Optional[RecurrenceType] = None
    expenses_recurrence: Optional[RecurrenceType] = None

    def is_empty(self) -> bool:
        """Check if query is effectively empty."""
        return not self.account_number or not self.start or not self.end


class RevenueExpensesQueryWithCategory(RevenueExpensesQuery):
    """Query for revenue and expenses with category filter."""

    category_qualified_name: str


class SuccessResponse(BaseModel):
    """Generic success response."""

    message: str
    status_code: int = 200


class ErrorResponse(BaseModel):
    """Generic error response."""

    error: str
    detail: Optional[str] = None
    status_code: int = 400


class CountResponse(BaseModel):
    """Response containing a count."""

    count: int


class UploadTransactionsResponse(BaseModel):
    """Response for transaction upload."""

    created: int = 0
    updated: int = 0
    upload_timestamp: datetime


class RegisterUserRequest(BaseModel):
    """Request schema for user registration."""

    username: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=8)
    email: str


class TokenRequest(BaseModel):
    """Request schema for token authentication."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Response schema for token authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str


class GetOrCreateRuleSetWrapperRequest(BaseModel):
    """Request to get or create a rule set wrapper."""

    category_qualified_name: str
    type: TransactionTypeEnum


class SaveAliasRequest(BaseModel):
    """Request to save a bank account alias."""

    alias: str
    bank_account: str


class PasswordResetRequest(BaseModel):
    """Request for password reset."""

    email: str


class PasswordResetConfirmRequest(BaseModel):
    """Request to confirm password reset."""

    token: str
    new_password: str = Field(min_length=8)


class PasswordUpdateRequest(BaseModel):
    """Request to update password."""

    password: Optional[str] = Field(default=None, min_length=8)
    email: Optional[str] = None


class CategorizeTransactionsResponse(BaseModel):
    """Response for categorize transactions operation."""

    message: str
    with_category_count: int
    without_category_count: int


class DateRangeShortcut(str, Enum):
    """Date range shortcut options."""

    CURRENT_MONTH = "current month"
    PREVIOUS_MONTH = "previous month"
    CURRENT_QUARTER = "current quarter"
    PREVIOUS_QUARTER = "previous quarter"
    CURRENT_YEAR = "current year"
    PREVIOUS_YEAR = "previous year"
    ALL = "all"


class ResolvedDateRange(BaseModel):
    """Resolved date range from shortcut."""

    start: datetime
    end: datetime
    shortcut: str
