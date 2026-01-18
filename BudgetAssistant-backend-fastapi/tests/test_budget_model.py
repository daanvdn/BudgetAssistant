"""Tests for BudgetTree and BudgetTreeNode models."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import BudgetTree, BudgetTreeNode, BankAccount, Category
from enums import TransactionTypeEnum


class TestBudgetTreeNode:
    """Test cases for the BudgetTreeNode model."""

    @pytest.mark.asyncio
    async def test_create_budget_tree_node_with_valid_data(self, async_session):
        """Test creating a budget tree node with valid data."""
        category = Category(
            name="Test Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="test",
        )
        async_session.add(category)
        await async_session.commit()
        await async_session.refresh(category)

        budget_tree_node = BudgetTreeNode(
            category_id=category.id,
            amount=100,
        )
        async_session.add(budget_tree_node)
        await async_session.commit()
        await async_session.refresh(budget_tree_node)

        assert budget_tree_node.id is not None
        assert budget_tree_node.category_id == category.id
        assert budget_tree_node.amount == 100

    @pytest.mark.asyncio
    async def test_add_child_to_budget_tree_node(self, async_session):
        """Test adding a child node to a budget tree node."""
        parent_category = Category(
            name="Parent Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="parent",
        )
        child_category = Category(
            name="Child Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="child",
        )
        async_session.add_all([parent_category, child_category])
        await async_session.commit()
        await async_session.refresh(parent_category)
        await async_session.refresh(child_category)

        parent_node = BudgetTreeNode(category_id=parent_category.id, amount=200)
        async_session.add(parent_node)
        await async_session.commit()
        await async_session.refresh(parent_node)

        child_node = BudgetTreeNode(
            category_id=child_category.id,
            amount=50,
            parent_id=parent_node.id,
        )
        async_session.add(child_node)
        await async_session.commit()

        # Query children explicitly
        result = await async_session.execute(
            select(BudgetTreeNode).where(BudgetTreeNode.parent_id == parent_node.id)
        )
        children = result.scalars().all()

        assert len(children) == 1
        assert children[0].amount == 50

    @pytest.mark.asyncio
    async def test_get_children_returns_correct_children(self, async_session):
        """Test that getting children returns all child nodes."""
        parent_category = Category(
            name="Parent Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="parent",
        )
        child_category1 = Category(
            name="Child Category 1",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="child1",
        )
        child_category2 = Category(
            name="Child Category 2",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="child2",
        )
        async_session.add_all([parent_category, child_category1, child_category2])
        await async_session.commit()

        parent_node = BudgetTreeNode(category_id=parent_category.id, amount=200)
        async_session.add(parent_node)
        await async_session.commit()
        await async_session.refresh(parent_node)

        child_node1 = BudgetTreeNode(
            category_id=child_category1.id,
            amount=50,
            parent_id=parent_node.id,
        )
        child_node2 = BudgetTreeNode(
            category_id=child_category2.id,
            amount=75,
            parent_id=parent_node.id,
        )
        async_session.add_all([child_node1, child_node2])
        await async_session.commit()

        # Query children explicitly
        result = await async_session.execute(
            select(BudgetTreeNode).where(BudgetTreeNode.parent_id == parent_node.id)
        )
        children = result.scalars().all()

        assert len(children) == 2
        amounts = [c.amount for c in children]
        assert 50 in amounts
        assert 75 in amounts

    @pytest.mark.asyncio
    async def test_is_root_category_returns_true_for_root_node(self, async_session):
        """Test is_root_category returns True for root category node."""
        root_category = Category(
            name="root",  # Use literal "root" to match the constant
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="root",
        )
        async_session.add(root_category)
        await async_session.commit()
        await async_session.refresh(root_category)

        root_node = BudgetTreeNode(category_id=root_category.id, amount=300)
        root_node.category = root_category

        assert root_node.is_root_category() is True

    @pytest.mark.asyncio
    async def test_is_root_category_returns_false_for_non_root_node(self, async_session):
        """Test is_root_category returns False for non-root category node."""
        child_category = Category(
            name="Child Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="child",
        )
        async_session.add(child_category)
        await async_session.commit()
        await async_session.refresh(child_category)

        child_node = BudgetTreeNode(category_id=child_category.id, amount=100)
        child_node.category = child_category

        assert child_node.is_root_category() is False

    @pytest.mark.asyncio
    async def test_parent_node_is_root_returns_true_for_direct_child(self, async_session):
        """Test parent_node_is_root returns True for direct child of root."""
        root_category = Category(
            name="root",  # Use literal "root" to match the constant
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="root",
        )
        child_category = Category(
            name="Child Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="child",
        )
        async_session.add_all([root_category, child_category])
        await async_session.commit()
        await async_session.refresh(root_category)
        await async_session.refresh(child_category)

        root_node = BudgetTreeNode(category_id=root_category.id, amount=300)
        root_node.category = root_category
        async_session.add(root_node)
        await async_session.commit()
        await async_session.refresh(root_node)

        child_node = BudgetTreeNode(
            category_id=child_category.id,
            amount=100,
            parent_id=root_node.id,
        )
        child_node.category = child_category
        child_node.parent = root_node

        assert child_node.parent_node_is_root() is True

    @pytest.mark.asyncio
    async def test_budget_tree_node_equality(self, async_session):
        """Test budget tree node equality."""
        category = Category(
            name="Test",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="test",
        )
        async_session.add(category)
        await async_session.commit()
        await async_session.refresh(category)

        node1 = BudgetTreeNode(id=1, category_id=category.id, amount=100)
        node2 = BudgetTreeNode(id=1, category_id=category.id, amount=100)
        node3 = BudgetTreeNode(id=2, category_id=category.id, amount=100)

        assert node1 == node2
        assert node1 != node3


class TestBudgetTree:
    """Test cases for the BudgetTree model."""

    @pytest.mark.asyncio
    async def test_create_budget_tree_with_valid_data(self, async_session):
        """Test creating a budget tree with valid data."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        async_session.add(bank_account)
        await async_session.commit()

        root_category = Category(
            name="Root",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="root",
        )
        async_session.add(root_category)
        await async_session.commit()
        await async_session.refresh(root_category)

        root_node = BudgetTreeNode(category_id=root_category.id, amount=100)
        async_session.add(root_node)
        await async_session.commit()
        await async_session.refresh(root_node)

        budget_tree = BudgetTree(
            bank_account_id=bank_account.account_number,
            root_id=root_node.id,
        )
        async_session.add(budget_tree)
        await async_session.commit()
        await async_session.refresh(budget_tree)

        assert budget_tree.bank_account_id == bank_account.account_number
        assert budget_tree.root_id == root_node.id

    @pytest.mark.asyncio
    async def test_create_budget_tree_with_duplicate_bank_account(self, async_session):
        """Test that duplicate bank accounts for budget tree raise an error."""
        bank_account = BankAccount(account_number="123456", alias="Savings")
        async_session.add(bank_account)
        await async_session.commit()

        root_category = Category(
            name="Root",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="root",
        )
        async_session.add(root_category)
        await async_session.commit()

        root_node1 = BudgetTreeNode(category_id=root_category.id, amount=100)
        root_node2 = BudgetTreeNode(category_id=root_category.id, amount=200)
        async_session.add_all([root_node1, root_node2])
        await async_session.commit()
        await async_session.refresh(root_node1)
        await async_session.refresh(root_node2)

        budget_tree1 = BudgetTree(
            bank_account_id=bank_account.account_number,
            root_id=root_node1.id,
        )
        async_session.add(budget_tree1)
        await async_session.commit()

        budget_tree2 = BudgetTree(
            bank_account_id=bank_account.account_number,
            root_id=root_node2.id,
        )
        async_session.add(budget_tree2)

        with pytest.raises(IntegrityError):
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_budget_tree_str_method(self, async_session):
        """Test budget tree __str__ method."""
        budget_tree = BudgetTree(bank_account_id="123456")

        assert str(budget_tree) == "123456"
