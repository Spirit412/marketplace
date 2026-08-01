"""Dependency injection — rodi container setup and FastAPI integration."""

from src.config.settings import Settings, settings
from src.dependencies import container
from src.facades.catalog import CatalogFacade
from src.facades.inventory import InventoryFacade
from src.facades.order import OrderFacade
from src.facades.payment import PaymentFacade


class Inject[T]:
    """FastAPI dependency that resolves a service from the rodi container."""

    def __init__(self, service: type[T]) -> None:
        self._service: type[T] = service

    def __call__(self) -> T:
        return container.resolve(self._service)


def init_container() -> None:
    """Register all dependencies in the rodi container."""
    container.add_instance(settings, Settings)

    container.add_instance(
        CatalogFacade(base_url=settings.CATALOG_SERVICE_URL), CatalogFacade
    )
    container.add_instance(
        InventoryFacade(base_url=settings.INVENTORY_SERVICE_URL), InventoryFacade
    )
    container.add_instance(
        OrderFacade(base_url=settings.ORDER_SERVICE_URL), OrderFacade
    )
    container.add_instance(
        PaymentFacade(base_url=settings.PAYMENT_SERVICE_URL), PaymentFacade
    )
