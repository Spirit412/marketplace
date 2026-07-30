from dataclasses import dataclass, field
from typing import Literal

from src.enums.report import ReportFormat, ReportType


@dataclass
class ReportConfig:
    source: Literal["postgres"]
    table: str
    columns: list[str]
    available_aggregations: list[str] = field(default_factory=list)
    default_format: ReportFormat = ReportFormat.CSV
    required_filters: list[str] = field(default_factory=list)


REPORT_TYPE_REGISTRY: dict[ReportType, ReportConfig] = {
    ReportType.SALES: ReportConfig(
        source="postgres",
        table="order.orders",
        columns=["id", "created_at", "seller_id", "total", "currency", "status"],
        available_aggregations=["seller_id", "created_at"],
        default_format=ReportFormat.XLSX,
        required_filters=["date_range"],
    ),
    ReportType.INVENTORY: ReportConfig(
        source="postgres",
        table="inventory.stock_items",
        columns=[
            "product_id",
            "warehouse_id",
            "quantity",
            "reserved",
            "updated_at",
        ],
        available_aggregations=["warehouse_id"],
        default_format=ReportFormat.CSV,
        required_filters=[],
    ),
    ReportType.CUSTOMERS: ReportConfig(
        source="postgres",
        table="auth.users",
        columns=["id", "email", "role", "created_at"],
        available_aggregations=["role"],
        default_format=ReportFormat.CSV,
        required_filters=[],
    ),
    ReportType.PRODUCTS: ReportConfig(
        source="postgres",
        table="catalog.products",
        columns=["id", "seller_id", "name", "price", "is_active", "created_at"],
        available_aggregations=["seller_id"],
        default_format=ReportFormat.XLSX,
        required_filters=[],
    ),
}
