"""Rules router for rule set management."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import CurrentUser
from common.enums import TransactionTypeEnum
from db.database import get_session
from schemas import (
    CategorizeTransactionsResponse,
    GetOrCreateRuleSetWrapperRequest,
    RuleSetWrapperCreate,
    RuleSetWrapperRead,
    RuleSetWrapperUpdate,
    SuccessResponse,
)
from schemas.rule_set_wrapper import RuleSetWrapperBatchRead
from services.category_service import category_service
from services.rule_service import rule_service

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.post("/get-or-create", response_model=RuleSetWrapperRead)
async def get_or_create_rule_set_wrapper(
    request: GetOrCreateRuleSetWrapperRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> RuleSetWrapperRead:
    """Get or create a rule set wrapper for a category."""
    try:
        rule_set_wrapper = await rule_service.get_or_create_rule_set_wrapper(
            category_qualified_name=request.category_qualified_name,
            transaction_type=request.type,
            user=current_user,
            session=session,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return RuleSetWrapperRead(
        id=rule_set_wrapper.id,
        category_id=rule_set_wrapper.category_id,
        rule_set=rule_set_wrapper.get_rule_set_as_dict(),
    )


@router.post("/get-or-create-all", response_model=RuleSetWrapperBatchRead)
async def get_or_create_all_rule_set_wrappers(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> RuleSetWrapperBatchRead:
    """Get or create rule set wrappers for all categories."""
    grouped = await rule_service.get_or_create_all_rule_set_wrappers(
        user=current_user,
        session=session,
    )

    def _to_read_map(
        wrappers: dict[str, Any],
    ) -> dict[str, RuleSetWrapperRead]:
        return {
            qn: RuleSetWrapperRead(
                id=w.id,
                category_id=w.category_id,
                rule_set=w.get_rule_set_as_dict(),
            )
            for qn, w in wrappers.items()
        }

    return RuleSetWrapperBatchRead(
        expenses_rules=_to_read_map(grouped.get(TransactionTypeEnum.EXPENSES, {})),
        revenue_rules=_to_read_map(grouped.get(TransactionTypeEnum.REVENUE, {})),
    )


@router.post("/save", response_model=SuccessResponse)
async def save_rule_set_wrapper(
    rule_set_wrapper_in: RuleSetWrapperCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Save a rule set wrapper."""
    # Check category exists via service
    category = await category_service.get_category_by_id(rule_set_wrapper_in.category_id, session)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Check if rule set wrapper exists for this category
    existing = await rule_service.get_rule_set_wrapper_by_category(rule_set_wrapper_in.category_id, session)

    if existing:
        # Update existing via service
        await rule_service.update_rule_set(
            rule_set_id=existing.id,
            rule_set=rule_set_wrapper_in.rule_set,
            session=session,
        )
    else:
        # Create new via service
        await rule_service.create_rule_set_wrapper(
            category_id=rule_set_wrapper_in.category_id,
            rule_set=rule_set_wrapper_in.rule_set,
            user=current_user,
            session=session,
        )

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
    rule_set_wrapper = await rule_service.get_rule_set_wrapper(rule_set_id, session)

    if not rule_set_wrapper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule set wrapper not found",
        )

    # Check user has access
    if not await rule_service.user_has_access(current_user, rule_set_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this rule set",
        )

    # Update via service
    if update.rule_set is not None:
        rule_set_wrapper = await rule_service.update_rule_set(
            rule_set_id=rule_set_id,
            rule_set=update.rule_set,
            session=session,
        )

    return RuleSetWrapperRead(
        id=rule_set_wrapper.id,
        category_id=rule_set_wrapper.category_id,
        rule_set=rule_set_wrapper.get_rule_set_as_dict(),
    )


@router.get("/{rule_set_id}", response_model=RuleSetWrapperRead)
async def get_rule_set_wrapper(
    rule_set_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> RuleSetWrapperRead:
    """Get a rule set wrapper by ID."""
    # Get the rule set wrapper via service
    rule_set_wrapper = await rule_service.get_rule_set_wrapper(rule_set_id, session)

    if not rule_set_wrapper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule set wrapper not found",
        )

    return RuleSetWrapperRead(
        id=rule_set_wrapper.id,
        category_id=rule_set_wrapper.category_id,
        rule_set=rule_set_wrapper.get_rule_set_as_dict(),
    )


@router.post("/categorize-transactions", response_model=CategorizeTransactionsResponse)
async def categorize_transactions(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    bank_account: str | None = None,
    transaction_type: TransactionTypeEnum | None = None,
) -> CategorizeTransactionsResponse:
    """Apply rules to categorize transactions.

    Categorizes all transactions for the user that don't have a manually
    assigned category, using the configured rule sets.
    """
    from services.categorization_service import categorization_service

    (
        with_category,
        without_category,
    ) = await categorization_service.categorize_transactions(
        user=current_user,
        bank_account_id=bank_account,
        transaction_type=transaction_type,
        session=session,
    )

    return CategorizeTransactionsResponse(
        message=f"Categorized {with_category} transactions; {without_category} transactions have no category",
        with_category_count=with_category,
        without_category_count=without_category,
    )
