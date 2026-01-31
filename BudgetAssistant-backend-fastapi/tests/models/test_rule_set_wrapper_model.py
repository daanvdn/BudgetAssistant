"""Tests for RuleSetWrapper model."""

import pytest
from enums import TransactionTypeEnum
from models import Category, RuleSetWrapper, User
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from tests.utils import assert_persisted


class TestRuleSetWrapper:
    """Test cases for the RuleSetWrapper model."""

    @pytest.mark.asyncio
    async def test_create_rule_set_wrapper_with_valid_data(self, async_session):
        """Test creating a rule set wrapper with valid data."""
        category = Category(
            name="Test Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="test",
        )
        async_session.add(category)
        await async_session.commit()
        await async_session.refresh(category)

        rule_set_dict = {
            "condition": "AND",
            "rules": [
                {
                    "field": ["communications"],
                    "field_type": "string",
                    "value": ["test"],
                    "operator": {
                        "name": "contains",
                        "value": "contains",
                        "type": "string",
                    },
                    "value_match_type": {"name": "any of", "value": "any of"},
                    "clazz": "Rule",
                    "type": "EXPENSES",
                }
            ],
            "is_child": False,
            "clazz": "RuleSet",
            "type": "EXPENSES",
        }

        rule_set_wrapper = RuleSetWrapper(
            category_id=category.id,
        )
        rule_set_wrapper.set_rule_set_from_dict(rule_set_dict)

        async_session.add(rule_set_wrapper)
        await async_session.commit()
        await async_session.refresh(rule_set_wrapper)

        assert rule_set_wrapper.id is not None
        assert rule_set_wrapper.category_id == category.id

        # Re-query from database to verify persistence and category relationship
        persisted = await assert_persisted(
            async_session,
            RuleSetWrapper,
            "id",
            rule_set_wrapper.id,
            {
                "category_id": category.id,
            },
        )
        # Verify rule_set_json was persisted correctly
        persisted_dict = persisted.get_rule_set_as_dict()
        assert persisted_dict["condition"] == "AND"
        assert len(persisted_dict["rules"]) == 1
        assert persisted_dict["clazz"] == "RuleSet"

    @pytest.mark.asyncio
    async def test_get_rule_set_as_dict(self, async_session):
        """Test getting rule set as dictionary."""
        category = Category(
            name="Test Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="test",
        )
        async_session.add(category)
        await async_session.commit()
        await async_session.refresh(category)

        rule_set_dict = {
            "condition": "OR",
            "rules": [],
            "is_child": True,
            "clazz": "RuleSet",
            "type": "EXPENSES",
        }

        rule_set_wrapper = RuleSetWrapper(category_id=category.id)
        rule_set_wrapper.set_rule_set_from_dict(rule_set_dict)

        async_session.add(rule_set_wrapper)
        await async_session.commit()
        await async_session.refresh(rule_set_wrapper)

        retrieved_dict = rule_set_wrapper.get_rule_set_as_dict()

        assert retrieved_dict["condition"] == "OR"
        assert retrieved_dict["is_child"] is True
        assert retrieved_dict["clazz"] == "RuleSet"

    @pytest.mark.asyncio
    async def test_get_rule_set_returns_typed_object(self, async_session):
        """Test getting rule set as strongly-typed RuleSet object."""
        from models.rules import RuleSet

        category = Category(
            name="Test Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="test",
        )
        async_session.add(category)
        await async_session.commit()
        await async_session.refresh(category)

        rule_set_dict = {
            "condition": "OR",
            "rules": [],
            "is_child": True,
            "clazz": "RuleSet",
            "type": "EXPENSES",
        }

        rule_set_wrapper = RuleSetWrapper(category_id=category.id)
        rule_set_wrapper.set_rule_set_from_dict(rule_set_dict)

        async_session.add(rule_set_wrapper)
        await async_session.commit()
        await async_session.refresh(rule_set_wrapper)

        rule_set = rule_set_wrapper.get_rule_set()

        assert rule_set is not None
        assert isinstance(rule_set, RuleSet)
        assert rule_set.condition == "OR"
        assert rule_set.is_child is True

    @pytest.mark.asyncio
    async def test_add_users_to_rule_set_wrapper(self, async_session):
        """Test adding users to a rule set wrapper."""
        category = Category(
            name="Test Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="test",
        )
        async_session.add(category)
        await async_session.commit()
        await async_session.refresh(category)

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="password",
        )
        async_session.add(user)
        await async_session.commit()
        user_id = user.id

        rule_set_wrapper = RuleSetWrapper(
            category_id=category.id,
            rule_set_json="{}",
        )
        rule_set_wrapper.users.append(user)
        async_session.add(rule_set_wrapper)
        await async_session.commit()
        await async_session.refresh(rule_set_wrapper)
        wrapper_id = rule_set_wrapper.id

        assert len(rule_set_wrapper.users) == 1
        assert rule_set_wrapper.users[0].username == "testuser"

        # Re-query from database to verify user relationship persistence
        result = await async_session.execute(
            select(RuleSetWrapper)
            .where(RuleSetWrapper.id == wrapper_id)
            .options(selectinload(RuleSetWrapper.users))
            .execution_options(populate_existing=True)
        )
        persisted_wrapper = result.scalar_one_or_none()

        assert persisted_wrapper is not None
        assert persisted_wrapper.category_id == category.id
        assert len(persisted_wrapper.users) == 1
        assert persisted_wrapper.users[0].id == user_id
        assert persisted_wrapper.users[0].username == "testuser"

    @pytest.mark.asyncio
    async def test_update_rule_set(self, async_session):
        """Test updating rule set in wrapper."""
        category = Category(
            name="Test Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="test",
        )
        async_session.add(category)
        await async_session.commit()
        await async_session.refresh(category)

        initial_rule_set = {
            "condition": "AND",
            "rules": [],
            "is_child": False,
            "clazz": "RuleSet",
            "type": "EXPENSES",
        }
        rule_set_wrapper = RuleSetWrapper(category_id=category.id)
        rule_set_wrapper.set_rule_set_from_dict(initial_rule_set)

        async_session.add(rule_set_wrapper)
        await async_session.commit()

        new_rule_set = {
            "condition": "OR",
            "rules": [],
            "is_child": False,
            "clazz": "RuleSet",
            "type": "EXPENSES",
        }
        rule_set_wrapper.set_rule_set_from_dict(new_rule_set)
        await async_session.commit()
        await async_session.refresh(rule_set_wrapper)

        retrieved_dict = rule_set_wrapper.get_rule_set_as_dict()
        assert retrieved_dict["condition"] == "OR"

    @pytest.mark.asyncio
    async def test_empty_rule_set(self, async_session):
        """Test handling of empty rule set."""
        category = Category(
            name="Test Category",
            type=TransactionTypeEnum.EXPENSES,
            qualified_name="test",
        )
        async_session.add(category)
        await async_session.commit()
        await async_session.refresh(category)

        rule_set_wrapper = RuleSetWrapper(
            category_id=category.id,
            rule_set_json="{}",
        )
        async_session.add(rule_set_wrapper)
        await async_session.commit()

        # get_rule_set_as_dict returns empty dict
        result_dict = rule_set_wrapper.get_rule_set_as_dict()
        assert result_dict == {}

        # get_rule_set returns None for empty rule set
        result_typed = rule_set_wrapper.get_rule_set()
        assert result_typed is None
