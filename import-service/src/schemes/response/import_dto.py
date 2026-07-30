
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ImportTaskResponse(BaseModel):
    id: UUID
    seller_id: UUID
    import_type: str
    file_name: str
    status: str
    total_rows: int
    processed_rows: int
    error_rows: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ImportErrorResponse(BaseModel):
    rows: list[dict]


class ErrorTemplateResponse(BaseModel):
    code: str
    message: str
    locale: str
