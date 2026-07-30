from pydantic import BaseModel, ConfigDict, Field


class CreateQuerySetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    data: dict = Field(default_factory=dict)
    displayed_fields: dict = Field(default_factory=dict)
    tags: dict = Field(default_factory=dict)


class UpdateQuerySetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)
    data: dict | None = None
    displayed_fields: dict | None = None
    tags: dict | None = None
