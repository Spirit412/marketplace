"""Composed response for GET /orders/{id}/full.

Mirrors order-service's OrderResponse/OrderItemResponse fields (api-service
has no shared import path to those — it only ever sees their JSON), plus a
flattened payment summary. `payment` is None when the order has no payment
yet (e.g. still `pending`) — an expected state, not an error.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemComposed(BaseModel):
    id: UUID = Field(
        description="Order item UUID.",
        examples=["019f0000-0000-0000-0000-000000000011"],
    )
    product_id: UUID = Field(
        description="Product UUID (catalog-service).",
        examples=["019f0000-0000-0000-0000-000000000001"],
    )
    product_name: str = Field(
        description="Product name snapshotted at order time.",
        examples=["Wireless Mouse"],
    )
    price: int = Field(
        description="Unit price in kopecks, snapshotted at order time.",
        examples=[199000],
    )
    quantity: int = Field(description="Units ordered.", examples=[2])
    seller_id: UUID | None = Field(
        default=None,
        description="UUID of the seller who owns this product.",
        examples=["019f0000-0000-0000-0000-000000000002"],
    )


class PaymentSummary(BaseModel):
    id: UUID = Field(
        description="Payment UUID (payment-service).",
        examples=["019f0000-0000-0000-0000-000000000020"],
    )
    status: str = Field(
        description="Payment status: PENDING, PROCESSING, SUCCEEDED, FAILED, "
        "REFUNDED, PARTIALLY_REFUNDED or CANCELLED.",
        examples=["SUCCEEDED"],
    )
    amount: int = Field(description="Amount charged, in kopecks.", examples=[398000])
    currency: str = Field(description="ISO 4217 currency code.", examples=["RUB"])
    gateway: str = Field(
        description="Payment gateway used.", examples=["mock", "stripe", "yookassa"]
    )
    gateway_payment_id: str | None = Field(
        default=None,
        description="Gateway-side payment identifier, if the gateway assigned one.",
        examples=["mock_pi_1"],
    )


class OrderFullResponse(BaseModel):
    id: UUID = Field(
        description="Order UUID.",
        examples=["019f0000-0000-0000-0000-000000000010"],
    )
    user_id: UUID = Field(
        description="UUID of the buyer who placed the order.",
        examples=["019f0000-0000-0000-0000-000000000011"],
    )
    status: str = Field(
        description="Order status: pending, confirmed, paid, shipped, "
        "delivered or cancelled.",
        examples=["confirmed"],
    )
    items: list[OrderItemComposed] = Field(description="Order line items.")
    subtotal: int = Field(
        description="Sum of item prices before tax/shipping/discount, in kopecks.",
        examples=[398000],
    )
    tax: int = Field(description="Tax amount, in kopecks.", examples=[0])
    discount: int = Field(description="Discount amount, in kopecks.", examples=[0])
    shipping: int = Field(description="Shipping cost, in kopecks.", examples=[0])
    total: int = Field(
        description="subtotal + tax + shipping - discount, in kopecks.",
        examples=[398000],
    )
    currency: str = Field(description="ISO 4217 currency code.", examples=["RUB"])
    payment_method: str | None = Field(
        default=None,
        description="Payment method chosen at checkout.",
        examples=["MOCK"],
    )
    shipping_address: dict[str, Any] | None = Field(
        default=None,
        description="Shipping address as submitted at checkout.",
        examples=[{"city": "Moscow", "street": "Tverskaya 1"}],
    )
    notes: str | None = Field(
        default=None, description="Buyer-supplied order notes.", examples=[None]
    )
    created_at: datetime = Field(
        description="When the order was created.", examples=["2026-01-01T00:00:00Z"]
    )
    updated_at: datetime = Field(
        description="When the order was last updated.",
        examples=["2026-01-01T00:00:00Z"],
    )

    payment: PaymentSummary | None = Field(
        default=None,
        description=(
            "Payment status for this order, from payment-service. `null` "
            "if no payment has been created yet (a freshly-placed order is "
            "`pending` with no payment) or if payment-service was "
            "unreachable — the order itself still renders."
        ),
    )
