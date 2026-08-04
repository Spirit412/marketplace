"""Business logic for the storefront composed endpoint.

Owns the composition + degradation decision that used to live in the
router: routers stay a thin HTTP/DI boundary, this is where "what do we
actually do" lives, same split as every other service in the project.
"""

from src.exceptions import NotFoundError
from src.facades.catalog import CatalogFacade
from src.facades.inventory import InventoryFacade
from src.schemes.response.storefront import StorefrontProductResponse


class StorefrontService:
    def __init__(self, catalog: CatalogFacade, inventory: InventoryFacade) -> None:
        self._catalog = catalog
        self._inventory = inventory

    async def get_product_card(
        self, product_id: str, authorization: str
    ) -> StorefrontProductResponse:
        """Product detail + live availability — the classic storefront N+1.

        Catalog is the authoritative 404: if the product doesn't exist
        there's nothing to compose. Inventory being unreachable degrades to
        `available: null` on the card rather than failing the whole
        request — the product itself is still real and worth showing.
        """
        product = await self._catalog.get_product(product_id, authorization)
        if product is None:
            raise NotFoundError(f"Product {product_id} not found")

        try:
            stock = await self._inventory.check_stock_by_product(
                product_id, authorization
            )
        except Exception:  # degrade, don't fail the whole request
            stock = None

        return StorefrontProductResponse(
            **product,
            available=stock["available"] if stock else None,
            warehouse_id=stock["warehouse_id"] if stock else None,
        )
