import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.enums.order_status import OrderStatus


class OrderItemResponse(BaseModel):
    """Response schema for a single order item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    price: int
    quantity: int
    seller_id: uuid.UUID | None


class OrderResponse(BaseModel):
    """Response schema for an order."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_uuid: uuid.UUID
    status: OrderStatus
    items: list[OrderItemResponse]
    subtotal: int
    tax: int
    discount: int
    shipping: int
    total: int
    currency: str
    payment_method: str | None
    shipping_address: dict | None
    notes: str | None
    idempotency_key: str | None
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    """Paginated list of orders."""

    model_config = ConfigDict(from_attributes=True)

    items: list[OrderResponse]
    total_count: int
    page: int
    page_size: int
