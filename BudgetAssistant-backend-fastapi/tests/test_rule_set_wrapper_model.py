"""Tests for RuleSetWrapper model."""

import pytest
from sqlalchemy import select

from models import RuleSetWrapper, Category, User
from enums import TransactionTypeEnum


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
                    "operator": {"name": "contains", "value": "contains", "type": "string"},
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
        rule_set_wrapper.set_rule_set_dict(rule_set_dict)

        async_session.add(rule_set_wrapper)
        await async_session.commit()
        await async_session.refresh(rule_set_wrapper)

        assert rule_set_wrapper.id is not None
        assert rule_set_wrapper.category_id == category.id

    @pytest.mark.asyncio
    async def test_get_rule_set_dict(self, async_session):
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
        rule_set_wrapper.set_rule_set_dict(rule_set_dict)

        async_session.add(rule_set_wrapper)
        await async_session.commit()
        await async_session.refresh(rule_set_wrapper)

        retrieved_dict = rule_set_wrapper.get_rule_set_dict()

        assert retrieved_dict["condition"] == "OR"
        assert retrieved_dict["is_child"] is True
        assert retrieved_dict["clazz"] == "RuleSet"

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

        rule_set_wrapper = RuleSetWrapper(
            category_id=category.id,
            rule_set_json="{}",
        )
        rule_set_wrapper.users.append(user)
        async_session.add(rule_set_wrapper)
        await async_session.commit()
        await async_session.refresh(rule_set_wrapper)

        assert len(rule_set_wrapper.users) == 1
        assert rule_set_wrapper.users[0].username == "testuser"

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

        initial_rule_set = {"condition": "AND", "rules": []}
        rule_set_wrapper = RuleSetWrapper(category_id=category.id)
        rule_set_wrapper.set_rule_set_dict(initial_rule_set)

        async_session.add(rule_set_wrapper)
        await async_session.commit()

        new_rule_set = {"condition": "OR", "rules": [{"test": "value"}]}
        rule_set_wrapper.set_rule_set_dict(new_rule_set)
        await async_session.commit()
        await async_session.refresh(rule_set_wrapper)

        retrieved_dict = rule_set_wrapper.get_rule_set_dict()
        assert retrieved_dict["condition"] == "OR"
        assert len(retrieved_dict["rules"]) == 1

    @pytest.mark.asyncio
    async def test_empty_rule_set_dict(self, async_session):
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

        result = rule_set_wrapper.get_rule_set_dict()
        assert result == {}
