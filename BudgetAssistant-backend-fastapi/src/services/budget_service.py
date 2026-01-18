"""Budget service with async SQLModel operations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import BankAccount, BudgetTree, BudgetTreeNode, Category, User
from models.associations import UserBankAccountLink


class BudgetService:
    """Service for budget operations."""

    async def get_budget_tree(
        self,
        bank_account: str,
        session: AsyncSession,
    ) -> Optional[BudgetTree]:
        """Get the budget tree for a bank account."""
        normalized = BankAccount.normalize_account_number(bank_account)

        result = await session.execute(
            select(BudgetTree).where(BudgetTree.bank_account_id == normalized)
        )
        return result.scalar_one_or_none()

    async def get_budget_tree_node(
        self,
        node_id: int,
        session: AsyncSession,
    ) -> Optional[BudgetTreeNode]:
        """Get a budget tree node by ID."""
        result = await session.execute(
            select(BudgetTreeNode).where(BudgetTreeNode.id == node_id)
        )
        return result.scalar_one_or_none()

    async def get_node_children(
        self,
        node_id: int,
        session: AsyncSession,
    ) -> List[BudgetTreeNode]:
        """Get children of a budget tree node."""
        result = await session.execute(
            select(BudgetTreeNode).where(BudgetTreeNode.parent_id == node_id)
        )
        return list(result.scalars().all())

    async def find_or_create_budget(
        self,
        bank_account: str,
        session: AsyncSession,
    ) -> BudgetTree:
        """Find or create a budget tree for a bank account."""
        normalized = BankAccount.normalize_account_number(bank_account)

        # Check if budget tree exists
        existing = await self.get_budget_tree(normalized, session)
        if existing:
            return existing

        # Get root category for expenses (default budget type)
        root_cat_result = await session.execute(
            select(Category).where(
                Category.name == "root",
                Category.is_root == True,
            )
        )
        root_category = root_cat_result.scalar_one_or_none()

        if not root_category:
            raise ValueError(
                "Root category not found. Please initialize categories first."
            )

        # Create root node
        root_node = BudgetTreeNode(
            category_id=root_category.id,
            amount=0,
        )
        session.add(root_node)
        await session.flush()

        # Create budget tree
        budget_tree = BudgetTree(
            bank_account_id=normalized,
            root_id=root_node.id,
            number_of_descendants=0,
        )
        session.add(budget_tree)
        await session.commit()
        await session.refresh(budget_tree)

        return budget_tree

    async def update_budget_entry_amount(
        self,
        node_id: int,
        amount: int,
        session: AsyncSession,
    ) -> BudgetTreeNode:
        """Update a budget tree node's amount."""
        node = await self.get_budget_tree_node(node_id, session)
        if not node:
            raise ValueError(f"Budget entry with id {node_id} not found")

        node.amount = amount
        await session.commit()
        await session.refresh(node)
        return node

    async def add_budget_entry(
        self,
        parent_id: int,
        category_id: int,
        amount: int,
        session: AsyncSession,
    ) -> BudgetTreeNode:
        """Add a new budget entry under a parent node."""
        parent = await self.get_budget_tree_node(parent_id, session)
        if not parent:
            raise ValueError(f"Parent node with id {parent_id} not found")

        node = BudgetTreeNode(
            category_id=category_id,
            amount=amount,
            parent_id=parent_id,
        )
        session.add(node)
        await session.commit()
        await session.refresh(node)

        # Update budget tree descendant count
        await self._update_descendant_count(parent_id, session)

        return node

    async def _update_descendant_count(
        self,
        node_id: int,
        session: AsyncSession,
    ) -> None:
        """Recursively update descendant count for budget tree."""
        # Find the root node and its budget tree
        node = await self.get_budget_tree_node(node_id, session)
        if not node:
            return

        # Traverse up to find root
        current = node
        while current.parent_id:
            parent_result = await session.execute(
                select(BudgetTreeNode).where(BudgetTreeNode.id == current.parent_id)
            )
            current = parent_result.scalar_one_or_none()
            if not current:
                break

        # Update budget tree with root
        tree_result = await session.execute(
            select(BudgetTree).where(BudgetTree.root_id == current.id)
        )
        budget_tree = tree_result.scalar_one_or_none()

        if budget_tree:
            # Count all descendants
            count = await self._count_descendants(current.id, session)
            budget_tree.number_of_descendants = count
            await session.commit()

    async def _count_descendants(
        self,
        node_id: int,
        session: AsyncSession,
    ) -> int:
        """Recursively count descendants of a node."""
        children = await self.get_node_children(node_id, session)
        count = len(children)
        for child in children:
            count += await self._count_descendants(child.id, session)
        return count

    async def build_budget_tree_dict(
        self,
        node: BudgetTreeNode,
        session: AsyncSession,
    ) -> dict:
        """Recursively build a budget tree dictionary."""
        # Get category info
        category_result = await session.execute(
            select(Category).where(Category.id == node.category_id)
        )
        category = category_result.scalar_one_or_none()

        children = await self.get_node_children(node.id, session)

        child_dicts = []
        for child in children:
            child_dict = await self.build_budget_tree_dict(child, session)
            child_dicts.append(child_dict)

        return {
            "id": node.id,
            "amount": node.amount,
            "category_id": node.category_id,
            "parent_id": node.parent_id,
            "name": category.name if category else "",
            "qualified_name": category.qualified_name if category else "",
            "children": child_dicts,
        }

    async def user_has_budget_access(
        self,
        user: User,
        bank_account: str,
        session: AsyncSession,
    ) -> bool:
        """Check if user has access to a budget (via bank account)."""
        normalized = BankAccount.normalize_account_number(bank_account)

        result = await session.execute(
            select(UserBankAccountLink).where(
                UserBankAccountLink.user_id == user.id,
                UserBankAccountLink.bank_account_number == normalized,
            )
        )
        return result.scalar_one_or_none() is not None


# Singleton instance
budget_service = BudgetService()

