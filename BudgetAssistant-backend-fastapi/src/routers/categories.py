"""Categories router."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.database import get_session
from enums import TransactionTypeEnum
from models import Category, CategoryTree
from routers.auth import CurrentUser
from schemas import CategoryRead, CategoryTreeRead

router = APIRouter(prefix="/categories", tags=["Categories"])


async def build_category_tree_response(
    root_category: Category, session: AsyncSession
) -> CategoryRead:
    """Recursively build category tree response."""

    async def build_children(category: Category) -> List[CategoryRead]:
        """Build children recursively."""
        result = await session.execute(
            select(Category)
            .where(Category.parent_id == category.id)
            .order_by(Category.name)
        )
        children = result.scalars().all()

        child_reads = []
        for child in children:
            grandchildren = await build_children(child)
            child_read = CategoryRead(
                id=child.id,
                name=child.name,
                qualified_name=child.qualified_name,
                is_root=child.is_root,
                type=child.type,
                parent_id=child.parent_id,
                children=grandchildren,
            )
            child_reads.append(child_read)
        return child_reads

    children = await build_children(root_category)
    return CategoryRead(
        id=root_category.id,
        name=root_category.name,
        qualified_name=root_category.qualified_name,
        is_root=root_category.is_root,
        type=root_category.type,
        parent_id=root_category.parent_id,
        children=children,
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

    # Get the category tree
    result = await session.execute(
        select(CategoryTree)
        .options(selectinload(CategoryTree.root))
        .where(CategoryTree.type == transaction_type.value)
    )
    category_tree = result.scalar_one_or_none()

    if not category_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category tree for {transaction_type.value} not found",
        )

    # Build the tree response
    if category_tree.root:
        root_response = await build_category_tree_response(
            category_tree.root, session
        )
    else:
        root_response = None

    return CategoryTreeRead(
        id=category_tree.id,
        type=category_tree.type,
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
    query = select(Category).order_by(Category.qualified_name)

    if transaction_type:
        query = query.where(Category.type == transaction_type.value)

    result = await session.execute(query)
    categories = result.scalars().all()

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
    result = await session.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Get children
    children_result = await session.execute(
        select(Category)
        .where(Category.parent_id == category_id)
        .order_by(Category.name)
    )
    children = children_result.scalars().all()

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
    result = await session.execute(
        select(Category).where(Category.qualified_name == qualified_name)
    )
    category = result.scalar_one_or_none()

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

