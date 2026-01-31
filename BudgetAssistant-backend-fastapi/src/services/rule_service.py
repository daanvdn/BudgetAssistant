"""Rule service with async SQLModel operations."""

from collections import defaultdict
from typing import Any, Dict, List, Optional

import networkx as nx

from enums import TransactionTypeEnum
from models import Category, RuleSetWrapper, User
from models.associations import UserRuleSetLink
from models.category import CategoryTree
from models.transaction import Transaction
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class RuleService:
    """Service for rule set operations."""

    async def get_rule_set_wrapper(
        self,
        rule_set_id: int,
        session: AsyncSession,
    ) -> Optional[RuleSetWrapper]:
        """Get a rule set wrapper by ID."""
        result = await session.execute(
            select(RuleSetWrapper).where(RuleSetWrapper.id == rule_set_id)
        )
        return result.scalar_one_or_none()

    async def get_rule_set_wrapper_by_category(
        self,
        category_id: int,
        session: AsyncSession,
    ) -> Optional[RuleSetWrapper]:
        """Get a rule set wrapper by category ID."""
        result = await session.execute(
            select(RuleSetWrapper).where(RuleSetWrapper.category_id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_rule_set_wrapper(
        self,
        category_qualified_name: str,
        transaction_type: TransactionTypeEnum,
        user: User,
        session: AsyncSession,
    ) -> RuleSetWrapper:
        """Get or create a rule set wrapper for a category."""
        # Find the category
        category_result = await session.execute(
            select(Category).where(
                Category.qualified_name == category_qualified_name,
            )
        )
        category = category_result.scalar_one_or_none()

        if not category:
            raise ValueError(
                f"Category with name {category_qualified_name} does not exist"
            )

        # Check if rule set wrapper exists
        existing = await self.get_rule_set_wrapper_by_category(category.id, session)

        if existing:
            # Check if user is associated
            link_result = await session.execute(
                select(UserRuleSetLink).where(
                    UserRuleSetLink.user_id == user.id,
                    UserRuleSetLink.rule_set_wrapper_id == existing.id,
                )
            )
            if not link_result.scalar_one_or_none():
                link = UserRuleSetLink(
                    user_id=user.id,
                    rule_set_wrapper_id=existing.id,
                )
                session.add(link)
                await session.commit()

            return existing

        # Create new rule set wrapper
        rule_set_wrapper = RuleSetWrapper(
            category_id=category.id,
            rule_set_json="{}",
        )
        session.add(rule_set_wrapper)
        await session.flush()

        # Associate with user
        link = UserRuleSetLink(
            user_id=user.id,
            rule_set_wrapper_id=rule_set_wrapper.id,
        )
        session.add(link)
        await session.commit()
        await session.refresh(rule_set_wrapper)

        return rule_set_wrapper

    async def save_rule_set(
        self,
        rule_set_wrapper: RuleSetWrapper,
        session: AsyncSession,
    ) -> RuleSetWrapper:
        """Save a rule set wrapper."""
        await session.commit()
        await session.refresh(rule_set_wrapper)
        return rule_set_wrapper

    async def update_rule_set(
        self,
        rule_set_id: int,
        rule_set: Dict[str, Any],
        session: AsyncSession,
    ) -> RuleSetWrapper:
        """Update a rule set's rules."""
        rule_set_wrapper = await self.get_rule_set_wrapper(rule_set_id, session)
        if not rule_set_wrapper:
            raise ValueError(f"Rule set wrapper with id {rule_set_id} not found")

        rule_set_wrapper.set_rule_set_from_dict(rule_set)
        await session.commit()
        await session.refresh(rule_set_wrapper)
        return rule_set_wrapper

    async def delete_rule_set(
        self,
        rule_set_id: int,
        session: AsyncSession,
    ) -> None:
        """Delete a rule set wrapper."""
        rule_set_wrapper = await self.get_rule_set_wrapper(rule_set_id, session)
        if not rule_set_wrapper:
            raise ValueError(f"Rule set wrapper with id {rule_set_id} not found")

        # Delete user associations first
        await session.execute(
            select(UserRuleSetLink).where(
                UserRuleSetLink.rule_set_wrapper_id == rule_set_id
            )
        )
        # Note: This should cascade delete, but let's be explicit

        await session.delete(rule_set_wrapper)
        await session.commit()

    async def get_rule_sets_for_user(
        self,
        user: User,
        session: AsyncSession,
    ) -> List[RuleSetWrapper]:
        """Get all rule sets for a user."""
        result = await session.execute(
            select(RuleSetWrapper)
            .join(UserRuleSetLink)
            .where(UserRuleSetLink.user_id == user.id)
        )
        return list(result.scalars().all())

    async def user_has_access(
        self,
        user: User,
        rule_set_id: int,
        session: AsyncSession,
    ) -> bool:
        """Check if user has access to a rule set."""
        result = await session.execute(
            select(UserRuleSetLink).where(
                UserRuleSetLink.user_id == user.id,
                UserRuleSetLink.rule_set_wrapper_id == rule_set_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_rule_set_wrapper(
        self,
        category_id: int,
        rule_set: Dict[str, Any],
        user: User,
        session: AsyncSession,
    ) -> RuleSetWrapper:
        """Create a new rule set wrapper."""
        rule_set_wrapper = RuleSetWrapper(category_id=category_id)
        rule_set_wrapper.set_rule_set_from_dict(rule_set)
        session.add(rule_set_wrapper)
        await session.flush()

        # Associate with user
        link = UserRuleSetLink(
            user_id=user.id,
            rule_set_wrapper_id=rule_set_wrapper.id,
        )
        session.add(link)
        await session.commit()
        await session.refresh(rule_set_wrapper)

        return rule_set_wrapper


class RuleSetWrappersPostOrderTraverser:
    """Traverses category trees in post-order to find matching rule sets for transactions.

    This class converts category trees to NetworkX directed graphs and performs
    post-order traversal to find the most specific category that matches a transaction
    based on its rule set.
    """

    def __init__(
        self,
        expenses_category_tree: CategoryTree,
        revenue_category_tree: CategoryTree,
        rule_set_wrappers: List[RuleSetWrapper],
    ):
        """Initialize the traverser with category trees and rule sets.

        Args:
            expenses_category_tree: The category tree for expenses.
            revenue_category_tree: The category tree for revenue.
            rule_set_wrappers: List of rule set wrappers to use for matching.
        """
        self.expenses_category_tree = self._category_tree_to_nx_digraph(
            expenses_category_tree
        )
        self.revenue_category_tree = self._category_tree_to_nx_digraph(
            revenue_category_tree
        )
        self.rules_by_category: Dict[Category, RuleSetWrapper] = {
            wrapper.category: wrapper
            for wrapper in rule_set_wrappers
            if wrapper.category
        }
        self.current_transaction: Optional[Transaction] = None
        self.current_category: Optional[Category] = None
        self.counter: Dict[Category, int] = defaultdict(int)

    def _category_tree_to_nx_digraph(self, category_tree: CategoryTree) -> nx.DiGraph:
        """Convert a CategoryTree to a NetworkX directed graph.

        Args:
            category_tree: The category tree to convert.

        Returns:
            A NetworkX DiGraph representing the category hierarchy.
        """
        graph = nx.DiGraph()

        def add_category_to_graph(category: Category) -> None:
            graph.add_node(category)
            for child in category.children:
                graph.add_edge(category, child)
                add_category_to_graph(child)

        if category_tree.root:
            add_category_to_graph(category_tree.root)

        return graph

    def set_current_transaction(self, transaction: Transaction) -> None:
        """Set the current transaction to evaluate.

        Args:
            transaction: The transaction to evaluate against rule sets.
        """
        self.current_transaction = transaction

    def traverse(self) -> Optional[Category]:
        """Traverse the category tree in post-order to find a matching category.

        Post-order traversal ensures that child categories are evaluated before
        their parents, allowing more specific categories to match first.

        Returns:
            The matching Category if found, None otherwise.

        Raises:
            ValueError: If no transaction has been set before traversing.
        """
        if self.current_transaction is None:
            raise ValueError("Transaction must be set before traversing!")

        root = self.get_root_category()
        if root is None:
            return None

        categories_in_post_order = list(
            nx.dfs_postorder_nodes(self.get_category_tree(), root)
        )

        for category in categories_in_post_order:
            self.current_category = category
            if self.rule_set_matches(category):
                if self.current_category is None:
                    raise ValueError("Category must be set after traversing!")
                self.current_transaction.category = self.current_category
                self.current_transaction.category_id = self.current_category.id
                return self.current_category

        return None

    def get_root_category(self) -> Optional[Category]:
        """Get the root category based on the current transaction type.

        Returns:
            The root category for expenses or revenue based on transaction type.
        """
        if self.current_transaction is None:
            return None

        transaction_type = self.current_transaction.get_transaction_type()

        if transaction_type == TransactionTypeEnum.EXPENSES:
            # Find root node (node with in-degree 0)
            roots = [n for n, d in self.expenses_category_tree.in_degree() if d == 0]
            return roots[0] if roots else None
        else:
            roots = [n for n, d in self.revenue_category_tree.in_degree() if d == 0]
            return roots[0] if roots else None

    def get_category_tree(self) -> nx.DiGraph:
        """Get the appropriate category tree based on transaction type.

        Returns:
            The NetworkX DiGraph for expenses or revenue.
        """
        if self.current_transaction is None:
            return self.expenses_category_tree

        transaction_type = self.current_transaction.get_transaction_type()

        if transaction_type == TransactionTypeEnum.EXPENSES:
            return self.expenses_category_tree
        else:
            return self.revenue_category_tree

    def rule_set_matches(self, category: Category) -> bool:
        """Check if a category's rule set matches the current transaction.

        Args:
            category: The category to check.

        Returns:
            True if the category has a rule set that matches the transaction.
        """
        rule_set_wrapper = self.rules_by_category.get(category)
        if rule_set_wrapper is None:
            return False

        # Get the rule set as a RuleSet object
        rule_set = rule_set_wrapper.get_rule_set()
        if rule_set is None:
            return False

        return rule_set.evaluate(self.current_transaction)


# Singleton instance
rule_service = RuleService()
