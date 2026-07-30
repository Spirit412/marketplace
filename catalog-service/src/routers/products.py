import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.auth import (
    Permission,
    TokenPayload,
    get_token_payload,
    require_permission,
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


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=201,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
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
        seller_id=uuid.UUID(token_payload.user_uuid),
        name=body.name,
        price=body.price,
        description=body.description,
        sku=body.sku,
        stock=body.stock,
        category_id=uuid.UUID(body.category_id) if body.category_id else None,
        custom_properties_config=body.custom_properties_config,
        images=body.images,
    )
    return ProductResponse.model_validate(product)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
    summary="Get product by ID",
)
async def get_product(
    product_id: uuid.UUID,
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
    response_model=ProductResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
    summary="Update product",
)
async def update_product(
    product_id: uuid.UUID,
    body: UpdateProductRequest,
    service: Annotated[ProductService, Depends(Inject(ProductService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ProductResponse:
    """Update an existing product by ID."""
    product = await service.update(
        session=session,
        product_id=product_id,
        **body.model_dump(exclude_none=True),
    )
    if product is None:
        raise NotFoundError("Product not found")
    return ProductResponse.model_validate(product)


@router.delete(
    "/{product_id}",
    status_code=204,
    response_model=None,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
    summary="Delete product",
)
async def delete_product(
    product_id: uuid.UUID,
    service: Annotated[ProductService, Depends(Inject(ProductService))],
    service_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """Delete a product by ID."""
    deleted = await service.delete(service_session, product_id)
    if not deleted:
        raise NotFoundError("Product not found")


@router.get(
    "/",
    response_model=ProductListResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
    summary="Search products",
)
async def search_products(
    request: Request,
    filters: Annotated[ProductFilterParams, Depends()],
    service: Annotated[ProductService, Depends(Inject(ProductService))],
    service_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ProductListResponse:
    """Search and filter products with dynamic filters."""
    dynamic_filters: dict[str, str] = {}
    reserved = ProductFilterParams.model_fields.keys()
    for key, value in request.query_params.items():
        if key not in reserved:
            dynamic_filters[key] = value

    products, total = await service.search(
        service_session,
        query=filters.search,
        category_id=uuid.UUID(filters.category_id) if filters.category_id else None,
        seller_id=uuid.UUID(filters.seller_id) if filters.seller_id else None,
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
