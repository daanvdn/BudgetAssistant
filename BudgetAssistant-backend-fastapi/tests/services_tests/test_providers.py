"""Tests for category and budget tree providers."""

import importlib.resources as pkg_resources

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.enums import TransactionTypeEnum
from models import BankAccount, BudgetTree, BudgetTreeNode, Category
from services.providers import (
    BudgetTreeProvider,
    CategoryTreeInserter,
    CategoryTreeProvider,
)


def load_expenses_categories_from_file() -> list[str]:
    """Load expected category names from resource file."""
    with (
        pkg_resources.files("resources")
        .joinpath("categories-expenses.txt")
        .open(encoding="utf-8") as file
    ):
        lines = file.read().split("\n")
        lines = [line.strip() for line in lines if line.strip()]
        lines.append(Category.NO_CATEGORY_NAME)
        lines.append(Category.DUMMY_CATEGORY_NAME)
        return lines


def load_revenue_categories_from_file() -> list[str]:
    """Load expected category names from revenue resource file."""
    with (
        pkg_resources.files("resources")
        .joinpath("categories-revenue.txt")
        .open(encoding="utf-8") as file
    ):
        lines = file.read().split("\n")
        lines = [line.strip() for line in lines if line.strip()]
        lines.append(Category.NO_CATEGORY_NAME)
        lines.append(Category.DUMMY_CATEGORY_NAME)
        return lines


