
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from src.enums.dictionary_type import DictionaryType


class DictionaryUpdatedPayload(BaseModel):
    type: DictionaryType
    code: str
    action: Literal["created", "updated", "deleted"]
    changed_at: datetime
