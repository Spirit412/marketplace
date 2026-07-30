from fastapi import APIRouter

from src.config.settings import settings
from src.core.database import get_async_session
from src.core.health import HealthManager, HealthStatus
from src.engines.http_client import InventoryClient
from src.engines.postgres import check_postgres
from src.engines.redis import check_redis
from src.core.http_client import CircuitBreakerClient

router = APIRouter(tags=["health"])


async def _check_catalog() -> None:
    """Check catalog-service health."""
    client = CircuitBreakerClient(base_url=settings.CATALOG_SERVICE_URL)
    await client.get("/health")


async def _check_inventory() -> None:
    """Check inventory-service health."""
    client = InventoryClient(
        base_url=settings.INVENTORY_SERVICE_URL,
        system_token=settings.SYSTEM_TOKEN,
    )
    await client.check_stock("00000000-0000-0000-0000-000000000000", 1)


@router.get("/health", response_model=HealthStatus, summary="Health check")
async def health_check() -> HealthStatus:
    """Perform health check for order service."""
    from sqlalchemy.ext.asyncio import AsyncSession

    manager = HealthManager(service_name="order-service")
    session_factory = get_async_session()

    manager.register("postgres", lambda: check_postgres(session_factory))
    manager.register("redis", check_redis)
    manager.register("catalog", _check_catalog)
    manager.register("inventory", _check_inventory)

    return await manager.check()
