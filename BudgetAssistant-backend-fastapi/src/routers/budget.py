"""Budget router for budget management."""

from db.database import get_session
from fastapi import APIRouter, Depends, HTTPException, status
from models import BankAccount, BudgetTree, BudgetTreeNode, Category
from models.associations import UserBankAccountLink
from routers.auth import CurrentUser
from schemas import (
    BudgetTreeCreate,
    BudgetTreeNodeRead,
    BudgetTreeNodeUpdate,
    BudgetTreeRead,
    SuccessResponse,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/budget", tags=["Budget"])


async def build_budget_tree_node_response(
    node: BudgetTreeNode, session: AsyncSession
) -> BudgetTreeNodeRead:
    """Recursively build budget tree node response."""
    # Get category info
    category_result = await session.execute(
        select(Category).where(Category.id == node.category_id)
    )
    category = category_result.scalar_one_or_none()

    # Get children
    children_result = await session.execute(
        select(BudgetTreeNode).where(BudgetTreeNode.parent_id == node.id)
    )
    children = children_result.scalars().all()

    child_responses = []
    for child in children:
        child_response = await build_budget_tree_node_response(child, session)
        child_responses.append(child_response)

    return BudgetTreeNodeRead(
        id=node.id,
        amount=node.amount,
        category_id=node.category_id,
        parent_id=node.parent_id,
        name=category.name if category else "",
        qualified_name=category.qualified_name if category else "",
        children=child_responses,
    )


@router.post("/find-or-create", response_model=BudgetTreeRead)
async def find_or_create_budget(
    request: BudgetTreeCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BudgetTreeRead:
    """Find or create a budget tree for a bank account."""
    normalized = BankAccount.normalize_account_number(request.bank_account_id)

    # Check user access
    access_result = await session.execute(
        select(UserBankAccountLink).where(
            UserBankAccountLink.user_id == current_user.id,
            UserBankAccountLink.bank_account_number == normalized,
        )
    )
    if not access_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    # Check if budget tree exists
    result = await session.execute(
        select(BudgetTree).where(BudgetTree.bank_account_id == normalized)
    )
    budget_tree = result.scalar_one_or_none()

    if not budget_tree:
        # Create new budget tree with root node
        # Get root category for expenses
        root_cat_result = await session.execute(
            select(Category).where(Category.name == "root", Category.is_root == True)
        )
        root_category = root_cat_result.scalar_one_or_none()

        if not root_category:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Root category not found. Please initialize categories first.",
            )

        # Create root node
        root_node = BudgetTreeNode(
            category_id=root_category.id,
            amount=0,
        )
        session.add(root_node)
        await session.flush()

        # Create budget tree
        budget_tree = BudgetTree(
            bank_account_id=normalized,
            root_id=root_node.id,
            number_of_descendants=0,
        )
        session.add(budget_tree)
        await session.commit()
        await session.refresh(budget_tree)

    # Build response
    if budget_tree.root_id:
        root_node_result = await session.execute(
            select(BudgetTreeNode).where(BudgetTreeNode.id == budget_tree.root_id)
        )
        root_node = root_node_result.scalar_one_or_none()

        if root_node:
            root_response = await build_budget_tree_node_response(root_node, session)
        else:
            root_response = None
    else:
        root_response = None

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
    normalized = BankAccount.normalize_account_number(bank_account)

    # Check user access
    access_result = await session.execute(
        select(UserBankAccountLink).where(
            UserBankAccountLink.user_id == current_user.id,
            UserBankAccountLink.bank_account_number == normalized,
        )
    )
    if not access_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this bank account",
        )

    # Get budget tree
    result = await session.execute(
        select(BudgetTree).where(BudgetTree.bank_account_id == normalized)
    )
    budget_tree = result.scalar_one_or_none()

    if not budget_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget tree not found for this account",
        )

    # Build response
    if budget_tree.root_id:
        root_node_result = await session.execute(
            select(BudgetTreeNode).where(BudgetTreeNode.id == budget_tree.root_id)
        )
        root_node = root_node_result.scalar_one_or_none()

        if root_node:
            root_response = await build_budget_tree_node_response(root_node, session)
        else:
            root_response = None
    else:
        root_response = None

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
    # Get the node
    result = await session.execute(
        select(BudgetTreeNode).where(BudgetTreeNode.id == node_id)
    )
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget entry not found",
        )

    # Get the budget tree to check access
    tree_result = await session.execute(
        select(BudgetTree).where(BudgetTree.root_id == node_id)
    )
    budget_tree = tree_result.scalar_one_or_none()

    # If not the root, find the tree by traversing up
    if not budget_tree:
        # Find root by traversing parent chain
        current_node = node
        while current_node.parent_id:
            parent_result = await session.execute(
                select(BudgetTreeNode).where(
                    BudgetTreeNode.id == current_node.parent_id
                )
            )
            current_node = parent_result.scalar_one_or_none()
            if not current_node:
                break

        if current_node:
            tree_result = await session.execute(
                select(BudgetTree).where(BudgetTree.root_id == current_node.id)
            )
            budget_tree = tree_result.scalar_one_or_none()

    if not budget_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget tree not found",
        )

    # Check user access
    access_result = await session.execute(
        select(UserBankAccountLink).where(
            UserBankAccountLink.user_id == current_user.id,
            UserBankAccountLink.bank_account_number == budget_tree.bank_account_id,
        )
    )
    if not access_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this budget",
        )

    # Update amount
    if update.amount is not None:
        node.amount = update.amount

    await session.commit()

    return SuccessResponse(message="Budget entry updated successfully")
