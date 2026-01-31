"""SQLModel database models."""

from .associations import (
    user_bank_account_link,
    user_counterparty_link,
    user_ruleset_link,
)
from .bank_account import BankAccount
from .budget import BudgetTree, BudgetTreeNode
from .category import Category, CategoryTree
from .counterparty import Counterparty
from .rule_set_wrapper import RuleSetWrapper
from .rules import (
    ALL_OF,
    ANY_OF,
    CONTAINS_CAT_OP,
    CONTAINS_STRING_OP,
    MATCH_CAT_OP,
    MATCH_NUMBER_OP,
    MATCH_STRING_OP,
    Rule,
    RuleIF,
    RuleMatchType,
    RuleOperator,
    RuleSet,
)
from .transaction import Transaction
from .user import User

__all__ = [
    "User",
    "BankAccount",
    "Counterparty",
    "Category",
    "CategoryTree",
    "Transaction",
    "BudgetTree",
    "BudgetTreeNode",
    "RuleSetWrapper",
    "user_bank_account_link",
    "user_counterparty_link",
    "user_ruleset_link",
    # Rule models
    "Rule",
    "RuleSet",
    "RuleIF",
    "RuleMatchType",
    "RuleOperator",
    "ANY_OF",
    "ALL_OF",
    "CONTAINS_STRING_OP",
    "MATCH_STRING_OP",
    "CONTAINS_CAT_OP",
    "MATCH_CAT_OP",
    "MATCH_NUMBER_OP",
]