class TestCategoryTreeInserter:
    """Tests for CategoryTreeInserter."""

    @pytest.mark.asyncio
    async def test_run_creates_category_tree_with_root(
        self, async_session: AsyncSession
    ):
        """Test that run() creates a category tree with a root node."""
        inserter = CategoryTreeInserter()
        tree = await inserter.run(TransactionTypeEnum.EXPENSES, async_session)
        await async_session.commit()

        assert tree is not None
        assert tree.root is not None
        assert tree.root.name == Category.ROOT_NAME
        assert tree.root.is_root is True

    @pytest.mark.asyncio
    async def test_run_creates_no_category_and_dummy_category(
        self, async_session: AsyncSession
    ):
        """Test that run() creates NO CATEGORY and DUMMY CATEGORY."""
        inserter = CategoryTreeInserter()
        tree = await inserter.run(TransactionTypeEnum.EXPENSES, async_session)
        await async_session.commit()

        # Refresh root to load children
        await async_session.refresh(tree.root, ["children"])

        child_names = [child.name for child in tree.root.children]
        assert Category.NO_CATEGORY_NAME in child_names
        assert Category.DUMMY_CATEGORY_NAME in child_names

    @pytest.mark.asyncio
    async def test_run_invalid_type_raises_value_error(
        self, async_session: AsyncSession
    ):
        """Test that run() raises ValueError for invalid transaction type."""
        inserter = CategoryTreeInserter()
        with pytest.raises(ValueError, match="Invalid category tree type"):
            await inserter.run(TransactionTypeEnum.BOTH, async_session)

    @pytest.mark.asyncio
    async def test_expenses_tree_qualified_names(self, async_session: AsyncSession):
        """Test that expenses tree has correct qualified names."""
        expected_qualified_names = {
            "belastingen",
            "belastingen#KI",
            "belastingen#verkeersbelasting",
            "belastingen#boekhouder",
            "belastingen#personenbelasting",
            "belastingen#provinciebelasting",
            "belastingen#gemeentebelasting",
            "energie",
            "energie#gas & elektriciteit",
            "energie#water",
            "bankkosten",
            "leningen",
            "leningen#woonlening",
            "verzekeringen",
            "verzekeringen#brand- en familiale verzekering",
            "verzekeringen#schuldsaldo",
            "verzekeringen#autoverzekering",
            "verzekeringen#hospitalisatieverzekering",
            "auto & vervoer",
            "auto & vervoer#autoverzekering",
            "auto & vervoer#benzine",
            "auto & vervoer#parkeren",
            "auto & vervoer#onderhoud & herstelling",
            "auto & vervoer#trein",
            "kinderen",
            "kinderen#kinderopvang",
            "kinderen#school",
            "kinderen#school#boeken/materiaal",
            "kinderen#school#schoolreis",
            "kinderen#school#middagmaal",
            "kinderen#kleding",
            "kinderen#uitrusting",
            "kinderen#speelgoed",
            "kledij & verzorging",
            "kledij & verzorging#accessoires",
            "kledij & verzorging#kapper",
            "kledij & verzorging#schoenen",
            "kledij & verzorging#kleren",
            "wonen",
            "wonen#meubelen & accessoires",
            "wonen#poetsdienst",
            "wonen#tuin",
            "wonen#renovaties",
            "wonen#loodgieter",
            "wonen#chauffage",
            "wonen#keuken",
            "wonen#electro",
            "huishouden",
            "huishouden#boodschappen",
            "huishouden#boodschappen#bakker",
            "huishouden#boodschappen#slager",
            "huishouden#boodschappen#supermarkt",
            "huishouden#boodschappen#supermarkt#colruyt",
            "huishouden#lunch werk",
            "medisch",
            "medisch#dokter",
            "medisch#kinesist",
            "medisch#apotheek",
            "medisch#mutualiteit",
            "medisch#ziekenhuis",
            "medisch#dierenarts",
            "medisch#tandarts",
            "telecom",
            "telecom#internet & tv",
            "telecom#telefonie",
            "vrije tijd",
            "vrije tijd#restaurant",
            "vrije tijd#café",
            "vrije tijd#uitgaan",
            "vrije tijd#hobby",
            "vrije tijd#reizen",
            "giften",
            "giften#cadeau's",
            "vakbond",
            "sparen",
            "sparen#pensioensparen",
            "sparen#algemeen",
            "cash geldopname",
            "kredietkaart",
            "gemeenschappelijke kosten",
            "webshops",
            Category.NO_CATEGORY_NAME,
            Category.DUMMY_CATEGORY_NAME,
        }

        inserter = CategoryTreeInserter()
        _tree = await inserter.run(TransactionTypeEnum.EXPENSES, async_session)
        await async_session.commit()

        # Get all categories from database
        result = await async_session.execute(
            select(Category).where(Category.type == TransactionTypeEnum.EXPENSES.value)
        )
        all_categories = result.scalars().all()

        # Extract qualified names (excluding root)
        actual_qualified_names = {
            cat.qualified_name for cat in all_categories if not cat.is_root
        }

        assert expected_qualified_names == actual_qualified_names

    @pytest.mark.asyncio
    async def test_run_creates_revenue_tree(self, async_session: AsyncSession):
        """Test that run() creates a revenue category tree."""
        inserter = CategoryTreeInserter()
        tree = await inserter.run(TransactionTypeEnum.REVENUE, async_session)
        await async_session.commit()

        assert tree is not None
        assert tree.root is not None
        assert tree.root.name == Category.ROOT_NAME
        assert tree.type == TransactionTypeEnum.REVENUE


