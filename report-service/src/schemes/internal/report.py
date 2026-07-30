
import uuid
from datetime import datetime

from pydantic import BaseModel

from src.enums.report import ReportFormat, ReportType


class ReportGeneratedPayload(BaseModel):
    report_id: uuid.UUID
    user_uuid: uuid.UUID
    seller_id: uuid.UUID | None = None
    report_type: ReportType
    file_url: str
    format: ReportFormat
    created_at: datetime
    expires_at: datetime
