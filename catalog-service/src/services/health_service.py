"""Health check service — infrastructure probes delegated from router."""

from src.config.settings import settings
from src.core.health import HealthManager, HealthStatus
from src.core.http_client import CircuitBreakerClient
from src.engines.postgres import check_postgres
from src.engines.rabbitmq import RabbitMQEngine
from src.engines.redis import check_redis


class HealthService:
    """Encapsulates infrastructure health checks for catalog-service."""

    def __init__(self, service_name: str = "catalog-service") -> None:
        self._manager = HealthManager(service_name=service_name)

    async def check_rabbitmq(self) -> None:

        engine = RabbitMQEngine()
        try:
            await engine.connect()
        finally:
            await engine.close()

    async def check_dictionary_service(self) -> None:

        client = CircuitBreakerClient(base_url=settings.DICTIONARY_SERVICE_URL)
        await client.get("/health")

    async def check_all(self, session) -> HealthStatus:
        self._manager.register("postgres", lambda: check_postgres(session))
        self._manager.register("redis", check_redis)
        self._manager.register("rabbitmq", self.check_rabbitmq)
        self._manager.register("dictionary-service", self.check_dictionary_service)
        return await self._manager.check()