class TestCategoryTreeProvider:
    """Tests for CategoryTreeProvider."""

    @pytest.mark.asyncio
    async def test_provide_creates_category_tree(self, async_session: AsyncSession):
        """Test that provide() creates a category tree if one doesn't exist."""
        provider = CategoryTreeProvider()
        tree = await provider.provide(TransactionTypeEnum.EXPENSES, async_session)
        await async_session.commit()

        assert tree is not None
        assert tree.root is not None
        assert tree.root.name == Category.ROOT_NAME
        assert tree.root.is_root is True

        # Verify all expected categories exist
        expected_categories = load_expenses_categories_from_file()

        # Get all descendant category names
        result = await async_session.execute(
            select(Category).where(
                Category.type == TransactionTypeEnum.EXPENSES.value,
                Category.is_root == False,
            )
        )
        actual_categories = [cat.name for cat in result.scalars().all()]

        # Sort both lists for comparison
        expected_categories.sort()
        actual_categories.sort()

        assert set(expected_categories) == set(actual_categories)

    @pytest.mark.asyncio
    async def test_provide_returns_existing_tree(self, async_session: AsyncSession):
        """Test that provide() returns existing tree instead of creating new one."""
        provider = CategoryTreeProvider()

        # Create first tree
        tree1 = await provider.provide(TransactionTypeEnum.EXPENSES, async_session)
        await async_session.commit()

        tree1_id = tree1.id

        # Provide again - should return same tree
        tree2 = await provider.provide(TransactionTypeEnum.EXPENSES, async_session)

        assert tree2.id == tree1_id

    @pytest.mark.asyncio
    async def test_provide_invalid_type_raises_error(self, async_session: AsyncSession):
        """Test that provide() raises ValueError for BOTH type."""
        provider = CategoryTreeProvider()

        with pytest.raises(ValueError, match="Invalid category tree type"):
            await provider.provide(TransactionTypeEnum.BOTH, async_session)

    @pytest.mark.asyncio
    async def test_provide_creates_no_category_and_dummy(
        self, async_session: AsyncSession
    ):
        """Test that provide() creates NO CATEGORY and DUMMY CATEGORY."""
        provider = CategoryTreeProvider()
        tree = await provider.provide(TransactionTypeEnum.EXPENSES, async_session)
        await async_session.commit()

        # Find NO CATEGORY and DUMMY CATEGORY
        no_cat_result = await async_session.execute(
            select(Category).where(Category.name == Category.NO_CATEGORY_NAME)
        )
        no_category = no_cat_result.scalar_one_or_none()

        dummy_result = await async_session.execute(
            select(Category).where(Category.name == Category.DUMMY_CATEGORY_NAME)
        )
        dummy_category = dummy_result.scalar_one_or_none()

        assert no_category is not None
        assert dummy_category is not None
        assert no_category.parent_id == tree.root.id
        assert dummy_category.parent_id == tree.root.id


