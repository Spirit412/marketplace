import csv
import io
from abc import ABC, abstractmethod

from src.models.models import StockMovement


class ReceiptStrategy(ABC):
    @abstractmethod
    async def execute(self, data: dict) -> list[StockMovement]: ...


class ManualReceipt(ReceiptStrategy):
    """Single-item manual receipt."""

    async def execute(self, data: dict) -> list[StockMovement]:
        return []


class CSVImportReceipt(ReceiptStrategy):
    """Bulk receipt via CSV file parsing."""

    async def execute(self, data: dict) -> list[StockMovement]:
        csv_content = data.get("csv_content", "")
        reader = csv.DictReader(io.StringIO(csv_content))
        return []


class SupplierDeliveryReceipt(ReceiptStrategy):
    """Receipt from supplier delivery (integration with import-service)."""

    async def execute(self, data: dict) -> list[StockMovement]:
        return []
