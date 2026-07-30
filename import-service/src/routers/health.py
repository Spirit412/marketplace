from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.health import HealthManager, HealthStatus
from src.engines.http_client import CatalogClient, DictionaryClient
from src.engines.postgres import check_postgres
from src.engines.rabbitmq import ImportPublisher

router = APIRouter(tags=["health"])


async def _check_rabbitmq() -> None:
    """Check RabbitMQ connectivity."""
    publisher = ImportPublisher()
    await publisher.connect()
    try:
        pass
    finally:
        await publisher.disconnect()


async def _check_catalog() -> None:
    """Check catalog-service connectivity."""
    client = CatalogClient()
    await client.get_categories()


async def _check_dictionary() -> None:
    """Check dictionary-service connectivity."""
    client = DictionaryClient()
    await client.get_units()


@router.get("/health", response_model=HealthStatus, summary="Health check")
async def health_check(
    session: AsyncSession = Depends(get_async_session),
) -> HealthStatus:
    """Perform health check for import service."""
    manager = HealthManager(service_name="import-service")
    manager.register("postgres", lambda: check_postgres(session))
    manager.register("rabbitmq", _check_rabbitmq)
    manager.register("catalog", _check_catalog)
    manager.register("dictionary", _check_dictionary)
    return await manager.check()
