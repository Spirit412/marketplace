"""Composed response for GET /storefront/products/{id}.

catalog-service's own `Product.stock` field is a creation-time snapshot —
nothing keeps it in sync with actual reservations in inventory-service (the
`stock.changed` → catalog sync event was planned but never wired up, see
Архитектура взаимодействия сервисов §4). `available`/`warehouse_id` here
come from a live inventory-service call instead, which is the whole reason
this composed endpoint exists rather than just returning catalog's product
as-is.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class StorefrontProductResponse(BaseModel):
    id: UUID = Field(
        description="Product UUID (catalog-service).",
        examples=["019f0000-0000-0000-0000-000000000001"],
    )
    seller_id: UUID = Field(
        description="UUID of the seller who owns this product.",
        examples=["019f0000-0000-0000-0000-000000000002"],
    )
    category_id: UUID | None = Field(
        default=None,
        description="Category UUID, if the product is categorized.",
        examples=["019f0000-0000-0000-0000-000000000004"],
    )
    name: str = Field(description="Product name.", examples=["Wireless Mouse"])
    description: str | None = Field(
        default=None,
        description="Free-text product description.",
        examples=["Ergonomic wireless mouse, 2.4GHz, USB-C rechargeable."],
    )
    price: float = Field(
        description="Unit price in the seller's currency (rubles).",
        examples=[1990.0],
    )
    sku: str | None = Field(
        default=None,
        description="Seller-defined stock-keeping unit.",
        examples=["WM-2400-BLK"],
    )
    rating: float = Field(description="Average customer rating, 0-5.", examples=[4.5])
    custom_properties_config: dict[str, Any] = Field(
        description="Seller-defined custom attributes (e.g. color, size).",
        examples=[{"color": "black", "wireless": True}],
    )
    images: dict[str, Any] = Field(
        description="Product image URLs keyed by role (e.g. main, gallery).",
        examples=[{"main": "https://cdn.example.com/products/wm-2400.jpg"}],
    )
    is_active: bool = Field(
        description="Whether the seller has the product published.",
        examples=[True],
    )
    status: str = Field(description="Moderation/lifecycle status.", examples=["active"])
    created_at: datetime = Field(
        description="When the product was created.",
        examples=["2026-01-01T00:00:00Z"],
    )
    updated_at: datetime = Field(
        description="When the product was last updated.",
        examples=["2026-01-01T00:00:00Z"],
    )

    # From inventory-service — None if inventory-service was unreachable
    # (degrade the card, don't fail the whole request over it) or if no
    # warehouse currently holds any.
    available: int | None = Field(
        default=None,
        description=(
            "Live units in stock across warehouses, from inventory-service. "
            "`null` if inventory-service was unreachable (the card still "
            "renders) or if the product isn't stocked anywhere."
        ),
        examples=[12],
    )
    warehouse_id: UUID | None = Field(
        default=None,
        description="Warehouse UUID the `available` count was read from.",
        examples=["019f0000-0000-0000-0000-000000000003"],
    )
