from fastapi import APIRouter

from src.core.database import _get_session_factory
from src.core.health import HealthManager, HealthStatus
from src.engines.postgres import check_postgres
from src.engines.rabbitmq import check_rabbitmq
from src.engines.redis import check_redis

router = APIRouter(tags=["health"])


async def _check_postgres() -> None:
    """Run the database probe on a short-lived session."""
    factory = _get_session_factory()
    async with factory() as session:
        await check_postgres(session)


@router.get("/health", response_model=HealthStatus, summary="Health check")
async def health_check() -> HealthStatus:
    """Perform health check for scheduler service."""
    manager = HealthManager(service_name="scheduler-service")
    manager.register("postgres", _check_postgres)
    manager.register("redis", check_redis)
    manager.register("rabbitmq", check_rabbitmq)
    return await manager.check()
