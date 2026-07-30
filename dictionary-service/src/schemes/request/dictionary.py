
from pydantic import BaseModel, Field

from src.enums.dictionary_type import DictionaryType


class CreateDictionaryEntry(BaseModel):
    type: DictionaryType
    code: str = Field(min_length=1)
    data: dict
