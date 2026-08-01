from typing import Annotated

from fastapi import APIRouter, Depends, Request

from src.depends import Inject
from src.exceptions import NotFoundError
from src.facades.catalog import CatalogFacade
from src.facades.inventory import InventoryFacade
from src.schemes.response.storefront import StorefrontProductResponse

router = APIRouter(prefix="/storefront", tags=["storefront"])


@router.get(
    "/products/{product_id}",
    summary="Product card: catalog + live stock in one call",
)
async def get_storefront_product(
    product_id: str,
    request: Request,
    catalog: Annotated[CatalogFacade, Depends(Inject(CatalogFacade))],
    inventory: Annotated[InventoryFacade, Depends(Inject(InventoryFacade))],
) -> StorefrontProductResponse:
    """Product detail + live availability — the classic storefront N+1.

    Catalog is the authoritative 404: if the product doesn't exist there's
    nothing to compose. Inventory being unreachable degrades to
    `available: null` on the card rather than failing the whole request —
    the product itself is still real and worth showing.
    """
    authorization = request.headers.get("Authorization", "")

    product = await catalog.get_product(product_id, authorization)
    if product is None:
        raise NotFoundError(f"Product {product_id} not found")

    try:
        stock = await inventory.check_stock_by_product(product_id, authorization)
    except Exception:  # see docstring: degrade, don't fail the whole request
        stock = None

    return StorefrontProductResponse(
        **product,
        available=stock["available"] if stock else None,
        warehouse_id=stock["warehouse_id"] if stock else None,
    )
