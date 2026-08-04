from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.enums.order_status import PaymentMethod, TaxStrategy


class CreateOrderRequest(BaseModel):
    """Request body for order creation."""

    model_config = ConfigDict(extra="forbid")

    shipping_address: dict[str, Any] = Field(
        description="Delivery address.",
        examples=[{"city": "Moscow", "street": "Tverskaya 1", "zip": "125009"}],
    )
    payment_method: PaymentMethod = Field(
        description="Payment gateway to use.", examples=["STRIPE"]
    )
    tax_strategy: TaxStrategy = Field(
        default=TaxStrategy.RU, description="Tax calculation strategy.", examples=["RU"]
    )
    notes: str | None = Field(
        default=None,
        description="Optional buyer notes.",
        examples=["Leave at the door"],
    )
