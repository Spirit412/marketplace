from enum import StrEnum

from src.core.state_machine import StateMachine


class ReportType(StrEnum):
    SALES = "sales"
    INVENTORY = "inventory"
    CUSTOMERS = "customers"
    PRODUCTS = "products"


class ReportFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"


class ReportStatus(StrEnum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


REPORT_VALID_TRANSITIONS: dict[ReportStatus, set[ReportStatus]] = {
    ReportStatus.PENDING: {ReportStatus.GENERATING, ReportStatus.FAILED},
    ReportStatus.GENERATING: {ReportStatus.COMPLETED, ReportStatus.FAILED},
    ReportStatus.COMPLETED: set(),
    ReportStatus.FAILED: set(),
}

REPORT_STATE_MACHINE: StateMachine[ReportStatus] = StateMachine(
    REPORT_VALID_TRANSITIONS
)
