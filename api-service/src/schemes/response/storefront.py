"""Composed response for GET /storefront/products/{id}.

catalog-service's own `Product.stock` field is a creation-time snapshot —
nothing keeps it in sync with actual reservations in inventory-service (the
`stock.changed` → catalog sync event was planned but never wired up, see
Архитектура взаимодействия сервисов §4). `available`/`warehouse_id` here
come from a live inventory-service call instead, which is the whole reason
this composed endpoint exists rather than just returning catalog's product
as-is.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StorefrontProductResponse(BaseModel):
    id: uuid.UUID
    seller_id: uuid.UUID
    category_id: uuid.UUID | None = None
    name: str
    description: str | None = None
    price: float
    sku: str | None = None
    rating: float
    custom_properties_config: dict[str, Any]
    images: dict[str, Any]
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime

    # From inventory-service — None if inventory-service was unreachable
    # (degrade the card, don't fail the whole request over it) or if no
    # warehouse currently holds any.
    available: int | None = None
    warehouse_id: uuid.UUID | None = None
