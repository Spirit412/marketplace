import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from src.enums.report import ReportFormat, ReportType


class DateRange(BaseModel):
    from_date: date
    to_date: date


class GenerateReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_type: ReportType
    date_range: DateRange
    seller_id: uuid.UUID | None = None
    format: ReportFormat = ReportFormat.CSV
