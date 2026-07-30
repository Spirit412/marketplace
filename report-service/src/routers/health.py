from fastapi import APIRouter

from src.core.health import HealthManager, HealthStatus
from src.engines.postgres import check_postgres
from src.engines.rabbitmq import check_rabbitmq
from src.engines.redis import check_redis

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus, summary="Health check")
async def health_check() -> HealthStatus:
    """Perform health check for report service."""
    manager = HealthManager(service_name="report-service")
    manager.register("postgres", check_postgres)
    manager.register("redis", check_redis)
    manager.register("rabbitmq", check_rabbitmq)
    return await manager.check()
