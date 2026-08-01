import logging

from src.config.settings import settings
from src.engines.rabbitmq import publish_event
from src.facades import InventoryClient

logger = logging.getLogger(__name__)


async def inventory_alert_job() -> None:
    """Check all warehouse stock levels, publish stock.depleted for low items."""
    client = InventoryClient(settings.INVENTORY_SERVICE_URL, settings.SYSTEM_TOKEN)

    low_stock_items = await client.get_low_stock_items(
        settings.STOCK_DEPLETION_THRESHOLD
    )

    if not low_stock_items:
        logger.info("No low-stock items found")
        return

    logger.info(
        "Found %d items below threshold of %d",
        len(low_stock_items),
        settings.STOCK_DEPLETION_THRESHOLD,
    )

    for item in low_stock_items:
        product_id = item.get("product_id", "")
        warehouse_id = item.get("warehouse_id", "")
        current_stock = item.get("stock", 0)

        await publish_event(
            "stock.depleted",
            {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "current_stock": current_stock,
                "threshold": settings.STOCK_DEPLETION_THRESHOLD,
                "sku": item.get("sku", ""),
                "product_name": item.get("product_name", ""),
            },
        )

    logger.info("Published %d stock.depleted events", len(low_stock_items))
