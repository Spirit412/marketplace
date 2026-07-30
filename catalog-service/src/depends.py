"""Dependency injection — rodi container setup and FastAPI integration."""

from src.config.settings import settings
from src.dependencies import container
from src.engines.rabbitmq import RabbitMQEngine
from src.engines.redis import get_redis_client
from src.repositories.category_repo import CategoryRepo
from src.repositories.product_repo import ProductRepo
from src.repositories.property_repo import PropertyRepo
from src.repositories.query_set_repo import QuerySetRepo
from src.services.category_service import CategoryService
from src.services.health_service import HealthService
from src.services.product_service import ProductService
from src.services.query_set_service import QuerySetService


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
    container.add_instance(RabbitMQEngine())

    container.add_scoped(ProductRepo)
    container.add_scoped(CategoryRepo)
    container.add_scoped(PropertyRepo)
    container.add_scoped(QuerySetRepo)

    container.add_scoped(ProductService)
    container.add_scoped(CategoryService)
    container.add_scoped(QuerySetService)
    container.add_scoped_by_factory(lambda: HealthService(), HealthService)
