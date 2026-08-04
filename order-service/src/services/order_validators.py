from dataclasses import dataclass, field

from src.core.event import BaseEventValidator, EventError
from src.facades import InventoryClient


@dataclass
class CreateOrderContext:
    """Everything the create-order validator chain needs to inspect."""

    cart_items: dict[str, int]
    inventory_client: InventoryClient
    insufficient_products: list[str] = field(default_factory=list)


class CartNotEmptyValidator(BaseEventValidator[CreateOrderContext]):
    async def validate(self, context: CreateOrderContext) -> None:
        if not context.cart_items:
            raise EventError("Cart is empty", code="cart_empty")


class StockAvailableValidator(BaseEventValidator[CreateOrderContext]):
    """Checks every cart line, not just the first insufficient one.

    So a customer sees every out-of-stock product in a single response
    instead of fixing their cart one item at a time across repeated
    submits.
    """

    async def validate(self, context: CreateOrderContext) -> None:
        insufficient: list[str] = []
        for product_id, qty in context.cart_items.items():
            available = await context.inventory_client.check_stock(product_id, qty)
            if not available:
                insufficient.append(product_id)

        if insufficient:
            context.insufficient_products = insufficient
            msg = f"Insufficient stock for products: {', '.join(insufficient)}"
            raise EventError(
                msg,
                code="insufficient_stock",
            )
