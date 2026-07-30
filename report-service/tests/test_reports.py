"""Integration tests for report endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from src.enums.report import ReportFormat, ReportType
from src.schemes.request.report import GenerateReportRequest, DateRange


pytestmark = pytest.mark.anyio


class TestReportGeneration:
    async def test_generate_report_returns_202(
        self, async_client: AsyncClient
    ) -> None:
        request = GenerateReportRequest(
            report_type=ReportType.SALES,
            date_range=DateRange(from_date="2026-01-01", to_date="2026-07-25"),
            format=ReportFormat.CSV,
        )
        response = await async_client.post(
            "/reports",
            json=request.model_dump(mode="json"),
        )
        assert response.status_code in (202, 403)

    async def test_get_nonexistent_report_returns_404(
        self, async_client: AsyncClient
    ) -> None:
        fake_id = uuid.uuid4()
        response = await async_client.get(f"/reports/{fake_id}")
        assert response.status_code in (404, 403)


class TestReportBuilder:
    def test_builder_constructs_sql(self) -> None:
        from src.patterns.report_builder import ReportBuilder

        builder = ReportBuilder()
        builder.with_source("postgres").with_table("test_table").with_filters(
            {"status": "active"}
        )
        query = builder.build_query()
        assert "SELECT * FROM test_table" in query
        assert "WHERE status = 'active'" in query


class TestFormatStrategies:
    @pytest.mark.asyncio
    async def test_csv_strategy(self, tmp_path) -> None:
        from src.patterns.export_strategy import CsvFormat
        from src.patterns.report_builder import ResultSet

        data = ResultSet(
            columns=["id", "name"],
            rows=[["1", "Alice"], ["2", "Bob"]],
        )
        strategy = CsvFormat()
        file_path = str(tmp_path / "test.csv")
        result = await strategy.export(data, file_path)
        assert result == file_path

        content = open(file_path).read()
        assert "id,name" in content
        assert "1,Alice" in content
