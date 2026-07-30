import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.auth import (
    Permission,
    require_permission,
)
from src.core.database import get_async_session
from src.depends import Inject
from src.schemes.request.category import CreateCategoryRequest, UpdateCategoryRequest
from src.schemes.response.category import CategoryResponse, CategoryTreeResponse
from src.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=201,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
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
        parent_id=uuid.UUID(body.parent_id) if body.parent_id else None,
        properties=[prop.model_dump() for prop in body.properties]
        if body.properties
        else None,
    )
    return CategoryResponse.model_validate(category)


@router.get(
    "/",
    response_model=CategoryTreeResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
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
    response_model=CategoryResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
    summary="Get category by ID",
)
async def get_category(
    category_id: uuid.UUID,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> CategoryResponse:
    """Get a single category by ID."""
    category = await service.get_by_id(session, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse.model_validate(category)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
    summary="Update category",
)
async def update_category(
    category_id: uuid.UUID,
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
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=204,
    response_model=None,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
    summary="Delete category",
)
async def delete_category(
    category_id: uuid.UUID,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """Delete a category by ID."""
    deleted = await service.delete(session, category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")


@router.get(
    "/{category_id}/ancestors",
    response_model=list[CategoryResponse],
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
    summary="Get category ancestors",
)
async def get_ancestors(
    category_id: uuid.UUID,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[CategoryResponse]:
    """Get all ancestors of a category."""
    ancestors = await service.get_ancestors(session, category_id)
    return [CategoryResponse.model_validate(ancestor) for ancestor in ancestors]


@router.get(
    "/{category_id}/descendants",
    response_model=list[CategoryResponse],
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
    summary="Get category descendants",
)
async def get_descendants(
    category_id: uuid.UUID,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[CategoryResponse]:
    """Get all descendants of a category."""
    descendants = await service.get_descendants(session, category_id)
    return [CategoryResponse.model_validate(desc) for desc in descendants]


@router.post(
    "/{category_id}/move",
    response_model=CategoryResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
    summary="Move category",
)
async def move_category(
    category_id: uuid.UUID,
    service: Annotated[CategoryService, Depends(Inject(CategoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    new_parent_id: str | None = Query(None),
) -> CategoryResponse:
    """Move a category to a new parent."""
    parent = uuid.UUID(new_parent_id) if new_parent_id else None
    category = await service.move_node(session, category_id, parent)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse.model_validate(category)
