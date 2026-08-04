from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.depends import Inject
from src.exceptions import NotFoundError
from src.schemes.request.category import CreateCategoryRequest, UpdateCategoryRequest
from src.schemes.response.category import CategoryResponse, CategoryTreeResponse
from src.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])

CategoryIdPath = Annotated[
    UUID,
    Path(
        description="Category id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000020"],
    ),
]


@router.post(
    "/",
    status_code=201,
    summary="Create category",
)
async def create_category(
    body: CreateCategoryRequest,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> CategoryResponse:
    """Create a new category with optional properties."""
    category = await service.create_with_properties(
        session,
        name=body.name,
        slug=body.slug,
        description=body.description,
        parent_id=body.parent_id,
        properties=[prop.model_dump() for prop in body.properties]
        if body.properties
        else None,
    )
    return CategoryResponse.model_validate(category)


@router.get(
    "/",
    summary="Get category tree",
)
async def get_tree(
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> CategoryTreeResponse:
    """Get the full category tree."""
    tree = await service.get_tree(session)
    return CategoryTreeResponse(
        items=[CategoryResponse.model_validate(item) for item in tree],
    )


@router.get(
    "/{category_id}",
    summary="Get category by ID",
)
async def get_category(
    category_id: CategoryIdPath,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> CategoryResponse:
    """Get a single category by ID."""
    category = await service.get_by_id(session, category_id)
    if category is None:
        raise NotFoundError("Category not found")
    return CategoryResponse.model_validate(category)


@router.put(
    "/{category_id}",
    summary="Update category",
)
async def update_category(
    category_id: CategoryIdPath,
    body: UpdateCategoryRequest,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> CategoryResponse:
    """Update an existing category by ID."""
    category = await service.update(
        session,
        category_id=category_id,
        **body.model_dump(exclude_none=True),
    )
    if category is None:
        raise NotFoundError("Category not found")
    return CategoryResponse.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=204,
    response_model=None,
    summary="Delete category",
)
async def delete_category(
    category_id: CategoryIdPath,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """Delete a category by ID."""
    deleted = await service.delete(session, category_id)
    if not deleted:
        raise NotFoundError("Category not found")


@router.get(
    "/{category_id}/ancestors",
    summary="Get category ancestors",
)
async def get_ancestors(
    category_id: CategoryIdPath,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[CategoryResponse]:
    """Get all ancestors of a category."""
    ancestors = await service.get_ancestors(session, category_id)
    return [CategoryResponse.model_validate(ancestor) for ancestor in ancestors]


@router.get(
    "/{category_id}/descendants",
    summary="Get category descendants",
)
async def get_descendants(
    category_id: CategoryIdPath,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[CategoryResponse]:
    """Get all descendants of a category."""
    descendants = await service.get_descendants(session, category_id)
    return [CategoryResponse.model_validate(desc) for desc in descendants]


@router.post(
    "/{category_id}/move",
    summary="Move category",
)
async def move_category(
    category_id: CategoryIdPath,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    new_parent_id: Annotated[
        UUID | None,
        Query(
            description="New parent category id, or omit/null for root.",
            examples=["019f0000-0000-7000-8000-000000000021"],
        ),
    ] = None,
) -> CategoryResponse:
    """Move a category to a new parent."""
    category = await service.move_node(session, category_id, new_parent_id)
    if category is None:
        raise NotFoundError("Category not found")
    return CategoryResponse.model_validate(category)
