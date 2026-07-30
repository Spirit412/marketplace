from typing import Any

from fastapi import APIRouter

from src.core.health import HealthManager
from src.engines.postgres import _get_session_factory, check_postgres
from src.engines.redis import check_redis

router = APIRouter(tags=["health"])


async def _check_postgres() -> None:
    """Run the database probe on a short-lived session."""
    factory = _get_session_factory()
    async with factory() as session:
        await check_postgres(session)


@router.get("/health", summary="Health check")
async def health_check() -> dict[str, Any]:
    """Perform health check for dictionary service."""
    manager = HealthManager(service_name="dictionary-service")
    manager.register("postgres", _check_postgres)
    manager.register("redis", check_redis)
    result = await manager.check()
    return result.model_dump()
