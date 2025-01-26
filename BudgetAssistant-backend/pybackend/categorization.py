import logging
from typing import List, Optional

from pybackend.commons import TransactionTypeEnum
from pybackend.models import Category, CategoryTree, Counterparty, CustomUser, Transaction
from pybackend.providers import CategoryTreeProvider
from pybackend.rules import RuleSetWrapper, RuleSetWrappersPostOrderTraverser

logger = logging.getLogger(__name__)


class RuleBasedCategorizer:
    def __init__(self, expenses_category_tree: CategoryTree, revenue_category_tree: CategoryTree):
        self.expenses_category_tree = expenses_category_tree
        self.revenue_category_tree = revenue_category_tree
        self.traverser_by_user = {}

    def load_rules(self, user: CustomUser):

        if user not in self.traverser_by_user:
            rule_set_wrappers = RuleSetWrapper.objects.find_by_user(user)
            if not rule_set_wrappers or len(rule_set_wrappers) == 0:
                logger.warning(f"Found no rules for user {user}")
                return
            self.traverser_by_user[user] = RuleSetWrappersPostOrderTraverser(
                self.expenses_category_tree, self.revenue_category_tree, rule_set_wrappers
            )

    def categorize(self, transaction: Transaction, user: CustomUser) -> Optional[Category]:
        if transaction.has_category():
            return transaction.category

        if user not in self.traverser_by_user:
            return None

        traverser = self.traverser_by_user[user]
        traverser.set_current_transaction(transaction)
        return traverser.traverse()


class Categorizer:
    def __init__(self):
        self.rule_based_categorizer = RuleBasedCategorizer(expenses_category_tree=CategoryTreeProvider().provide(TransactionTypeEnum.EXPENSES),
                                                              revenue_category_tree=CategoryTreeProvider().provide(TransactionTypeEnum.REVENUE))

    def load_rules(self, user: CustomUser):
        self.rule_based_categorizer.load_rules(user)

    def categorize(self, transaction: Transaction, user: CustomUser) -> Transaction:
        if transaction.manually_assigned_category and transaction.has_category():
            return transaction

        category_opt: Optional[Category] = self.rule_based_categorizer.categorize(transaction, user)
        if category_opt:
            return transaction
        else:
            counterparty_id = transaction.counterparty.name
            counterparty: Optional[Counterparty] = Counterparty.objects.get(pk=counterparty_id)
            if counterparty and counterparty.category:
                transaction.category = counterparty.category

        if not transaction.has_category():
            logger.debug(f"No category found for transaction: {transaction}")

        return transaction

    def categorize_list(self, transactions: List[Transaction], user: CustomUser) -> List[Transaction]:
        return [self.categorize(transaction, user) for transaction in transactions]
