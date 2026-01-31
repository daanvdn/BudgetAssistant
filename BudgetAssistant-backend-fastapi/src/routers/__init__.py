"""FastAPI routers."""

from .analysis import router as analysis_router
from .bank_accounts import router as bank_accounts_router
from .budget import router as budget_router
from .categories import router as categories_router
from .rules import router as rules_router
from .transactions import router as transactions_router

__all__ = [
    "bank_accounts_router",
    "transactions_router",
    "categories_router",
    "analysis_router",
    "budget_router",
    "rules_router",
]
