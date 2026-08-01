from fastapi import APIRouter

from src.config.settings import settings
from src.core.health import HealthManager, HealthStatus
from src.core.http_client import CircuitBreakerClient

router = APIRouter(tags=["health"])


async def _check(base_url: str) -> None:
    client = CircuitBreakerClient(base_url=base_url)
    await client.get("/health")


@router.get("/health", summary="Health check")
async def health_check() -> HealthStatus:
    """Aggregated status of api-service and every service it composes from.

    Only the four services a composed endpoint actually depends on
    (catalog, order, payment, inventory) — not all ten — so this doesn't
    manufacture a false dependency on services api-service never calls.
    """
    manager = HealthManager(service_name="api-service")

    manager.register("catalog", lambda: _check(settings.CATALOG_SERVICE_URL))
    manager.register("order", lambda: _check(settings.ORDER_SERVICE_URL))
    manager.register("payment", lambda: _check(settings.PAYMENT_SERVICE_URL))
    manager.register("inventory", lambda: _check(settings.INVENTORY_SERVICE_URL))

    return await manager.check()
