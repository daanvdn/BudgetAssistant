"""Pydantic schemas for API request/response."""

from .analysis import (
    BudgetEntryResult,
    BudgetTrackerResult,
    CategoriesForAccountResponse,
    CategoryAmount,
    CategoryDetailsForPeriodResponse,
    CategoryDetailsForPeriodResult,
    ExpensesAndRevenueForPeriod,
    PeriodCategoryBreakdown,
    RevenueAndExpensesPerPeriodAndCategory,
    RevenueAndExpensesPerPeriodResponse,
)
from .bank_account import BankAccountCreate, BankAccountRead, BankAccountUpdate
from .budget import (
    BudgetTreeCreate,
    BudgetTreeNodeCreate,
    BudgetTreeNodeRead,
    BudgetTreeNodeUpdate,
    BudgetTreeRead,
)
from .category import CategoryRead, CategoryTreeRead
from .common import (
    CategorizeTransactionsResponse,
    CountResponse,
    DateRangeShortcut,
    ErrorResponse,
    GetOrCreateRuleSetWrapperRequest,
    Grouping,
    PageTransactionsInContextRequest,
    PageTransactionsRequest,
    PageTransactionsToManuallyReviewRequest,
    PaginatedResponse,
    PaginationParams,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordUpdateRequest,
    RefreshTokenRequest,
    RegisterUserRequest,
    ResolvedDateRange,
    RevenueExpensesQuery,
    RevenueExpensesQueryWithCategory,
    SaveAliasRequest,
    SortOrder,
    SuccessResponse,
    TokenRequest,
    TokenResponse,
    TransactionInContextQuery,
    TransactionQuery,
    TransactionSortProperty,
    UploadTransactionsResponse,
    ValidateResetTokenResponse,
)
from .counterparty import CounterpartyCreate, CounterpartyRead, CounterpartyUpdate
from .period import (
    Month,
    Period,
    PeriodFromTransactionFactory,
    PeriodSchema,
    PeriodValueFormatter,
    Quarter,
    Year,
)
from .rule_set_wrapper import (
    RuleSetWrapperCreate,
    RuleSetWrapperRead,
    RuleSetWrapperUpdate,
)
from .transaction import TransactionCreate, TransactionRead, TransactionUpdate
from .user import UserCreate, UserRead, UserUpdate

__all__ = [
    # User schemas
    "UserCreate",
    "UserRead",
    "UserUpdate",
    # Bank account schemas
    "BankAccountCreate",
    "BankAccountRead",
    "BankAccountUpdate",
    # Counterparty schemas
    "CounterpartyCreate",
    "CounterpartyRead",
    "CounterpartyUpdate",
    # Category schemas
    "CategoryRead",
    "CategoryTreeRead",
    # Transaction schemas
    "TransactionCreate",
    "TransactionRead",
    "TransactionUpdate",
    # Budget schemas
    "BudgetTreeNodeCreate",
    "BudgetTreeNodeRead",
    "BudgetTreeNodeUpdate",
    "BudgetTreeCreate",
    "BudgetTreeRead",
    # Rule set wrapper schemas
    "RuleSetWrapperCreate",
    "RuleSetWrapperRead",
    "RuleSetWrapperUpdate",
    # Common schemas
    "PaginatedResponse",
    "SortOrder",
    "TransactionSortProperty",
    "Grouping",
    "PaginationParams",
    "TransactionQuery",
    "PageTransactionsRequest",
    "TransactionInContextQuery",
    "PageTransactionsInContextRequest",
    "PageTransactionsToManuallyReviewRequest",
    "RevenueExpensesQuery",
    "RevenueExpensesQueryWithCategory",
    "SuccessResponse",
    "ErrorResponse",
    "CountResponse",
    "UploadTransactionsResponse",
    "RegisterUserRequest",
    "TokenRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "GetOrCreateRuleSetWrapperRequest",
    "SaveAliasRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    "PasswordUpdateRequest",
    "CategorizeTransactionsResponse",
    "DateRangeShortcut",
    "ResolvedDateRange",
    "ValidateResetTokenResponse",
    # Analysis schemas
    "ExpensesAndRevenueForPeriod",
    "RevenueAndExpensesPerPeriodResponse",
    "CategoryAmount",
    "PeriodCategoryBreakdown",
    "RevenueAndExpensesPerPeriodAndCategory",
    "CategoryDetailsForPeriodResult",
    "CategoryDetailsForPeriodResponse",
    "BudgetEntryResult",
    "BudgetTrackerResult",
    "CategoriesForAccountResponse",
    # Period schemas
    "Period",
    "Month",
    "Quarter",
    "Year",
    "PeriodFromTransactionFactory",
    "PeriodValueFormatter",
    "PeriodSchema",
]
