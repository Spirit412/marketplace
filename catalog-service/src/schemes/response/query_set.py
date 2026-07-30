import uuid
from datetime import datetime

from pydantic import BaseModel


class QuerySetResponse(BaseModel):
    id: uuid.UUID
    seller_id: uuid.UUID
    name: str
    data: dict
    displayed_fields: dict
    is_favorite: bool
    is_system: bool
    tags: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuerySetListResponse(BaseModel):
    items: list[QuerySetResponse]
    total: int
    page: int
    page_size: int
