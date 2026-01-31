"""Category and Budget tree providers with async SQLModel operations."""

import importlib.resources as pkg_resources
import re
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.enums import TransactionTypeEnum
from models import BankAccount, BudgetTree, BudgetTreeNode, Category, CategoryTree


class CategoryTreeInserter:
    """Inserts category trees from resource files."""

    LEADING_TABS = re.compile(r"^\t+")

    def __init__(self) -> None:
        pass

    def _parse_lines(self, lines: List[str]) -> List[str]:
        """Parse lines into qualified name paths.

        Converts a tab-indented category file into a list of qualified names.
        Each qualified name is constructed by joining ancestor names with '#'.
        """
        result: List[str] = []
        ancestors: List[str] = []

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            # Determine the number of leading tabs
            leading_tabs = self.LEADING_TABS.match(line)
            level = len(leading_tabs.group()) if leading_tabs else 0

            # Adjust the ancestors list to the current level
            if level < len(ancestors):
                ancestors = ancestors[:level]
            elif level > len(ancestors):
                ancestors.append(ancestors[-1])

            # Add the current category to the ancestors list
            if level == 0:
                ancestors = [stripped_line]
            else:
                ancestors.append(stripped_line)

            # Construct the full path
            full_path = "#".join(ancestors)
            result.append(full_path)

        # Sort lines ascending
        result.sort()
        return result

    async def _insert_lines(
        self,
        lines: List[str],
        root: Category,
        transaction_type: TransactionTypeEnum,
        session: AsyncSession,
    ) -> None:
        """Insert parsed categories into database."""
        inserted_categories: Dict[str, Category] = {}
        parsed_lines = self._parse_lines(lines)

        for qualified_name in parsed_lines:
            qualified_name_parts = qualified_name.split("#")
            parent = root

            for i in range(len(qualified_name_parts)):
                # Get parts 0 till i (inclusive)
                partial_qualified_name = "#".join(qualified_name_parts[: i + 1])

                # Check if category exists
                if partial_qualified_name in inserted_categories:
                    parent = inserted_categories[partial_qualified_name]
                else:
                    category = Category(
                        name=qualified_name_parts[i],
                        parent=parent,
                        parent_id=parent.id,
                        is_root=False,
                        type=transaction_type,
                        qualified_name=partial_qualified_name,
                    )
                    session.add(category)
                    await session.flush()
                    inserted_categories[partial_qualified_name] = category
                    parent = category

    async def run(
        self,
        transaction_type: TransactionTypeEnum,
        session: AsyncSession,
    ) -> CategoryTree:
        """Create and populate a category tree for the given transaction type."""
        if transaction_type == TransactionTypeEnum.EXPENSES:
            resource = "categories-expenses.txt"
        elif transaction_type == TransactionTypeEnum.REVENUE:
            resource = "categories-revenue.txt"
        else:
            raise ValueError("Invalid category tree type")

        # Load resource file
        with (
            pkg_resources.files("resources")
            .joinpath(resource)
            .open(encoding="utf-8") as file
        ):
            lines = file.read().split("\n")

        # Create root category
        root = Category(
            name=Category.ROOT_NAME,
            parent=None,
            is_root=True,
            type=transaction_type,
            qualified_name=Category.ROOT_NAME,
        )
        session.add(root)
        await session.flush()

        # Create NO CATEGORY
        no_category = Category(
            name=Category.NO_CATEGORY_NAME,
            parent=root,
            parent_id=root.id,
            is_root=False,
            type=transaction_type,
            qualified_name=Category.NO_CATEGORY_NAME,
        )
        session.add(no_category)
        await session.flush()

        # Create DUMMY CATEGORY
        dummy_category = Category(
            name=Category.DUMMY_CATEGORY_NAME,
            parent=root,
            parent_id=root.id,
            is_root=False,
            type=transaction_type,
            qualified_name=Category.DUMMY_CATEGORY_NAME,
        )
        session.add(dummy_category)
        await session.flush()

        # Insert all categories from file
        await self._insert_lines(lines, root, transaction_type, session)

        # Create and save the category tree
        tree = CategoryTree(
            root=root,
            root_id=root.id,
            type=transaction_type,
        )
        session.add(tree)
        await session.flush()

        return tree


class CategoryTreeProvider:
    """Provides category trees, creating them if needed."""

    def __init__(self) -> None:
        pass

    async def provide(
        self,
        transaction_type: TransactionTypeEnum,
        session: AsyncSession,
    ) -> CategoryTree:
        """Get or create category tree for transaction type.

        Returns existing tree if found, otherwise creates a new one via CategoryTreeInserter.
        """
        # Try to find existing category tree
        result = await session.execute(
            select(CategoryTree)
            .options(selectinload(CategoryTree.root))
            .where(CategoryTree.type == transaction_type.value)
        )
        category_tree = result.scalar_one_or_none()

        if category_tree is not None:
            return category_tree

        # Create new category tree
        return await CategoryTreeInserter().run(transaction_type, session)


class BudgetTreeProvider:
    """Provides budget trees for bank accounts."""

    def __init__(self) -> None:
        pass

    async def provide(
        self,
        bank_account: BankAccount,
        session: AsyncSession,
    ) -> BudgetTree:
        """Get or create budget tree for bank account.

        Creates a budget tree that mirrors the expenses category tree structure.
        """
        # Try to find existing budget tree
        result = await session.execute(
            select(BudgetTree)
            .options(selectinload(BudgetTree.root))
            .where(BudgetTree.bank_account_id == bank_account.account_number)
        )
        existing_budget_tree = result.scalar_one_or_none()

        if existing_budget_tree is not None:
            return existing_budget_tree

        # Get expenses category tree
        expenses_category_tree = await CategoryTreeProvider().provide(
            TransactionTypeEnum.EXPENSES, session
        )

        # Create budget tree mirroring category structure
        root_category = expenses_category_tree.root
        if root_category is None:
            raise ValueError("Category tree has no root")

        # Refresh root_category to ensure children are loaded
        await session.refresh(root_category, ["children"])

        number_of_descendants = 0

        # Create root budget node
        root_node = BudgetTreeNode(
            category=root_category,
            category_id=root_category.id,
            amount=-1,
        )
        session.add(root_node)
        await session.flush()
        number_of_descendants += 1

        # Recursively create child nodes
        for child_category in root_category.children:
            number_of_descendants = await self._handle_child(
                child_category, root_node, number_of_descendants, session
            )

        # Create and save budget tree
        budget_tree = BudgetTree(
            bank_account=bank_account,
            bank_account_id=bank_account.account_number,
            root=root_node,
            root_id=root_node.id,
            number_of_descendants=number_of_descendants,
        )
        session.add(budget_tree)
        await session.flush()

        return budget_tree

    async def _handle_child(
        self,
        category: Category,
        parent_node: BudgetTreeNode,
        number_of_descendants: int,
        session: AsyncSession,
    ) -> int:
        """Recursively create budget tree nodes for category children."""
        # Refresh category to ensure children are loaded
        await session.refresh(category, ["children"])

        budget_tree_node = BudgetTreeNode(
            category=category,
            category_id=category.id,
            amount=0,
            parent=parent_node,
            parent_id=parent_node.id,
        )
        session.add(budget_tree_node)
        await session.flush()
        number_of_descendants += 1

        for child_category in category.children:
            number_of_descendants = await self._handle_child(
                child_category, budget_tree_node, number_of_descendants, session
            )

        return number_of_descendants
