
from pydantic import BaseModel, ConfigDict

from src.enums.import_type import ImportType


class UploadCSVRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    import_type: ImportType


class MappingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    column_mapping: dict[str, str]
