"""Pydantic schemas for API request/response."""

from .user import UserCreate, UserRead, UserUpdate
from .bank_account import BankAccountCreate, BankAccountRead, BankAccountUpdate
from .counterparty import CounterpartyCreate, CounterpartyRead, CounterpartyUpdate
from .category import CategoryRead, CategoryTreeRead
from .transaction import TransactionCreate, TransactionRead, TransactionUpdate
from .budget import (
    BudgetTreeNodeCreate,
    BudgetTreeNodeRead,
    BudgetTreeNodeUpdate,
    BudgetTreeCreate,
    BudgetTreeRead,
)
from .rule_set_wrapper import (
    RuleSetWrapperCreate,
    RuleSetWrapperRead,
    RuleSetWrapperUpdate,
)
from .common import (
    PaginatedResponse,
    SortOrder,
    TransactionSortProperty,
    Grouping,
    PaginationParams,
    TransactionQuery,
    PageTransactionsRequest,
    TransactionInContextQuery,
    PageTransactionsInContextRequest,
    PageTransactionsToManuallyReviewRequest,
    RevenueExpensesQuery,
    RevenueExpensesQueryWithCategory,
    SuccessResponse,
    ErrorResponse,
    CountResponse,
    UploadTransactionsResponse,
    RegisterUserRequest,
    TokenRequest,
    TokenResponse,
    RefreshTokenRequest,
    GetOrCreateRuleSetWrapperRequest,
    SaveAliasRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    PasswordUpdateRequest,
    CategorizeTransactionsResponse,
    DateRangeShortcut,
    ResolvedDateRange,
)
from .analysis import (
    ExpensesAndRevenueForPeriod,
    RevenueAndExpensesPerPeriodResponse,
    CategoryAmount,
    PeriodCategoryBreakdown,
    RevenueAndExpensesPerPeriodAndCategory,
    CategoryDetailsForPeriodResult,
    CategoryDetailsForPeriodResponse,
    BudgetEntryResult,
    BudgetTrackerResult,
    CategoriesForAccountResponse,
)

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
]