class TestBudgetTreeProvider:
    """Tests for BudgetTreeProvider."""

    @pytest.mark.asyncio
    async def test_provide_creates_budget_tree(self, async_session: AsyncSession):
        """Test that provide() creates a budget tree for a bank account."""
        # First create category tree (required for budget tree)
        cat_provider = CategoryTreeProvider()
        await cat_provider.provide(TransactionTypeEnum.EXPENSES, async_session)
        await async_session.commit()

        # Create bank account
        bank_account = BankAccount(account_number="123456789", alias="Test Account")
        async_session.add(bank_account)
        await async_session.flush()

        # Create budget tree
        provider = BudgetTreeProvider()
        budget_tree = await provider.provide(bank_account, async_session)
        await async_session.commit()

        assert budget_tree is not None
        assert budget_tree.root is not None
        assert budget_tree.bank_account_id == "123456789"
        assert budget_tree.root.category.name == Category.ROOT_NAME
        assert budget_tree.root.category.is_root is True

    @pytest.mark.asyncio
    async def test_provide_returns_existing_budget_tree(
        self, async_session: AsyncSession
    ):
        """Test that provide() returns existing budget tree."""
        # Create category tree
        cat_provider = CategoryTreeProvider()
        expenses_tree = await cat_provider.provide(
            TransactionTypeEnum.EXPENSES, async_session
        )
        await async_session.commit()

        # Create bank account
        bank_account = BankAccount(account_number="987654321", alias="Test Account 2")
        async_session.add(bank_account)
        await async_session.flush()

        # Create budget tree manually
        root_node = BudgetTreeNode(
            category_id=expenses_tree.root.id,
            amount=-1,
        )
        async_session.add(root_node)
        await async_session.flush()

        existing_tree = BudgetTree(
            bank_account_id=bank_account.account_number,
            root_id=root_node.id,
            number_of_descendants=1,
        )
        async_session.add(existing_tree)
        await async_session.commit()

        # Provide should return existing tree
        provider = BudgetTreeProvider()
        budget_tree = await provider.provide(bank_account, async_session)

        assert budget_tree.bank_account_id == existing_tree.bank_account_id

    @pytest.mark.asyncio
    async def test_budget_tree_mirrors_category_structure(
        self, async_session: AsyncSession
    ):
        """Test that budget tree mirrors the category tree structure."""
        # Create category tree
        cat_provider = CategoryTreeProvider()
        _expenses_tree = await cat_provider.provide(
            TransactionTypeEnum.EXPENSES, async_session
        )
        await async_session.commit()

        # Create bank account
        bank_account = BankAccount(account_number="111222333", alias="Mirror Test")
        async_session.add(bank_account)
        await async_session.flush()

        # Create budget tree
        provider = BudgetTreeProvider()
        _budget_tree = await provider.provide(bank_account, async_session)
        await async_session.commit()

        # Get all categories
        cat_result = await async_session.execute(
            select(Category).where(Category.type == TransactionTypeEnum.EXPENSES.value)
        )
        all_categories = {cat.qualified_name: cat for cat in cat_result.scalars().all()}

        # Get all budget tree nodes
        node_result = await async_session.execute(select(BudgetTreeNode))
        all_nodes = node_result.scalars().all()

        # Build dict of budget tree nodes by category qualified name
        budget_nodes = {}
        for node in all_nodes:
            if node.category_id:
                cat = await async_session.get(Category, node.category_id)
                if cat:
                    budget_nodes[cat.qualified_name] = node

        # Verify all categories have corresponding budget nodes
        assert len(all_categories) > 0
        assert len(budget_nodes) > 0
        assert set(all_categories.keys()) == set(budget_nodes.keys())

    @pytest.mark.asyncio
    async def test_budget_tree_root_has_negative_amount(
        self, async_session: AsyncSession
    ):
        """Test that budget tree root node has amount of -1."""
        # Create category tree
        cat_provider = CategoryTreeProvider()
        await cat_provider.provide(TransactionTypeEnum.EXPENSES, async_session)
        await async_session.commit()

        # Create bank account
        bank_account = BankAccount(account_number="444555666", alias="Amount Test")
        async_session.add(bank_account)
        await async_session.flush()

        # Create budget tree
        provider = BudgetTreeProvider()
        budget_tree = await provider.provide(bank_account, async_session)
        await async_session.commit()

        assert budget_tree.root.amount == -1

    @pytest.mark.asyncio
    async def test_budget_tree_children_have_zero_amount(
        self, async_session: AsyncSession
    ):
        """Test that budget tree child nodes have amount of 0."""
        # Create category tree
        cat_provider = CategoryTreeProvider()
        await cat_provider.provide(TransactionTypeEnum.EXPENSES, async_session)
        await async_session.commit()

        # Create bank account
        bank_account = BankAccount(
            account_number="777888999", alias="Child Amount Test"
        )
        async_session.add(bank_account)
        await async_session.flush()

        # Create budget tree
        provider = BudgetTreeProvider()
        _budget_tree = await provider.provide(bank_account, async_session)
        await async_session.commit()

        # Get all non-root nodes
        result = await async_session.execute(
            select(BudgetTreeNode).where(BudgetTreeNode.parent_id != None)  # noqa: E711
        )
        child_nodes = result.scalars().all()

        assert len(child_nodes) > 0
        for node in child_nodes:
            assert node.amount == 0

    @pytest.mark.asyncio
    async def test_number_of_descendants_is_correct(self, async_session: AsyncSession):
        """Test that number_of_descendants is correctly calculated."""
        # Create category tree
        cat_provider = CategoryTreeProvider()
        await cat_provider.provide(TransactionTypeEnum.EXPENSES, async_session)
        await async_session.commit()

        # Create bank account
        bank_account = BankAccount(account_number="000111222", alias="Descendants Test")
        async_session.add(bank_account)
        await async_session.flush()

        # Create budget tree
        provider = BudgetTreeProvider()
        budget_tree = await provider.provide(bank_account, async_session)
        await async_session.commit()

        # Count actual nodes
        result = await async_session.execute(select(BudgetTreeNode))
        actual_count = len(result.scalars().all())

        assert budget_tree.number_of_descendants == actual_count
