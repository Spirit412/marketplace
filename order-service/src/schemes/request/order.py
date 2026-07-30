from typing import Any

from pydantic import BaseModel, ConfigDict

from src.enums.order_status import PaymentMethod, TaxStrategy


class CreateOrderRequest(BaseModel):
    """Request body for order creation."""

    model_config = ConfigDict(extra="forbid")

    shipping_address: dict[str, Any]
    payment_method: PaymentMethod
    tax_strategy: TaxStrategy = TaxStrategy.RU
    notes: str | None = None
