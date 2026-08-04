from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.enums.report import ReportFormat, ReportType


class DateRange(BaseModel):
    from_date: date = Field(description="Start of the range, inclusive.")
    to_date: date = Field(description="End of the range, inclusive.")


class GenerateReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_type: ReportType = Field(
        description="Kind of report to generate.", examples=["sales"]
    )
    date_range: DateRange = Field(description="Period the report covers.")
    seller_id: UUID | None = Field(
        default=None,
        description="Restrict the report to this seller; omit for all sellers.",
        examples=["019f0000-0000-7000-8000-000000000030"],
    )
    format: ReportFormat = Field(
        default=ReportFormat.CSV, description="Output file format.", examples=["csv"]
    )
