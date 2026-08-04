from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class QuerySetResponse(BaseModel):
    id: UUID
    seller_id: UUID
    name: str
    data: dict[str, Any]
    displayed_fields: dict[str, Any]
    is_favorite: bool
    is_system: bool
    tags: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuerySetListResponse(BaseModel):
    items: list[QuerySetResponse]
    total: int
    page: int
    page_size: int
