from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from src.depends import Inject
from src.schemes.response.storefront import StorefrontProductResponse
from src.services.storefront_service import StorefrontService

router = APIRouter(prefix="/storefront", tags=["storefront"])


@router.get(
    "/products/{product_id}",
    summary="Product card: catalog + live stock in one call",
)
async def get_storefront_product(
    product_id: Annotated[
        str,
        Path(
            description="catalog-service product UUID.",
            examples=["019f0000-0000-0000-0000-000000000001"],
        ),
    ],
    request: Request,
    service: Annotated[StorefrontService, Depends(Inject(StorefrontService))],
) -> StorefrontProductResponse:
    authorization = request.headers.get("Authorization", "")
    return await service.get_product_card(product_id, authorization)
