"""Categories router."""

from typing import List

from db.database import get_session
from enums import TransactionTypeEnum
from fastapi import APIRouter, Depends, HTTPException, Query, status
from routers.auth import CurrentUser
from schemas import CategoryRead, CategoryTreeRead
from services.category_service import category_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/categories", tags=["Categories"])


def _dict_to_category_read(tree_dict: dict) -> CategoryRead:
    """Convert a category tree dictionary to CategoryRead schema."""
    return CategoryRead(
        id=tree_dict["id"],
        name=tree_dict["name"],
        qualified_name=tree_dict["qualified_name"],
        is_root=tree_dict["is_root"],
        type=tree_dict["type"],
        parent_id=tree_dict["parent_id"],
        children=[_dict_to_category_read(child) for child in tree_dict["children"]],
    )


@router.get("/tree", response_model=CategoryTreeRead)
async def get_category_tree(
    transaction_type: TransactionTypeEnum = Query(
        ..., description="Type of transactions (EXPENSES or REVENUE)"
    ),
    current_user: CurrentUser = None,
    session: AsyncSession = Depends(get_session),
) -> CategoryTreeRead:
    """Get the category tree for a transaction type."""
    if transaction_type == TransactionTypeEnum.BOTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="transaction_type must be EXPENSES or REVENUE, not BOTH",
        )

    # Get the category tree via service
    tree = await category_service.get_category_tree(transaction_type, session)

    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category tree for {transaction_type.value} not found",
        )

    # Build the tree response using service
    root_response = None
    if tree.root:
        root_dict = await category_service.build_category_tree(tree.root, session)
        root_response = _dict_to_category_read(root_dict)

    return CategoryTreeRead(
        id=tree.id,
        type=tree.type,
        root=root_response,
    )


@router.get("", response_model=List[CategoryRead])
async def list_categories(
    transaction_type: TransactionTypeEnum | None = Query(
        None, description="Filter by transaction type"
    ),
    current_user: CurrentUser = None,
    session: AsyncSession = Depends(get_session),
) -> List[CategoryRead]:
    """List all categories, optionally filtered by type."""
    if transaction_type:
        categories = await category_service.get_categories_by_type(
            transaction_type, session
        )
    else:
        categories = await category_service.get_all_categories(session)

    return [
        CategoryRead(
            id=cat.id,
            name=cat.name,
            qualified_name=cat.qualified_name,
            is_root=cat.is_root,
            type=cat.type,
            parent_id=cat.parent_id,
            children=[],  # Flat list, no children
        )
        for cat in categories
    ]


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    current_user: CurrentUser = None,
    session: AsyncSession = Depends(get_session),
) -> CategoryRead:
    """Get a specific category by ID."""
    category = await category_service.get_category_by_id(category_id, session)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Get children via service
    children = await category_service.get_category_children(category_id, session)

    return CategoryRead(
        id=category.id,
        name=category.name,
        qualified_name=category.qualified_name,
        is_root=category.is_root,
        type=category.type,
        parent_id=category.parent_id,
        children=[
            CategoryRead(
                id=child.id,
                name=child.name,
                qualified_name=child.qualified_name,
                is_root=child.is_root,
                type=child.type,
                parent_id=child.parent_id,
                children=[],
            )
            for child in children
        ],
    )


@router.get("/by-qualified-name/{qualified_name:path}", response_model=CategoryRead)
async def get_category_by_qualified_name(
    qualified_name: str,
    current_user: CurrentUser = None,
    session: AsyncSession = Depends(get_session),
) -> CategoryRead:
    """Get a category by its qualified name."""
    category = await category_service.get_category_by_qualified_name(
        qualified_name, session
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return CategoryRead(
        id=category.id,
        name=category.name,
        qualified_name=category.qualified_name,
        is_root=category.is_root,
        type=category.type,
        parent_id=category.parent_id,
        children=[],
    )
