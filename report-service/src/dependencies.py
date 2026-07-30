"""Dependency injection — rodi container setup and FastAPI integration."""


from rodi import Container

from src.config.settings import Settings, settings
from src.engines.file_storage import LocalFileStorage
from src.services.report_service import ReportService

container = Container()


class Inject[T]:
    """FastAPI dependency that resolves a service from the rodi container."""

    def __init__(self, service: type[T]) -> None:
        self._service: type[T] = service

    def __call__(self) -> T:
        return container.resolve(self._service)


def init_container() -> None:
    """Register all dependencies in the rodi container."""
    
    container.add_instance(settings, Settings)
    container.add_instance(LocalFileStorage())

    container.add_scoped(ReportService)
