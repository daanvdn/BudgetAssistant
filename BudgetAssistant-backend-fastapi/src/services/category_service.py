"""Category service with async SQLModel operations."""

from typing import List, Optional

from common.enums import TransactionTypeEnum
from models import Category, CategoryTree
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class CategoryService:
    """Service for category operations."""

    async def get_category_tree(
        self,
        transaction_type: TransactionTypeEnum,
        session: AsyncSession,
    ) -> Optional[CategoryTree]:
        """Get the category tree for a transaction type."""
        result = await session.execute(
            select(CategoryTree)
            .options(selectinload(CategoryTree.root))
            .where(CategoryTree.type == transaction_type.value)
        )
        return result.scalar_one_or_none()

    async def get_category_by_id(
        self,
        category_id: int,
        session: AsyncSession,
    ) -> Optional[Category]:
        """Get a category by ID."""
        result = await session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_category_by_qualified_name(
        self,
        qualified_name: str,
        session: AsyncSession,
    ) -> Optional[Category]:
        """Get a category by qualified name."""
        result = await session.execute(
            select(Category).where(Category.qualified_name == qualified_name)
        )
        return result.scalar_one_or_none()

    async def get_categories_by_type(
        self,
        transaction_type: TransactionTypeEnum,
        session: AsyncSession,
    ) -> List[Category]:
        """Get all categories of a specific type."""
        result = await session.execute(
            select(Category)
            .where(Category.type == transaction_type.value)
            .order_by(Category.qualified_name)
        )
        return list(result.scalars().all())

    async def get_all_categories(
        self,
        session: AsyncSession,
    ) -> List[Category]:
        """Get all categories."""
        result = await session.execute(
            select(Category).order_by(Category.qualified_name)
        )
        return list(result.scalars().all())

    async def get_category_children(
        self,
        category_id: int,
        session: AsyncSession,
    ) -> List[Category]:
        """Get children of a category."""
        result = await session.execute(
            select(Category)
            .where(Category.parent_id == category_id)
            .order_by(Category.name)
        )
        return list(result.scalars().all())

    async def get_root_categories(
        self,
        transaction_type: TransactionTypeEnum,
        session: AsyncSession,
    ) -> List[Category]:
        """Get root categories for a transaction type."""
        result = await session.execute(
            select(Category).where(
                Category.is_root == True,
                Category.type == transaction_type.value,
            )
        )
        return list(result.scalars().all())

    async def build_category_tree(
        self,
        root_category: Category,
        session: AsyncSession,
    ) -> dict:
        """Recursively build a category tree dictionary."""
        children = await self.get_category_children(root_category.id, session)

        child_trees = []
        for child in children:
            child_tree = await self.build_category_tree(child, session)
            child_trees.append(child_tree)

        return {
            "id": root_category.id,
            "name": root_category.name,
            "qualified_name": root_category.qualified_name,
            "is_root": root_category.is_root,
            "type": root_category.type,
            "parent_id": root_category.parent_id,
            "children": child_trees,
        }

    async def get_or_create_category(
        self,
        name: str,
        qualified_name: str,
        transaction_type: TransactionTypeEnum,
        parent_id: Optional[int],
        session: AsyncSession,
    ) -> Category:
        """Get or create a category."""
        existing = await self.get_category_by_qualified_name(qualified_name, session)
        if existing:
            return existing

        category = Category(
            name=name,
            qualified_name=qualified_name,
            type=transaction_type,
            parent_id=parent_id,
            is_root=parent_id is None,
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


# Singleton instance
category_service = CategoryService()
