from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.health import HealthManager, HealthStatus
from src.engines.postgres import check_postgres
from src.engines.rabbitmq import check_rabbitmq
from src.engines.redis import check_redis

router = APIRouter(tags=["health"])

_health_manager: HealthManager | None = None


def get_health_manager() -> HealthManager:
    global _health_manager
    if _health_manager is None:
        _health_manager = HealthManager(service_name="inventory-service")
    return _health_manager


@router.get("/health", response_model=HealthStatus, summary="Health check")
async def health_check(
    session: AsyncSession = Depends(get_async_session),
) -> HealthStatus:
    """Perform health check for inventory service."""
    manager = get_health_manager()
    manager._checks.clear()
    manager.register("postgres", lambda: check_postgres(session))
    manager.register("redis", check_redis)
    manager.register("rabbitmq", check_rabbitmq)
    return await manager.check()
