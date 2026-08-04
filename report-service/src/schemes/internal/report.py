from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.enums.report import ReportFormat, ReportType


class ReportGeneratedPayload(BaseModel):
    report_id: UUID
    user_id: UUID
    seller_id: UUID | None = None
    report_type: ReportType
    file_url: str
    format: ReportFormat
    created_at: datetime
    expires_at: datetime
