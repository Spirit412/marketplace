from fastapi import APIRouter

from src.config.settings import settings
from src.core.health import HealthManager, HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus, summary="Health check")
async def health_check() -> HealthStatus:
    """Return the current health status of the service."""
    manager = HealthManager(service_name=settings.APP_NAME)
    return HealthStatus(
        status="healthy",
        service=settings.APP_NAME,
        timestamp="",
        checks={},
    )
