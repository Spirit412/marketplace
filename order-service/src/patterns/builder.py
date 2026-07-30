import uuid
from typing import Any

from src.models.order import Order, OrderItem


class OrderBuilder:
    """Fluent builder for constructing Order objects."""

    TAX_RATES: dict[str, float] = {
        "RU": 0.20,
        "US": 0.08,
        "EU": 0.21,
    }

    def __init__(self) -> None:
        self._order = Order()
        self._order.subtotal = 0
        self._order.tax = 0
        self._order.discount = 0
        self._order.shipping = 0
        self._order.total = 0

    def add_items(self, cart_items: dict[str, int]) -> "OrderBuilder":
        """Add OrderItem entries from cart data {product_uuid: quantity}.

        Price is set to 0 — caller should populate prices before building.
        """
        self._order.items = []
        for product_uuid, quantity in cart_items.items():
            item = OrderItem(
                order_id=self._order.id,
                product_id=uuid.UUID(product_uuid),
                product_name="",
                price=0,
                quantity=quantity,
                seller_id=None,
            )
            self._order.items.append(item)
        return self

    def calculate_subtotal(self) -> "OrderBuilder":
        """Calculate subtotal from items."""
        self._order.subtotal = sum(
            item.price * item.quantity for item in self._order.items
        )
        return self

    def apply_tax_strategy(self, region: str) -> "OrderBuilder":
        """Apply tax rate based on region."""
        rate = self.TAX_RATES.get(region, 0.0)
        self._order.tax = int(self._order.subtotal * rate)
        self._order.tax_strategy = region
        return self

    def apply_discounts(self, user_uuid: uuid.UUID | None) -> "OrderBuilder":
        """Apply discounts (noop for now)."""
        self._order.discount = 0
        return self

    def calculate_total(self) -> "OrderBuilder":
        """Calculate order total."""
        self._order.total = (
            self._order.subtotal
            + self._order.tax
            + self._order.shipping
            - self._order.discount
        )
        return self

    def set_shipping_address(self, address: dict[str, Any]) -> "OrderBuilder":
        """Set the shipping address."""
        self._order.shipping_address = address
        return self

    def set_payment_method(self, method: str) -> "OrderBuilder":
        """Set the payment method."""
        self._order.payment_method = method
        return self

    def build(self) -> Order:
        """Return the constructed Order (unsaved)."""
        return self._order
