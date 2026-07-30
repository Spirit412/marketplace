from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class CategoryPropertyResponse(BaseModel):
    id: uuid.UUID
    property_id: uuid.UUID
    is_required: bool
    sort_order: int

    model_config = {"from_attributes": True}


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    parent_id: uuid.UUID | None = None
    lft: int = 0
    rgt: int = 0
    tree_id: int = 0
    level: int = 0
    properties: list[CategoryPropertyResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryTreeResponse(BaseModel):
    items: list[CategoryResponse]
