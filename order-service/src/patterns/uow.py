import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.facades import InventoryClient
from src.models.order import Order
from src.patterns.builder import OrderBuilder
from src.repositories.order_repo import OrderRepo

logger = logging.getLogger(__name__)


class OrderUnitOfWork:
    """Orchestrates order creation as a transactional unit."""

    def __init__(
        self,
        order_repo: OrderRepo,
        inventory_client: InventoryClient,
        order_builder: OrderBuilder,
    ) -> None:
        self._order_repo = order_repo
        self._inventory_client = inventory_client
        self._order_builder = order_builder

    async def commit(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        cart_items: dict[str, int],
        shipping_address: dict[str, Any],
        payment_method: str,
        tax_strategy: str,
        notes: str | None = None,
    ) -> Order:
        """Execute order creation as a unit of work.

        Reservations are rolled back on failure.
        """
        # {product_uuid: (warehouse_id, quantity)} — release() must target the
        # exact warehouse reserve() picked, not just the product.
        reserved: dict[str, tuple[str, int]] = {}

        try:
            for product_uuid, quantity in cart_items.items():
                result = await self._inventory_client.reserve(product_uuid, quantity)
                reserved[product_uuid] = (result["warehouse_id"], quantity)

            builder = self._order_builder
            builder.add_items(cart_items)
            builder.calculate_subtotal()
            builder.apply_tax_strategy(tax_strategy)
            builder.apply_discounts(user_id)
            builder.calculate_total()
            builder.set_shipping_address(shipping_address)
            builder.set_payment_method(payment_method)

            order = builder.build()
            order.user_id = user_id
            order.notes = notes

            return await self._order_repo.create(session, order)

        except Exception:
            for product_uuid, (warehouse_id, quantity) in reserved.items():
                try:
                    await self._inventory_client.release(
                        product_uuid, warehouse_id, quantity
                    )
                except Exception:
                    logger.exception(
                        "Failed to release stock for %s during rollback",
                        product_uuid,
                    )
            raise
