from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartItemRequest(BaseModel):
    """Request body for cart add operation."""

    model_config = ConfigDict(extra="forbid")

    product_id: UUID = Field(
        description="Product id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000050"],
    )
    quantity: int = Field(
        default=1, ge=1, le=100, description="Units to add.", examples=[1]
    )
