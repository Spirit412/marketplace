from typing import Any

from pydantic import BaseModel, Field

from src.enums.dictionary_type import DictionaryType


class CreateDictionaryEntry(BaseModel):
    type: DictionaryType = Field(
        description="Dictionary type.", examples=["currencies"]
    )
    code: str = Field(
        min_length=1,
        description="Entry code, unique within its type.",
        examples=["USD"],
    )
    data: dict[str, Any] = Field(
        description="Arbitrary entry payload.",
        examples=[{"label": "US Dollar", "symbol": "$"}],
    )
