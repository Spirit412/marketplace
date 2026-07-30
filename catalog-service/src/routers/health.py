from fastapi import APIRouter

from src.core.health import HealthStatus
from src.services.health_service import HealthService
from src.core.database import _get_session_factory

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus, summary="Health check")
async def health_check() -> HealthStatus:
    """Perform health check for catalog service."""
    health_service = HealthService()
    session_factory = _get_session_factory()

    async with session_factory() as session:
        return await health_service.check_all(session)
