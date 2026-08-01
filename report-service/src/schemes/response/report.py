import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.enums.report import ReportFormat


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    report_type: str
    format: str
    status: str
    file_path: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
    total: int


class ReportDownloadLink(BaseModel):
    download_url: str
    format: ReportFormat
    expires_at: datetime
