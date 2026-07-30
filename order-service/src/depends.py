"""Dependency injection — rodi container setup and FastAPI integration."""

from src.config.settings import Settings, settings
from src.dependencies import container
from src.engines.http_client import InventoryClient
from src.engines.redis import get_redis_client
from src.patterns.builder import OrderBuilder
from src.patterns.uow import OrderUnitOfWork
from src.repositories.order_repo import OrderItemRepo, OrderRepo
from src.services.cart_service import CartService
from src.services.order_service import OrderService


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
    container.add_instance(
        InventoryClient(
            base_url=settings.INVENTORY_SERVICE_URL,
            system_token=settings.SYSTEM_TOKEN,
        ),
        InventoryClient,
    )

    container.add_scoped(OrderRepo)
    container.add_scoped(OrderItemRepo)

    container.add_scoped(CartService)
    container.add_scoped(OrderService)

    container.add_scoped(OrderBuilder)
    container.add_scoped(OrderUnitOfWork)
