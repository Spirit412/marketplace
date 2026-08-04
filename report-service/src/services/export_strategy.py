import asyncio
import csv
import io
from abc import ABC, abstractmethod
from pathlib import Path

try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
except ImportError:
    colors = A4 = SimpleDocTemplate = Table = TableStyle = None

from src.enums.report import ReportFormat
from src.services.report_builder import ResultSet


class FormatStrategy(ABC):
    """Abstract strategy for formatting report data into a file."""

    @abstractmethod
    async def export(self, data: ResultSet, file_path: str) -> str: ...


class CsvFormat(FormatStrategy):
    async def export(self, data: ResultSet, file_path: str) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(data.columns)
        for row in data.rows:
            writer.writerow(row)

        path = Path(file_path)

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(output.getvalue())

        await asyncio.to_thread(_write)
        return str(path)


class XlsxFormat(FormatStrategy):
    async def export(self, data: ResultSet, file_path: str) -> str:
        if Workbook is None:
            raise ImportError("openpyxl is required for XLSX export")

        wb = Workbook()
        ws = wb.active
        if ws is None:
            ws = wb.create_sheet()

        ws.append(data.columns)
        for row in data.rows:
            ws.append(row)

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(path))
        return str(path)


class PdfFormat(FormatStrategy):
    async def export(self, data: ResultSet, file_path: str) -> str:
        if SimpleDocTemplate is None:
            raise ImportError("reportlab is required for PDF export")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(str(path), pagesize=A4)
        table_data = [data.columns] + [[str(cell) for cell in row] for row in data.rows]
        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        doc.build([table])
        return str(path)


class FormatStrategyRegistry:
    """Registry of format strategies, keyed by ReportFormat."""

    def __init__(self) -> None:
        self._strategies: dict[ReportFormat, FormatStrategy] = {
            ReportFormat.CSV: CsvFormat(),
            ReportFormat.XLSX: XlsxFormat(),
            ReportFormat.PDF: PdfFormat(),
        }

    def get(self, fmt: ReportFormat) -> FormatStrategy:
        strategy = self._strategies.get(fmt)
        if strategy is None:
            msg = f"Unsupported report format: {fmt}"
            raise ValueError(msg)
        return strategy
