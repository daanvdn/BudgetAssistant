"""Rule service with async SQLModel operations."""

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enums import TransactionTypeEnum
from models import Category, RuleSetWrapper, User
from models.associations import UserRuleSetLink


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

        rule_set_wrapper.set_rule_set_dict(rule_set)
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
            select(UserRuleSetLink)
            .where(UserRuleSetLink.rule_set_wrapper_id == rule_set_id)
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
        rule_set_wrapper.set_rule_set_dict(rule_set)
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


# Singleton instance
rule_service = RuleService()

