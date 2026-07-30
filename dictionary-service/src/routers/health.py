from fastapi import APIRouter

from src.core.health import HealthManager

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
async def health_check() -> dict:
    """Perform health check for dictionary service."""
    manager = HealthManager(service_name="dictionary-service")
    result = await manager.check()
    return result.model_dump()
