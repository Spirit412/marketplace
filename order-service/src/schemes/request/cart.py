from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartItemRequest(BaseModel):
    """Request body for cart add operation."""

    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    quantity: int = Field(default=1, ge=1, le=100)
