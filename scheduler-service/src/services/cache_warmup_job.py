import logging

from src.config.settings import settings
from src.engines.redis import RedisCache, get_redis_client
from src.facades import CatalogClient, InventoryClient

logger = logging.getLogger(__name__)


async def cache_warmup_job() -> None:
    """Preload popular products and categories into Redis cache."""
    redis = RedisCache(get_redis_client())

    inventory_client = InventoryClient(
        settings.INVENTORY_SERVICE_URL, settings.SYSTEM_TOKEN
    )
    catalog_client = CatalogClient(settings.CATALOG_SERVICE_URL, settings.SYSTEM_TOKEN)

    try:
        categories = await catalog_client.get_categories()
        if categories:
            await redis.setex_json("cache:warm:categories", 3600, categories)
            logger.info("Cache warmed: %d categories", len(categories))
    except Exception as exc:
        logger.warning("Cache warmup categories failed: %s", exc)

    try:
        products = await inventory_client.get_popular_products(limit=50)
        if products:
            await redis.setex_json("cache:warm:popular_products", 1800, products)
            logger.info("Cache warmed: %d popular products", len(products))
    except Exception as exc:
        logger.warning("Cache warmup popular products failed: %s", exc)

    logger.info("Cache warmup completed")
