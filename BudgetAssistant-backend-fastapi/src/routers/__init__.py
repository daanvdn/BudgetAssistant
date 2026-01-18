"""FastAPI routers."""

from .auth import router as auth_router
from .bank_accounts import router as bank_accounts_router
from .transactions import router as transactions_router
from .categories import router as categories_router
from .analysis import router as analysis_router
from .budget import router as budget_router
from .rules import router as rules_router

__all__ = [
    "auth_router",
    "bank_accounts_router",
    "transactions_router",
    "categories_router",
    "analysis_router",
    "budget_router",
    "rules_router",
]

