import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: uuid.UUID
    seller_id: uuid.UUID
    category_id: uuid.UUID | None = None
    name: str
    description: str | None = None
    price: float
    sku: str | None = None
    stock: int
    rating: float
    custom_properties_config: dict[str, Any]
    images: dict[str, Any]
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
