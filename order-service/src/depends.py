"""Dependency injection — rodi container setup and FastAPI integration."""

from typing import Annotated

from fastapi import Depends

from src.config.settings import Settings, settings
from src.core.auth import TokenPayload, get_token_payload
from src.dependencies import container
from src.engines.redis import get_redis_client
from src.exceptions import RateLimitExceededError
from src.facades import InventoryClient
from src.facades.catalog import CatalogClient
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
    container.add_instance(
        CatalogClient(
            base_url=settings.CATALOG_SERVICE_URL,
            system_token=settings.SYSTEM_TOKEN,
        ),
        CatalogClient,
    )

    container.add_scoped(OrderRepo)
    container.add_scoped(OrderItemRepo)

    container.add_scoped(CartService)
    container.add_scoped(OrderService)

    container.add_scoped(OrderBuilder)
    container.add_scoped(OrderUnitOfWork)


async def enforce_order_rate_limit(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> None:
    """Dependency: throttle POST /orders/ per authenticated user.

    Keyed by user_id, not IP — order creation requires a token, so a spamming
    account is the more precise signal than the caller's address (which is
    also what test_sec_021 exercises: many orders from one account).
    """
    redis_client = get_redis_client()
    key = f"{settings.REDIS_KEY_PREFIX}:rate_limit:orders:{token_payload.user_id}"

    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)

    if count > settings.RATE_LIMIT_MAX_REQUESTS:
        message = f"Too many orders from user {token_payload.user_id}, retry later"
        raise RateLimitExceededError(message)
