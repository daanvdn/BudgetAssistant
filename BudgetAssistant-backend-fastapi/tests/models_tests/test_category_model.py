"""Tests for Category and CategoryTree models."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from common.enums import TransactionTypeEnum
from models import Category, CategoryTree
from tests.utils import assert_persisted


class TestCategory:
    """Test cases for the Category model."""

    @pytest.mark.asyncio
    async def test_create_category_with_valid_data(self, async_session):
        """Test creating a category with valid data."""
        category = Category(
            name="Test Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="Test Category",
        )
        async_session.add(category)
        await async_session.commit()
        await async_session.refresh(category)

        assert category.id is not None
        assert category.name == "Test Category"
        assert category.type == TransactionTypeEnum.EXPENSES
        assert category.is_root is False

        # Re-query from database to verify persistence
        await assert_persisted(
            async_session,
            Category,
            "id",
            category.id,
            {
                "name": "Test Category",
                "type": TransactionTypeEnum.EXPENSES,
                "qualified_name": "Test Category",
                "is_root": False,
            },
        )

    @pytest.mark.asyncio
    async def test_category_qualified_name_hierarchy(self, async_session):
        """Test category qualified name reflects hierarchy."""
        root_category = Category(
            name="Root",
            type=TransactionTypeEnum.EXPENSES,
            is_root=True,
            qualified_name="root",
        )
        async_session.add(root_category)
        await async_session.commit()
        await async_session.refresh(root_category)
        root_id = root_category.id

        child_category = Category(
            name="Child",
            type=TransactionTypeEnum.EXPENSES,
            parent_id=root_category.id,
            qualified_name="root#child",
        )
        async_session.add(child_category)
        await async_session.commit()
        await async_session.refresh(child_category)
        child_id = child_category.id

        assert child_category.qualified_name == "root#child"

        # Re-query from database to verify hierarchy is persisted
        await assert_persisted(
            async_session,
            Category,
            "id",
            root_id,
            {
                "name": "Root",
                "is_root": True,
                "qualified_name": "root",
            },
        )

        await assert_persisted(
            async_session,
            Category,
            "id",
            child_id,
            {
                "name": "Child",
                "parent_id": root_id,
                "qualified_name": "root#child",
            },
        )

    @pytest.mark.asyncio
    async def test_add_child_category(self, async_session):
        """Test adding a child category to a parent."""
        root_category = Category(
            name="Root",
            type=TransactionTypeEnum.EXPENSES,
            is_root=True,
            qualified_name="root",
        )
        async_session.add(root_category)
        await async_session.commit()
        await async_session.refresh(root_category)
        root_id = root_category.id

        child_category = Category(
            name="Child",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="root#child",
        )
        async_session.add(child_category)
        await async_session.commit()

        root_category.add_child(child_category)
        await async_session.commit()
        await async_session.refresh(child_category)
        child_id = child_category.id

        assert child_category.parent_id == root_category.id

        # Re-query from database to verify parent-child relationship
        await assert_persisted(
            async_session,
            Category,
            "id",
            child_id,
            {
                "name": "Child",
                "parent_id": root_id,
                "qualified_name": "root#child",
            },
        )

        # Verify parent's children relationship using selectinload
        result = await async_session.execute(
            select(Category)
            .where(Category.id == root_id)
            .options(selectinload(Category.children))
            .execution_options(populate_existing=True)
        )
        persisted_root = result.scalar_one_or_none()

        assert persisted_root is not None
        assert len(persisted_root.children) == 1
        assert persisted_root.children[0].id == child_id
        assert persisted_root.children[0].name == "Child"

    @pytest.mark.asyncio
    async def test_category_equality_based_on_qualified_name(self, async_session):
        """Test category equality is based on qualified_name."""
        category1 = Category(
            name="Child",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="child",
        )
        category2 = Category(
            name="Child",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="child",
        )

        assert category1 == category2

    @pytest.mark.asyncio
    async def test_category_hash_based_on_qualified_name(self, async_session):
        """Test category hash is based on qualified_name."""
        root_category = Category(
            name="Root",
            type=TransactionTypeEnum.EXPENSES,
            is_root=True,
            qualified_name="root",
        )
        async_session.add(root_category)
        await async_session.commit()

        child_category = Category(
            name="Child",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="root#child",
        )

        assert hash(child_category) == hash("root#child")

    @pytest.mark.asyncio
    async def test_category_str_method(self, async_session):
        """Test category __str__ method."""
        category = Category(
            name="Test Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="test",
        )
        assert str(category) == "Test Category"

    @pytest.mark.asyncio
    async def test_category_comparison_operators(self, async_session):
        """Test category comparison operators."""
        category1 = Category(
            name="A",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="a",
        )
        category2 = Category(
            name="B",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="b",
        )

        assert category1 < category2
        assert category2 > category1


class TestCategoryTree:
    """Test cases for the CategoryTree model."""

    @pytest.mark.asyncio
    async def test_create_category_tree_with_valid_data(self, async_session):
        """Test creating a category tree with valid data."""
        root_category = Category(
            name="Root",
            type=TransactionTypeEnum.EXPENSES,
            is_root=True,
            qualified_name="root",
        )
        async_session.add(root_category)
        await async_session.commit()
        await async_session.refresh(root_category)

        category_tree = CategoryTree(
            root_id=root_category.id,
            type=TransactionTypeEnum.EXPENSES,
        )
        async_session.add(category_tree)
        await async_session.commit()
        await async_session.refresh(category_tree)

        assert category_tree.id is not None
        assert category_tree.root_id == root_category.id
        assert category_tree.type == TransactionTypeEnum.EXPENSES

    @pytest.mark.asyncio
    async def test_create_category_tree_with_duplicate_root(self, async_session):
        """Test that duplicate root categories raise an error."""
        root_category = Category(
            name="Root",
            type=TransactionTypeEnum.EXPENSES,
            is_root=True,
            qualified_name="root",
        )
        async_session.add(root_category)
        await async_session.commit()
        await async_session.refresh(root_category)

        category_tree1 = CategoryTree(
            root_id=root_category.id,
            type=TransactionTypeEnum.EXPENSES,
        )
        async_session.add(category_tree1)
        await async_session.commit()

        category_tree2 = CategoryTree(
            root_id=root_category.id,
            type=TransactionTypeEnum.EXPENSES,
        )
        async_session.add(category_tree2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_category_tree_str_method(self, async_session):
        """Test category tree __str__ method."""
        root_category = Category(
            name="Root",
            type=TransactionTypeEnum.EXPENSES,
            is_root=True,
            qualified_name="root",
        )
        async_session.add(root_category)
        await async_session.commit()
        await async_session.refresh(root_category)

        category_tree = CategoryTree(
            root_id=root_category.id,
            type=TransactionTypeEnum.EXPENSES,
        )
        category_tree.root = root_category

        assert str(category_tree) == "EXPENSES - Root"

    @pytest.mark.asyncio
    async def test_category_tree_with_children(self, async_session):
        """Test category tree with child categories."""
        root_category = Category(
            name="Root",
            type=TransactionTypeEnum.EXPENSES,
            is_root=True,
            qualified_name="root",
        )
        async_session.add(root_category)
        await async_session.commit()
        await async_session.refresh(root_category)

        child_category = Category(
            name="Child",
            type=TransactionTypeEnum.EXPENSES,
            parent_id=root_category.id,
            qualified_name="root#child",
        )
        async_session.add(child_category)
        await async_session.commit()

        category_tree = CategoryTree(
            root_id=root_category.id,
            type=TransactionTypeEnum.EXPENSES,
        )
        async_session.add(category_tree)
        await async_session.commit()
        await async_session.refresh(root_category)

        assert len(root_category.children) == 1
        assert root_category.children[0].name == "Child"
