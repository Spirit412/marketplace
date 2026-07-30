"""Dependency injection — rodi container setup and FastAPI integration."""

from src.config.settings import settings
from src.dependencies import container
from src.engines.redis import get_redis_client


class Inject[T]:
    """FastAPI dependency that resolves a service from the rodi container."""

    def __init__(self, service: type[T]) -> None:
        self._service: type[T] = service

    def __call__(self) -> T:
        return container.resolve(self._service)


def init_container() -> None:
    """Register all dependencies in the rodi container."""
    container.add_instance(settings)
    container.add_instance(get_redis_client())
