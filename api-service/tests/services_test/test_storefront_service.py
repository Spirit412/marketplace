from unittest.mock import AsyncMock

import pytest

from src.exceptions import NotFoundError
from src.services.storefront_service import StorefrontService

PRODUCT = {
    "id": "019f0000-0000-0000-0000-000000000001",
    "seller_id": "019f0000-0000-0000-0000-000000000002",
    "category_id": None,
    "name": "Widget",
    "description": None,
    "price": 9.99,
    "sku": None,
    "stock": 0,  # catalog's own stale field — deliberately not in the response schema
    "rating": 4.5,
    "custom_properties_config": {},
    "images": {},
    "is_active": True,
    "status": "active",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}


@pytest.mark.asyncio
async def test_composes_product_and_stock() -> None:
    catalog = AsyncMock(get_product=AsyncMock(return_value=PRODUCT))
    inventory = AsyncMock(
        check_stock_by_product=AsyncMock(
            return_value={
                "available": 3,
                "warehouse_id": "019f0000-0000-0000-0000-000000000003",
            }
        )
    )
    service = StorefrontService(catalog, inventory)

    result = await service.get_product_card(PRODUCT["id"], "Bearer caller-token")

    assert str(result.id) == PRODUCT["id"]
    assert result.available == 3
    assert str(result.warehouse_id) == "019f0000-0000-0000-0000-000000000003"


@pytest.mark.asyncio
async def test_missing_product_is_404() -> None:
    catalog = AsyncMock(get_product=AsyncMock(return_value=None))
    inventory = AsyncMock()
    service = StorefrontService(catalog, inventory)

    with pytest.raises(NotFoundError):
        await service.get_product_card("missing", "Bearer caller-token")

    inventory.check_stock_by_product.assert_not_called()


@pytest.mark.asyncio
async def test_inventory_outage_degrades_instead_of_failing() -> None:
    """The whole point of composing at the API layer.

    One dependency being down doesn't have to take the others down with it.
    """
    catalog = AsyncMock(get_product=AsyncMock(return_value=PRODUCT))
    inventory = AsyncMock(
        check_stock_by_product=AsyncMock(
            side_effect=ConnectionError("inventory is down")
        )
    )
    service = StorefrontService(catalog, inventory)

    result = await service.get_product_card(PRODUCT["id"], "Bearer caller-token")

    assert str(result.id) == PRODUCT["id"]
    assert result.available is None
