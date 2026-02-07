"""Tests for RuleService.get_or_create_all_rule_set_wrappers."""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.enums import TransactionTypeEnum
from models import Category, RuleSetWrapper, User
from models.associations import UserRuleSetLink
from services.rule_service import RuleService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def user(async_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(email="ruletest@example.com", password_hash="hashed_password123")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_user(async_session: AsyncSession) -> User:
    """Create a second test user."""
    user = User(email="ruletest2@example.com", password_hash="hashed_password456")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def expense_categories(async_session: AsyncSession) -> list[Category]:
    """Create expense categories."""
    root = Category(
        name="Expenses",
        qualified_name="Expenses",
        is_root=True,
        type=TransactionTypeEnum.EXPENSES,
    )
    async_session.add(root)
    await async_session.flush()

    groceries = Category(
        name="Groceries",
        qualified_name="Expenses > Groceries",
        is_root=False,
        type=TransactionTypeEnum.EXPENSES,
        parent_id=root.id,
    )
    transport = Category(
        name="Transport",
        qualified_name="Expenses > Transport",
        is_root=False,
        type=TransactionTypeEnum.EXPENSES,
        parent_id=root.id,
    )
    async_session.add_all([groceries, transport])
    await async_session.commit()
    await async_session.refresh(root)
    await async_session.refresh(groceries)
    await async_session.refresh(transport)
    return [root, groceries, transport]


@pytest_asyncio.fixture
async def revenue_categories(async_session: AsyncSession) -> list[Category]:
    """Create revenue categories."""
    root = Category(
        name="Revenue",
        qualified_name="Revenue",
        is_root=True,
        type=TransactionTypeEnum.REVENUE,
    )
    async_session.add(root)
    await async_session.flush()

    salary = Category(
        name="Salary",
        qualified_name="Revenue > Salary",
        is_root=False,
        type=TransactionTypeEnum.REVENUE,
        parent_id=root.id,
    )
    async_session.add(salary)
    await async_session.commit()
    await async_session.refresh(root)
    await async_session.refresh(salary)
    return [root, salary]


@pytest.fixture
def service() -> RuleService:
    return RuleService()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetOrCreateAllRuleSetWrappers:
    """Tests for RuleService.get_or_create_all_rule_set_wrappers."""

    @pytest.mark.asyncio
    async def test_creates_wrappers_for_all_categories(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
        expense_categories: list[Category],
        revenue_categories: list[Category],
    ):
        """When no wrappers exist yet, one is created per category."""
        result = await service.get_or_create_all_rule_set_wrappers(user, async_session)

        total_categories = len(expense_categories) + len(revenue_categories)

        # Flatten all wrappers across types
        all_wrappers = {qn: w for type_dict in result.values() for qn, w in type_dict.items()}
        assert len(all_wrappers) == total_categories

    @pytest.mark.asyncio
    async def test_returns_correct_type_grouping(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
        expense_categories: list[Category],
        revenue_categories: list[Category],
    ):
        """Result is correctly split into EXPENSES and REVENUE."""
        result = await service.get_or_create_all_rule_set_wrappers(user, async_session)

        assert TransactionTypeEnum.EXPENSES in result
        assert TransactionTypeEnum.REVENUE in result
        assert len(result[TransactionTypeEnum.EXPENSES]) == len(expense_categories)
        assert len(result[TransactionTypeEnum.REVENUE]) == len(revenue_categories)

    @pytest.mark.asyncio
    async def test_keys_are_qualified_names(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
        expense_categories: list[Category],
        revenue_categories: list[Category],
    ):
        """Wrappers are keyed by the category qualified_name."""
        result = await service.get_or_create_all_rule_set_wrappers(user, async_session)

        expense_qnames = {c.qualified_name for c in expense_categories}
        revenue_qnames = {c.qualified_name for c in revenue_categories}

        assert set(result[TransactionTypeEnum.EXPENSES].keys()) == expense_qnames
        assert set(result[TransactionTypeEnum.REVENUE].keys()) == revenue_qnames

    @pytest.mark.asyncio
    async def test_creates_user_links_for_all_wrappers(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
        expense_categories: list[Category],
        revenue_categories: list[Category],
    ):
        """Every wrapper should be linked to the user."""
        await service.get_or_create_all_rule_set_wrappers(user, async_session)

        links_result = await async_session.execute(select(UserRuleSetLink).where(UserRuleSetLink.user_id == user.id))
        links = links_result.scalars().all()
        total_categories = len(expense_categories) + len(revenue_categories)
        assert len(links) == total_categories

    @pytest.mark.asyncio
    async def test_idempotent_no_duplicate_wrappers(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
        expense_categories: list[Category],
        revenue_categories: list[Category],
    ):
        """Calling twice does not create duplicate wrappers."""
        await service.get_or_create_all_rule_set_wrappers(user, async_session)
        await service.get_or_create_all_rule_set_wrappers(user, async_session)

        wrappers_result = await async_session.execute(select(RuleSetWrapper))
        wrappers = wrappers_result.scalars().all()
        total_categories = len(expense_categories) + len(revenue_categories)
        assert len(wrappers) == total_categories

    @pytest.mark.asyncio
    async def test_idempotent_no_duplicate_links(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
        expense_categories: list[Category],
        revenue_categories: list[Category],
    ):
        """Calling twice does not create duplicate user links."""
        await service.get_or_create_all_rule_set_wrappers(user, async_session)
        await service.get_or_create_all_rule_set_wrappers(user, async_session)

        links_result = await async_session.execute(select(UserRuleSetLink).where(UserRuleSetLink.user_id == user.id))
        links = links_result.scalars().all()
        total_categories = len(expense_categories) + len(revenue_categories)
        assert len(links) == total_categories

    @pytest.mark.asyncio
    async def test_reuses_existing_wrappers(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
        expense_categories: list[Category],
    ):
        """Pre-existing wrappers are reused, not recreated."""
        cat = expense_categories[0]
        existing = RuleSetWrapper(
            category_id=cat.id,
            rule_set_json='{"condition":"OR","rules":[]}',
        )
        async_session.add(existing)
        await async_session.commit()
        await async_session.refresh(existing)

        result = await service.get_or_create_all_rule_set_wrappers(user, async_session)

        returned_wrapper = result[TransactionTypeEnum.EXPENSES][cat.qualified_name]
        assert returned_wrapper.id == existing.id
        assert returned_wrapper.rule_set_json == '{"condition":"OR","rules":[]}'

    @pytest.mark.asyncio
    async def test_new_wrappers_have_empty_rule_set(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
        expense_categories: list[Category],
    ):
        """Newly created wrappers have an empty JSON rule set."""
        result = await service.get_or_create_all_rule_set_wrappers(user, async_session)

        for wrapper in result[TransactionTypeEnum.EXPENSES].values():
            assert wrapper.get_rule_set_as_dict() == {}

    @pytest.mark.asyncio
    async def test_second_user_gets_links_to_same_wrappers(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
        second_user: User,
        expense_categories: list[Category],
    ):
        """A second user calling the method gets linked to the same wrappers."""
        result1 = await service.get_or_create_all_rule_set_wrappers(user, async_session)
        result2 = await service.get_or_create_all_rule_set_wrappers(second_user, async_session)

        # Same wrapper IDs for both users
        ids1 = {w.id for w in result1[TransactionTypeEnum.EXPENSES].values()}
        ids2 = {w.id for w in result2[TransactionTypeEnum.EXPENSES].values()}
        assert ids1 == ids2

        # Both users have links
        for uid in (user.id, second_user.id):
            links_result = await async_session.execute(select(UserRuleSetLink).where(UserRuleSetLink.user_id == uid))
            assert len(links_result.scalars().all()) == len(expense_categories)

    @pytest.mark.asyncio
    async def test_no_categories_returns_empty(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
    ):
        """When no categories exist, the result is empty."""
        result = await service.get_or_create_all_rule_set_wrappers(user, async_session)
        # defaultdict so access doesn't fail, but all should be empty
        total = sum(len(d) for d in result.values())
        assert total == 0

    @pytest.mark.asyncio
    async def test_wrapper_category_id_matches(
        self,
        async_session: AsyncSession,
        service: RuleService,
        user: User,
        expense_categories: list[Category],
    ):
        """Each returned wrapper's category_id matches the category it maps to."""
        result = await service.get_or_create_all_rule_set_wrappers(user, async_session)

        for cat in expense_categories:
            wrapper = result[TransactionTypeEnum.EXPENSES][cat.qualified_name]
            assert wrapper.category_id == cat.id
