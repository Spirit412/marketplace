"""Dependency injection — rodi container setup and FastAPI integration."""

from src.config.settings import Settings, settings
from src.dependencies import container
from src.engines.rabbitmq import DictionaryPublisher, get_publisher
from src.engines.redis import RedisDictCache
from src.repositories.dictionary_repo import DictionaryRepository
from src.services.dictionary_service import DictionaryService


class Inject[T]:
    """FastAPI dependency that resolves a service from the rodi container."""

    def __init__(self, service: type[T]) -> None:
        self._service: type[T] = service

    def __call__(self) -> T:
        return container.resolve(self._service)


def init_container() -> None:
    """Register all dependencies in the rodi container."""
    container.add_instance(settings, Settings)
    container.add_instance(RedisDictCache(), RedisDictCache)
    container.add_instance(get_publisher(), DictionaryPublisher)

    container.add_scoped(DictionaryRepository)

    container.add_scoped(DictionaryService)
