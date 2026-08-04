from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CategoryPropertyResponse(BaseModel):
    id: UUID
    property_id: UUID
    is_required: bool
    sort_order: int

    model_config = {"from_attributes": True}


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    parent_id: UUID | None = None
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
