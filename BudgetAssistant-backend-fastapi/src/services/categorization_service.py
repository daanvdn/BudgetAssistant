"""Categorization service for rule-based transaction categorization.

This service uses the RuleSet/Rule models and RuleSetWrappersPostOrderTraverser
for proper post-order traversal of category trees when categorizing transactions.
"""

from typing import List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.enums import TransactionTypeEnum
from models import BankAccount, Category, RuleSetWrapper, Transaction, User
from models.associations import UserBankAccountLink, UserRuleSetLink
from models.category import CategoryTree
from services.rule_service import RuleSetWrappersPostOrderTraverser


class CategorizationService:
    """Service for rule-based transaction categorization.

    This service provides methods to categorize transactions based on rule sets
    defined by users. It uses post-order traversal of category trees to ensure
    that more specific (child) categories are matched before more general (parent)
    categories.
    """

    async def get_rule_sets_for_user(self, user: User, session: AsyncSession) -> List[RuleSetWrapper]:
        """Get all rule set wrappers for a user.

        Args:
            user: The user to get rule sets for.
            session: The database session.

        Returns:
            List of RuleSetWrapper objects associated with the user.
        """
        result = await session.execute(
            select(RuleSetWrapper)
            .join(UserRuleSetLink)
            .where(UserRuleSetLink.user_id == user.id)
            .options(selectinload(RuleSetWrapper.category))
        )
        return list(result.scalars().all())

    async def get_category_tree(
        self,
        transaction_type: TransactionTypeEnum,
        session: AsyncSession,
    ) -> Optional[CategoryTree]:
        """Get the category tree for a transaction type.

        Args:
            transaction_type: The type of transactions (EXPENSES or REVENUE).
            session: The database session.

        Returns:
            The CategoryTree if found, None otherwise.
        """
        result = await session.execute(
            select(CategoryTree)
            .where(CategoryTree.type == transaction_type.value)
            .options(selectinload(CategoryTree.root))
        )
        category_tree = result.scalar_one_or_none()

        if category_tree and category_tree.root:
            # Recursively load children for the entire tree
            await self._load_category_children(category_tree.root, session)

        return category_tree

    async def _load_category_children(self, category: Category, session: AsyncSession) -> None:
        """Recursively load children for a category.

        Args:
            category: The category to load children for.
            session: The database session.
        """
        await session.refresh(category, ["children"])
        for child in category.children:
            await self._load_category_children(child, session)

    async def get_uncategorized_transactions(
        self,
        user: User,
        bank_account_id: Optional[str],
        transaction_type: Optional[TransactionTypeEnum],
        session: AsyncSession,
    ) -> List[Transaction]:
        """Get transactions that need categorization.

        Args:
            user: The user whose transactions to get.
            bank_account_id: Optional specific bank account to filter by.
            transaction_type: Optional transaction type filter (EXPENSES/REVENUE).
            session: The database session.

        Returns:
            List of transactions that don't have manually assigned categories.
        """
        # Get user's bank accounts
        if bank_account_id:
            bank_accounts = [BankAccount.normalize_account_number(bank_account_id)]
        else:
            result = await session.execute(
                select(UserBankAccountLink.bank_account_number).where(UserBankAccountLink.user_id == user.id)
            )
            bank_accounts = list(result.scalars().all())

        if not bank_accounts:
            return []

        # Build query conditions
        conditions = [
            Transaction.bank_account_id.in_(bank_accounts),
            Transaction.manually_assigned_category == False,  # noqa: E712
        ]

        # Add transaction type filter
        if transaction_type:
            if transaction_type == TransactionTypeEnum.REVENUE:
                conditions.append(Transaction.amount >= 0)
            elif transaction_type == TransactionTypeEnum.EXPENSES:
                conditions.append(Transaction.amount < 0)

        result = await session.execute(
            select(Transaction)
            .where(and_(*conditions))
            .options(
                selectinload(Transaction.counterparty),
                selectinload(Transaction.bank_account),
            )
        )
        return list(result.scalars().all())

    async def categorize_transaction_with_traverser(
        self,
        transaction: Transaction,
        traverser: RuleSetWrappersPostOrderTraverser,
    ) -> Optional[Category]:
        """Categorize a single transaction using post-order tree traversal.

        This method uses the RuleSetWrappersPostOrderTraverser to find the most
        specific category that matches the transaction's rule set.

        Args:
            transaction: The transaction to categorize.
            traverser: The configured traverser with category trees and rule sets.

        Returns:
            The matching Category if found, None otherwise.
        """
        traverser.set_current_transaction(transaction)
        return traverser.traverse()

    async def categorize_transaction(
        self,
        transaction: Transaction,
        rule_sets: List[RuleSetWrapper],
        session: AsyncSession,
    ) -> Optional[int]:
        """Try to categorize a single transaction using rule sets (simple evaluation).

        This is a simpler categorization method that evaluates rules in order
        without post-order tree traversal. For proper hierarchical categorization,
        use categorize_transaction_with_traverser instead.

        Args:
            transaction: The transaction to categorize.
            rule_sets: List of rule set wrappers to evaluate.
            session: The database session.

        Returns:
            The category_id if a match is found, None otherwise.
        """
        for rule_set_wrapper in rule_sets:
            rule_set = rule_set_wrapper.get_rule_set()
            if not rule_set:
                continue

            # Use the RuleSet's evaluate method directly
            if rule_set.evaluate(transaction):
                return rule_set_wrapper.category_id

        # If no rules match, try counterparty category
        if transaction.counterparty and transaction.counterparty.category_id:
            return transaction.counterparty.category_id

        return None

    async def categorize_transactions_with_traverser(
        self,
        user: User,
        bank_account_id: Optional[str],
        transaction_type: Optional[TransactionTypeEnum],
        session: AsyncSession,
    ) -> Tuple[int, int]:
        """Categorize transactions using post-order tree traversal.

        This method uses RuleSetWrappersPostOrderTraverser for proper hierarchical
        categorization, ensuring that more specific categories are matched first.

        Args:
            user: The user whose transactions to categorize.
            bank_account_id: Optional specific bank account to filter by.
            transaction_type: Optional transaction type filter.
            session: The database session.

        Returns:
            Tuple of (with_category_count, without_category_count).
        """
        # Load rule sets with category relationships
        rule_sets = await self.get_rule_sets_for_user(user, session)

        # Get category trees
        expenses_tree = await self.get_category_tree(TransactionTypeEnum.EXPENSES, session)
        revenue_tree = await self.get_category_tree(TransactionTypeEnum.REVENUE, session)

        if not expenses_tree or not revenue_tree:
            # Cannot categorize without category trees
            return (0, 0)

        # Create traverser
        traverser = RuleSetWrappersPostOrderTraverser(
            expenses_category_tree=expenses_tree,
            revenue_category_tree=revenue_tree,
            rule_set_wrappers=rule_sets,
        )

        # Get uncategorized transactions
        transactions = await self.get_uncategorized_transactions(user, bank_account_id, transaction_type, session)

        with_category = 0
        without_category = 0

        for transaction in transactions:
            category = await self.categorize_transaction_with_traverser(transaction, traverser)

            if category is not None:
                transaction.category_id = category.id
                transaction.category = category
                transaction.manually_assigned_category = False
                transaction.is_manually_reviewed = False
                with_category += 1
            else:
                without_category += 1

        await session.commit()

        return with_category, without_category

    async def categorize_transactions(
        self,
        user: User,
        bank_account_id: Optional[str],
        transaction_type: Optional[TransactionTypeEnum],
        session: AsyncSession,
    ) -> Tuple[int, int]:
        """Categorize all matching transactions for a user.

        This method delegates to categorize_transactions_with_traverser for
        proper hierarchical categorization using post-order tree traversal.

        Args:
            user: The user whose transactions to categorize.
            bank_account_id: Optional specific bank account to filter by.
            transaction_type: Optional transaction type filter.
            session: The database session.

        Returns:
            Tuple of (with_category_count, without_category_count).
        """
        return await self.categorize_transactions_with_traverser(user, bank_account_id, transaction_type, session)


# Singleton instance
categorization_service = CategorizationService()
