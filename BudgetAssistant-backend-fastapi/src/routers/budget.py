"""Budget router for budget management."""

from db.database import get_session
from fastapi import APIRouter, Depends, HTTPException, status
from models import BankAccount
from routers.auth import CurrentUser
from schemas import (
    BudgetTreeCreate,
    BudgetTreeNodeRead,
    BudgetTreeNodeUpdate,
    BudgetTreeRead,
    SuccessResponse,
)
from services.bank_account_service import bank_account_service
from services.budget_service import budget_service
from services.providers import BudgetTreeProvider
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/budget", tags=["Budget"])


def _dict_to_budget_tree_node_read(tree_dict: dict) -> BudgetTreeNodeRead:
    """Convert a budget tree node dictionary to BudgetTreeNodeRead schema."""
    return BudgetTreeNodeRead(
        id=tree_dict["id"],
        amount=tree_dict["amount"],
        category_id=tree_dict["category_id"],
        parent_id=tree_dict["parent_id"],
        name=tree_dict["name"],
        qualified_name=tree_dict["qualified_name"],
        children=[
            _dict_to_budget_tree_node_read(child) for child in tree_dict["children"]
        ],
    )


@router.post("/find-or-create", response_model=BudgetTreeRead)
async def find_or_create_budget(
    request: BudgetTreeCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BudgetTreeRead:
    """Find or create a budget tree for a bank account."""
    # Check user access
    if not await bank_account_service.user_has_access(
        current_user, request.bank_account_id, session
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    # Get bank account
    normalized = BankAccount.normalize_account_number(request.bank_account_id)
    bank_account = await session.get(BankAccount, normalized)
    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found",
        )

    # Use provider to get or create budget tree
    provider = BudgetTreeProvider()
    budget_tree = await provider.provide(bank_account, session)
    await session.commit()

    # Build response using service
    root_response = None
    if budget_tree.root_id:
        root_node = await budget_service.get_budget_tree_node(
            budget_tree.root_id, session
        )
        if root_node:
            root_dict = await budget_service.build_budget_tree_dict(root_node, session)
            root_response = _dict_to_budget_tree_node_read(root_dict)

    return BudgetTreeRead(
        bank_account_id=budget_tree.bank_account_id,
        number_of_descendants=budget_tree.number_of_descendants,
        root_id=budget_tree.root_id,
        root=root_response,
    )


@router.get("/{bank_account}", response_model=BudgetTreeRead)
async def get_budget(
    bank_account: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BudgetTreeRead:
    """Get the budget tree for a bank account."""
    # Check user access
    if not await bank_account_service.user_has_access(
        current_user, bank_account, session
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    # Get budget tree via service
    budget_tree = await budget_service.get_budget_tree(bank_account, session)

    if not budget_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget tree not found for this account",
        )

    # Build response using service
    root_response = None
    if budget_tree.root_id:
        root_node = await budget_service.get_budget_tree_node(
            budget_tree.root_id, session
        )
        if root_node:
            root_dict = await budget_service.build_budget_tree_dict(root_node, session)
            root_response = _dict_to_budget_tree_node_read(root_dict)

    return BudgetTreeRead(
        bank_account_id=budget_tree.bank_account_id,
        number_of_descendants=budget_tree.number_of_descendants,
        root_id=budget_tree.root_id,
        root=root_response,
    )


@router.patch("/entry/{node_id}", response_model=SuccessResponse)
async def update_budget_entry_amount(
    node_id: int,
    update: BudgetTreeNodeUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Update a budget tree node's amount."""
    # Get the node via service
    node = await budget_service.get_budget_tree_node(node_id, session)

    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget entry not found",
        )

    # Find the budget tree for this node
    budget_tree = await budget_service.find_budget_tree_for_node(node_id, session)

    if not budget_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget tree not found",
        )

    # Check user access via service
    if not await budget_service.user_has_budget_access(
        current_user, budget_tree.bank_account_id, session
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this budget",
        )

    # Update amount via service
    if update.amount is not None:
        await budget_service.update_budget_entry_amount(
            node_id=node_id,
            amount=update.amount,
            session=session,
        )

    return SuccessResponse(message="Budget entry updated successfully")
