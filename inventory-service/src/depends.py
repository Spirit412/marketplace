"""Dependency injection — rodi container setup and FastAPI integration."""

from src.config.settings import Settings, settings
from src.dependencies import container
from src.services.inventory_service import InventoryService
from src.services.movement_service import MovementService
from src.services.warehouse_service import WarehouseService


class Inject[T]:
    """FastAPI dependency that resolves a service from the rodi container."""

    def __init__(self, service: type[T]) -> None:
        self._service: type[T] = service

    def __call__(self) -> T:
        return container.resolve(self._service)


def init_container() -> None:
    """Register all dependencies in the rodi container."""
    container.add_instance(settings, Settings)

    container.add_transient(InventoryService)
    container.add_transient(MovementService)
    container.add_transient(WarehouseService)
