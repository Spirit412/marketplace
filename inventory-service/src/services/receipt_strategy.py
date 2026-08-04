import csv
import io
from abc import ABC, abstractmethod
from typing import Any

from src.models.models import StockMovement


class ReceiptStrategy(ABC):
    @abstractmethod
    async def execute(self, data: dict[str, Any]) -> list[StockMovement]: ...


class ManualReceipt(ReceiptStrategy):
    """Single-item manual receipt."""

    async def execute(self, data: dict[str, Any]) -> list[StockMovement]:
        return []


class CSVImportReceipt(ReceiptStrategy):
    """Bulk receipt via CSV file parsing."""

    async def execute(self, data: dict[str, Any]) -> list[StockMovement]:
        csv_content = data.get("csv_content", "")
        csv.DictReader(io.StringIO(csv_content))
        return []


class SupplierDeliveryReceipt(ReceiptStrategy):
    """Receipt from supplier delivery (integration with import-service)."""

    async def execute(self, data: dict[str, Any]) -> list[StockMovement]:
        return []
