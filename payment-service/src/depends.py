"""Dependency injection — rodi container setup and FastAPI integration."""

from src.config.settings import Settings, settings
from src.dependencies import container
from src.engines.redis import get_redis_client
from src.repositories.payment_repo import PaymentRepo
from src.services.gateway_registry import PaymentGatewayRegistry
from src.services.payload_builder import PaymentPayloadBuilder
from src.services.payment_service import PaymentService


class Inject[T]:
    """FastAPI dependency that resolves a service from the rodi container."""

    def __init__(self, service: type[T]) -> None:
        self._service: type[T] = service

    def __call__(self) -> T:
        return container.resolve(self._service)


def init_container() -> None:
    """Register all dependencies in the rodi container."""
    container.add_instance(settings, Settings)
    container.add_instance(get_redis_client())

    container.add_transient(PaymentPayloadBuilder)

    container.add_scoped_by_factory(
        lambda: PaymentGatewayRegistry(settings), PaymentGatewayRegistry
    )

    container.add_transient(PaymentRepo)

    container.add_scoped(PaymentService)
