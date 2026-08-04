from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CartItemResponse(BaseModel):
    """Single cart item."""

    product_id: UUID
    quantity: int


class CartResponse(BaseModel):
    """Full cart contents."""

    model_config = ConfigDict(from_attributes=True)

    items: list[CartItemResponse]
