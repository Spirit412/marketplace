from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.enums.dictionary_type import DictionaryType


class DictionaryEntryResponse(BaseModel):
    id: UUID
    type: DictionaryType
    code: str
    data: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DictionaryListResponse(BaseModel):
    type: DictionaryType
    items: list[DictionaryEntryResponse]
    total: int
