from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth_middleware import _get_auth_state
from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.core.database import get_async_session
from src.depends import Inject
from src.exceptions import NotFoundError
from src.schemes.request.product import (
    CreateProductRequest,
    ProductFilterParams,
    UpdateProductRequest,
)
from src.schemes.response.product import ProductListResponse, ProductResponse
from src.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

ProductIdPath = Annotated[
    UUID,
    Path(
        description="Product id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000050"],
    ),
]


@router.post(
    "/",
    status_code=201,
    summary="Create product",
)
async def create_product(
    body: CreateProductRequest,
    service: Annotated[ProductService, Depends(Inject(ProductService))],
    service_session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> ProductResponse:
    """Create a new product with details and images."""
    product = await service.create(
        service_session,
        seller_id=UUID(token_payload.user_id),
        name=body.name,
        price=body.price,
        description=body.description,
        sku=body.sku,
        stock=body.stock,
        category_id=body.category_id,
        custom_properties_config=body.custom_properties_config,
        images=body.images,
    )
    return ProductResponse.model_validate(product)


@router.get(
    "/{product_id}",
    summary="Get product by ID",
)
async def get_product(
    product_id: ProductIdPath,
    service: Annotated[ProductService, Depends(Inject(ProductService))],
    service_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ProductResponse:
    """Get a single product by ID."""
    product = await service.get_by_id(service_session, product_id)
    if product is None:
        raise NotFoundError("Product not found")
    return ProductResponse.model_validate(product)


@router.put(
    "/{product_id}",
    summary="Update product",
)
async def update_product(
    request: Request,
    product_id: ProductIdPath,
    body: UpdateProductRequest,
    service: Annotated[ProductService, Depends(Inject(ProductService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> ProductResponse:
    """Update an existing product by ID.

    Owning seller, a moderator, or an admin only. CATALOG:PUT alone (RBAC)
    does not imply "any product" — without this, any seller could edit any
    other seller's listing.
    """
    auth_state = _get_auth_state(request)
    product = await service.update(
        session=session,
        product_id=product_id,
        caller_id=UUID(token_payload.user_id),
        caller_is_admin=auth_state.is_admin,
        caller_role=auth_state.role,
        **body.model_dump(exclude_none=True),
    )
    if product is None:
        raise NotFoundError("Product not found")
    return ProductResponse.model_validate(product)


@router.delete(
    "/{product_id}",
    status_code=204,
    response_model=None,
    summary="Delete product",
)
async def delete_product(
    request: Request,
    product_id: ProductIdPath,
    service: Annotated[ProductService, Depends(Inject(ProductService))],
    service_session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> None:
    """Delete a product by ID — the owning seller or an admin only."""
    auth_state = _get_auth_state(request)
    deleted = await service.delete(
        service_session,
        product_id,
        caller_id=UUID(token_payload.user_id),
        caller_is_admin=auth_state.is_admin,
    )
    if not deleted:
        raise NotFoundError("Product not found")


@router.get(
    "/",
    summary="Search products",
)
async def search_products(
    request: Request,
    filters: Annotated[ProductFilterParams, Depends()],
    service: Annotated[ProductService, Depends(Inject(ProductService))],
    service_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ProductListResponse:
    """Search and filter products with dynamic filters."""
    reserved = ProductFilterParams.model_fields.keys()
    dynamic_filters: dict[str, str] = {
        key: value for key, value in request.query_params.items() if key not in reserved
    }

    products, total = await service.search(
        service_session,
        query=filters.search,
        category_id=filters.category_id,
        seller_id=filters.seller_id,
        price_min=filters.price_min,
        price_max=filters.price_max,
        sort=filters.sort,
        page=filters.page,
        page_size=filters.page_size,
        status=filters.status,
        filters=dynamic_filters or None,
    )

    return ProductListResponse(
        items=[ProductResponse.model_validate(prod) for prod in products],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
    )
