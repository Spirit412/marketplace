"""Composed response for GET /orders/{id}/full.

Mirrors order-service's OrderResponse/OrderItemResponse fields (api-service
has no shared import path to those — it only ever sees their JSON), plus a
flattened payment summary. `payment` is None when the order has no payment
yet (e.g. still `pending`) — an expected state, not an error.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OrderItemComposed(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    price: int
    quantity: int
    seller_id: uuid.UUID | None = None


class PaymentSummary(BaseModel):
    id: uuid.UUID
    status: str
    amount: int
    currency: str
    gateway: str
    gateway_payment_id: str | None = None


class OrderFullResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    items: list[OrderItemComposed]
    subtotal: int
    tax: int
    discount: int
    shipping: int
    total: int
    currency: str
    payment_method: str | None = None
    shipping_address: dict[str, Any] | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    payment: PaymentSummary | None = None
