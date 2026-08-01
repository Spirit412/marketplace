"""Dependency injection — rodi container setup and FastAPI integration.

Request-scoped dependencies (repositories with DB session) use FastAPI Depends().
Singleton infrastructure (settings, engines) uses rodi container.
"""

from rodi import Container

from src.config.settings import Settings, settings
from src.engines.rabbitmq import ImportPublisher
from src.facades import CatalogClient, DictionaryClient
from src.patterns.file_storage_registry import FileStorageRegistry
from src.patterns.import_registry import ImportStrategyRegistry
from src.repositories.import_repo import ImportRowRepository, ImportTaskRepository
from src.services.import_service import ImportService

container = Container()


class Inject[T]:
    """FastAPI dependency that resolves a service from the rodi container."""

    def __init__(self, service: type[T]) -> None:
        self._service: type[T] = service

    def __call__(self) -> T:
        return container.resolve(self._service)


def init_container() -> None:
    """Register singleton dependencies in the rodi container."""
    container.add_instance(settings, Settings)

    container.add_scoped(CatalogClient)
    container.add_scoped(DictionaryClient)
    container.add_scoped(ImportPublisher)

    container.add_scoped(FileStorageRegistry)
    container.add_scoped(ImportStrategyRegistry)

    container.add_scoped(ImportTaskRepository)
    container.add_scoped(ImportRowRepository)

    container.add_scoped(ImportService)
