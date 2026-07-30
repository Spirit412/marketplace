import logging
import uuid
from typing import Any

import redis.asyncio as redis_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.datatype import uuid7
from src.core.event import EventManager
from src.engines.http_client import InsufficientStockError, InventoryClient
from src.enums.order_status import ORDER_STATE_MACHINE, OrderStatus
from src.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from src.models.order import Order
from src.patterns.builder import OrderBuilder
from src.patterns.state_machine import InvalidTransitionError
from src.repositories.order_repo import OrderRepo
from src.services.cart_service import CartService
from src.services.order_validators import (
    CartNotEmptyValidator,
    CreateOrderContext,
    StockAvailableValidator,
)

logger = logging.getLogger(__name__)


class OrderService:
    """Core order business logic."""

    def __init__(
        self,
        order_repo: OrderRepo,
        cart_service: CartService,
        inventory_client: InventoryClient,
        redis_client: redis_asyncio.Redis,
    ) -> None:
        self._order_repo = order_repo
        self._cart_service = cart_service
        self._inventory_client = inventory_client
        self._redis = redis_client

    async def create_order(
        self,
        *,
        session: AsyncSession,
        user_uuid: uuid.UUID,
        shipping_address: dict[str, Any],
        payment_method: str,
        tax_strategy: str,
        idempotency_key: str | None = None,
        notes: str | None = None,
    ) -> Order:
        """Create an order from the user's cart."""
        user_uuid_str = str(user_uuid)

        if idempotency_key:
            idem_key = f"idempotency:{idempotency_key}"
            acquired = await self._redis.setnx(idem_key, 1)
            if not acquired:
                existing = await self._order_repo.get_by_idempotency_key(
                    session, idempotency_key
                )
                if existing:
                    return existing
            await self._redis.expire(idem_key, 86400)

        cart_items = await self._cart_service.get_cart(user_uuid_str)

        validation_context = CreateOrderContext(
            cart_items=cart_items, inventory_client=self._inventory_client
        )
        validation_errors = await EventManager.validate_all(
            [CartNotEmptyValidator(), StockAvailableValidator()],
            validation_context,
        )
        if validation_errors:
            raise ValidationError(errors=[err.detail for err in validation_errors])

        order_id = uuid7()

        warehouse_by_product = await self._reserve_cart_items(
            cart_items, reference_id=str(order_id)
        )

        builder = OrderBuilder()
        builder.add_items(cart_items)
        builder.calculate_subtotal()
        builder.apply_tax_strategy(tax_strategy)
        builder.apply_discounts(user_uuid)
        builder.calculate_total()
        builder.set_shipping_address(shipping_address)
        builder.set_payment_method(payment_method)

        order = builder.build()
        order.id = order_id
        order.user_uuid = user_uuid
        order.status = OrderStatus.PENDING.value
        order.tax_strategy = tax_strategy
        order.idempotency_key = idempotency_key
        order.notes = notes
        for item in order.items:
            warehouse_id_str = warehouse_by_product.get(str(item.product_id))
            item.warehouse_id = (
                uuid.UUID(warehouse_id_str) if warehouse_id_str else None
            )

        order = await self._order_repo.create(session, order)

        await self._cart_service.clear_cart(user_uuid_str)

        return order

    async def _reserve_cart_items(
        self, cart_items: dict[str, int], *, reference_id: str | None
    ) -> dict[str, str]:
        """Reserve every cart item, releasing all of them if any one fails.

        Returns {product_id: warehouse_id} for the successfully reserved
        items — the caller stores this on each OrderItem so cancel_order()
        later releases from the exact warehouse the stock came from.
        """
        warehouse_by_product: dict[str, str] = {}
        try:
            for product_uuid, qty in cart_items.items():
                result = await self._inventory_client.reserve(
                    product_uuid, qty, reference_id=reference_id
                )
                warehouse_by_product[product_uuid] = result["warehouse_id"]
        except InsufficientStockError as exc:
            await self._release_reserved(warehouse_by_product, cart_items, reference_id)
            raise ValidationError(str(exc)) from exc
        except Exception:
            await self._release_reserved(warehouse_by_product, cart_items, reference_id)
            raise
        return warehouse_by_product

    async def _release_reserved(
        self,
        warehouse_by_product: dict[str, str],
        cart_items: dict[str, int],
        reference_id: str | None,
    ) -> None:
        """Best-effort compensating release for a checkout that failed partway through."""
        for product_uuid, warehouse_id in warehouse_by_product.items():
            try:
                await self._inventory_client.release(
                    product_uuid,
                    warehouse_id,
                    cart_items[product_uuid],
                    reference_id=reference_id,
                )
            except Exception:
                logger.exception(
                    "Failed to release reserved stock for product %s during "
                    "checkout rollback — stock will be stuck reserved until "
                    "manually corrected",
                    product_uuid,
                )

    async def get_order(
        self, *, session: AsyncSession, order_uuid: uuid.UUID
    ) -> Order:
        """Get an order by UUID."""
        order = await self._order_repo.get_by_uuid(session, order_uuid)
        if not order:
            raise NotFoundError(f"Order {order_uuid} not found")
        return order

    async def get_user_orders(
        self,
        *,
        session: AsyncSession,
        user_uuid: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:
        """Get paginated orders for a user."""
        return await self._order_repo.get_by_user(
            session, user_uuid, page=page, page_size=page_size
        )

    async def cancel_order(
        self,
        *,
        session: AsyncSession,
        order_uuid: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> Order:
        """Cancel an order and release reserved stock."""
        order = await self._order_repo.get_by_uuid(session, order_uuid)
        if not order:
            raise NotFoundError(f"Order {order_uuid} not found")

        if order.user_uuid != user_uuid:
            raise ForbiddenError("Order does not belong to user")

        current_status = OrderStatus(order.status)
        try:
            ORDER_STATE_MACHINE.assert_transition(current_status, OrderStatus.CANCELLED)
        except InvalidTransitionError as exc:
            raise ConflictError(
                f"Cannot cancel order in status {order.status}"
            ) from exc

        for item in order.items:
            if item.warehouse_id is None:
                continue
            try:
                await self._inventory_client.release(
                    str(item.product_id),
                    str(item.warehouse_id),
                    item.quantity,
                    reference_id=str(order.id),
                )
            except Exception:
                logger.exception(
                    "Failed to release stock for product %s", item.product_id
                )

        order = await self._order_repo.update_status(
            session,
            order,
            OrderStatus.CANCELLED.value,
            changed_by=user_uuid,
            comment="Cancelled by user",
        )
        return order

    async def get_expired_orders(
        self, *, session: AsyncSession, expiration_minutes: int
    ) -> list[Order]:
        """Get orders that have expired."""
        return await self._order_repo.get_expired_orders(session, expiration_minutes)

    @staticmethod
    def can_transition(current_status: OrderStatus, new_status: OrderStatus) -> bool:
        """Check if a status transition is allowed."""
        return ORDER_STATE_MACHINE.can_transition(current_status, new_status)
