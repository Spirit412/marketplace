from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.health import HealthManager, HealthStatus
from src.engines.postgres import check_postgres
from src.engines.redis import check_redis

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus, summary="Health check")
async def health_check(
    session: AsyncSession = Depends(get_async_session),
) -> HealthStatus:
    """Perform health check for payment service."""
    manager = HealthManager(service_name="payment-service")
    manager.register("postgres", lambda: check_postgres(session))
    manager.register("redis", check_redis)
    return await manager.check()
