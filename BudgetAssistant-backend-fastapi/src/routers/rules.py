"""Rules router for rule set management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from enums import TransactionTypeEnum
from models import Category, RuleSetWrapper
from models.associations import UserRuleSetLink
from routers.auth import CurrentUser
from schemas import (
    CategorizeTransactionsResponse,
    GetOrCreateRuleSetWrapperRequest,
    RuleSetWrapperCreate,
    RuleSetWrapperRead,
    RuleSetWrapperUpdate,
    SuccessResponse,
)

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.post("/get-or-create", response_model=RuleSetWrapperRead)
async def get_or_create_rule_set_wrapper(
    request: GetOrCreateRuleSetWrapperRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> RuleSetWrapperRead:
    """Get or create a rule set wrapper for a category."""
    # Find the category by qualified name
    category_result = await session.execute(
        select(Category).where(
            Category.qualified_name == request.category_qualified_name
        )
    )
    category = category_result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category '{request.category_qualified_name}' not found",
        )

    # Check if rule set wrapper exists for this category
    result = await session.execute(
        select(RuleSetWrapper).where(RuleSetWrapper.category_id == category.id)
    )
    rule_set_wrapper = result.scalar_one_or_none()

    if not rule_set_wrapper:
        # Create new rule set wrapper
        rule_set_wrapper = RuleSetWrapper(
            category_id=category.id,
            rule_set_json="{}",
        )
        session.add(rule_set_wrapper)
        await session.flush()

        # Associate with user
        link = UserRuleSetLink(
            user_id=current_user.id,
            rule_set_wrapper_id=rule_set_wrapper.id,
        )
        session.add(link)
        await session.commit()
        await session.refresh(rule_set_wrapper)
    else:
        # Check if user is already associated
        link_result = await session.execute(
            select(UserRuleSetLink).where(
                UserRuleSetLink.user_id == current_user.id,
                UserRuleSetLink.rule_set_wrapper_id == rule_set_wrapper.id,
            )
        )
        if not link_result.scalar_one_or_none():
            link = UserRuleSetLink(
                user_id=current_user.id,
                rule_set_wrapper_id=rule_set_wrapper.id,
            )
            session.add(link)
            await session.commit()

    return RuleSetWrapperRead(
        id=rule_set_wrapper.id,
        category_id=rule_set_wrapper.category_id,
        rule_set=rule_set_wrapper.get_rule_set_dict(),
    )


@router.post("/save", response_model=SuccessResponse)
async def save_rule_set_wrapper(
    rule_set_wrapper: RuleSetWrapperCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Save a rule set wrapper."""
    # Check category exists
    category_result = await session.execute(
        select(Category).where(Category.id == rule_set_wrapper.category_id)
    )
    category = category_result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Check if rule set wrapper exists
    result = await session.execute(
        select(RuleSetWrapper).where(
            RuleSetWrapper.category_id == rule_set_wrapper.category_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.set_rule_set_dict(rule_set_wrapper.rule_set)
        await session.commit()
    else:
        # Create new
        new_wrapper = RuleSetWrapper(category_id=rule_set_wrapper.category_id)
        new_wrapper.set_rule_set_dict(rule_set_wrapper.rule_set)
        session.add(new_wrapper)
        await session.flush()

        # Associate with user
        link = UserRuleSetLink(
            user_id=current_user.id,
            rule_set_wrapper_id=new_wrapper.id,
        )
        session.add(link)
        await session.commit()

    return SuccessResponse(message="Rule set saved successfully")


@router.patch("/{rule_set_id}", response_model=RuleSetWrapperRead)
async def update_rule_set_wrapper(
    rule_set_id: int,
    update: RuleSetWrapperUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> RuleSetWrapperRead:
    """Update a rule set wrapper."""
    # Get the rule set wrapper
    result = await session.execute(
        select(RuleSetWrapper).where(RuleSetWrapper.id == rule_set_id)
    )
    rule_set_wrapper = result.scalar_one_or_none()

    if not rule_set_wrapper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule set wrapper not found",
        )

    # Check user has access
    link_result = await session.execute(
        select(UserRuleSetLink).where(
            UserRuleSetLink.user_id == current_user.id,
            UserRuleSetLink.rule_set_wrapper_id == rule_set_id,
        )
    )
    if not link_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this rule set",
        )

    # Update
    if update.rule_set is not None:
        rule_set_wrapper.set_rule_set_dict(update.rule_set)

    await session.commit()
    await session.refresh(rule_set_wrapper)

    return RuleSetWrapperRead(
        id=rule_set_wrapper.id,
        category_id=rule_set_wrapper.category_id,
        rule_set=rule_set_wrapper.get_rule_set_dict(),
    )


@router.get("/{rule_set_id}", response_model=RuleSetWrapperRead)
async def get_rule_set_wrapper(
    rule_set_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> RuleSetWrapperRead:
    """Get a rule set wrapper by ID."""
    # Get the rule set wrapper
    result = await session.execute(
        select(RuleSetWrapper).where(RuleSetWrapper.id == rule_set_id)
    )
    rule_set_wrapper = result.scalar_one_or_none()

    if not rule_set_wrapper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule set wrapper not found",
        )

    return RuleSetWrapperRead(
        id=rule_set_wrapper.id,
        category_id=rule_set_wrapper.category_id,
        rule_set=rule_set_wrapper.get_rule_set_dict(),
    )


@router.post("/categorize-transactions", response_model=CategorizeTransactionsResponse)
async def categorize_transactions(
    bank_account: str,
    transaction_type: TransactionTypeEnum,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> CategorizeTransactionsResponse:
    """Apply rules to categorize transactions.

    Note: This is a placeholder. The actual implementation would use
    the RuleBasedCategorizer service.
    """
    # TODO: Implement actual categorization using RuleBasedCategorizer

    return CategorizeTransactionsResponse(
        message="Categorization complete",
        with_category_count=0,
        without_category_count=0,
    )

