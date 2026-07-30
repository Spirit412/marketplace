import json
import logging
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.datatype import uuid7
from src.engines.file_storage import LocalFileStorage
from src.engines.rabbitmq import get_broker
from src.engines.redis import get_redis_client
from src.enums.report import (
    REPORT_STATE_MACHINE,
    ReportFormat,
    ReportStatus,
    ReportType,
)
from src.models.report import Report
from src.patterns.export_strategy import FormatStrategyRegistry
from src.patterns.report_builder import ReportBuilder
from src.patterns.report_registry import REPORT_TYPE_REGISTRY
from src.repositories.report_repo import ReportRepo
from src.repositories.template_repo import ReportTemplateRepo
from src.schemes.request.report import GenerateReportRequest
from src.schemes.response.report import (
    ReportListResponse,
    ReportResponse,
)

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(
        self,
        report_repo: ReportRepo,
        template_repo: ReportTemplateRepo,
        file_storage: LocalFileStorage,
    ) -> None:
        self._report_repo = report_repo
        self._template_repo = template_repo
        self._file_storage = file_storage
        self._format_registry = FormatStrategyRegistry()
        self._settings = settings

    async def generate(
        self,
        session: AsyncSession,
        request: GenerateReportRequest,
        user_uuid: uuid.UUID,
    ) -> ReportResponse:
        """Initiate report generation. Publishes to RabbitMQ for async processing."""
        config = REPORT_TYPE_REGISTRY.get(request.report_type)
        if config is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported report type: {request.report_type}",
            )

        report = Report(
            id=uuid7(),
            user_uuid=user_uuid,
            report_type=request.report_type.value,
            parameters={
                "date_from": request.date_range.from_date.isoformat(),
                "date_to": request.date_range.to_date.isoformat(),
                "seller_id": str(request.seller_id) if request.seller_id else None,
                "format": request.format.value,
            },
            format=request.format.value,
            status=ReportStatus.PENDING.value,
        )

        report = await self._report_repo.create(session, report)

        try:
            broker = get_broker()
            await broker.publish(
                {
                    "report_id": str(report.id),
                    "user_uuid": str(user_uuid),
                    "report_type": request.report_type.value,
                    "format": request.format.value,
                    "parameters": report.parameters,
                },
                routing_key=f"report.generate.{request.report_type.value}",
            )
        except Exception:
            await self._transition_status(
                session,
                report.id,
                ReportStatus.FAILED,
                error_message="Failed to publish generation event",
            )
            raise HTTPException(
                status_code=503,
                detail="Report generation queue unavailable",
            )

        return ReportResponse.model_validate(report)

    async def _transition_status(
        self,
        session: AsyncSession,
        report_id: uuid.UUID,
        new_status: ReportStatus,
        *,
        file_path: str | None = None,
        error_message: str | None = None,
    ) -> Report | None:
        """Validate and apply a report status transition.

        Reports are updated by an async worker with no HTTP caller to
        surface a conflict to, so an invalid transition is logged and
        skipped rather than raised.
        """
        report = await self._report_repo.get_by_id(session, report_id)
        if report is None:
            return None

        current_status = ReportStatus(report.status)
        if not REPORT_STATE_MACHINE.can_transition(current_status, new_status):
            logger.warning(
                "Skipping invalid report status transition %s -> %s for report %s",
                current_status,
                new_status,
                report_id,
            )
            return report

        return await self._report_repo.update_status(
            session,
            report_id,
            new_status.value,
            file_path=file_path,
            error_message=error_message,
        )

    async def get_report(
        self, session: AsyncSession, report_id: uuid.UUID
    ) -> ReportResponse:
        """Get report metadata by ID."""
        report = await self._report_repo.get_by_id(session, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        return ReportResponse.model_validate(report)

    async def download(
        self, session: AsyncSession, report_id: uuid.UUID
    ) -> tuple[bytes, str, str]:
        """Download a generated report file.

        Returns (content, filename, media_type).
        """
        redis_client = get_redis_client()
        cache_key = f"report:{report_id}:download"
        cached = await redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            content = await self._file_storage.get(data["file_path"])
            filename = f"report_{report_id}.{data['format']}"
            media_type = self._get_media_type(data["format"])
            return content, filename, media_type

        report = await self._report_repo.get_by_id(session, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")

        if report.status == ReportStatus.PENDING.value:
            raise HTTPException(
                status_code=202,
                detail="Report generation in progress",
                headers={"Retry-After": "30"},
            )

        if report.status == ReportStatus.GENERATING.value:
            raise HTTPException(
                status_code=202,
                detail="Report is being generated",
                headers={"Retry-After": "10"},
            )

        if report.status == ReportStatus.FAILED.value:
            raise HTTPException(
                status_code=500,
                detail=f"Report generation failed: {report.error_message or 'Unknown error'}",
            )

        if report.file_path is None:
            raise HTTPException(status_code=404, detail="Report file not available")

        content = await self._file_storage.get(report.file_path)
        filename = f"report_{report_id}.{report.format}"
        media_type = self._get_media_type(report.format)

        return content, filename, media_type

    async def list_reports(
        self,
        session: AsyncSession,
        user_uuid: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> ReportListResponse:
        reports, total = await self._report_repo.list_by_user(
            session, user_uuid, offset=offset, limit=limit
        )
        return ReportListResponse(
            reports=[ReportResponse.model_validate(report) for report in reports],
            total=total,
        )

    async def process_generation(
        self,
        session: AsyncSession,
        report_id: uuid.UUID,
        report_type: str,
        fmt: str,
        parameters: dict[str, Any],
    ) -> None:
        """Background task: execute query, format, save, and publish completion."""
        try:
            await self._transition_status(session, report_id, ReportStatus.GENERATING)

            builder = ReportBuilder()
            config = REPORT_TYPE_REGISTRY.get(ReportType(report_type))
            if config:
                builder.with_source(config.source).with_table(config.table)
                builder.with_columns(config.columns)

            builder.with_filters(parameters)
            result_set = await builder.execute()

            report_format = ReportFormat(fmt)
            strategy = self._format_registry.get(report_format)
            file_path = f"{report_id}/report.{fmt}"
            saved_path = await strategy.export(result_set, file_path)

            file_content = open(saved_path, "rb").read()
            await self._file_storage.save(file_content, file_path)

            await self._transition_status(
                session,
                report_id,
                ReportStatus.COMPLETED,
                file_path=file_path,
            )

            redis_client = get_redis_client()
            cache_key = f"report:{report_id}:download"
            await redis_client.setex(
                cache_key,
                self._settings.REPORT_TTL,
                json.dumps({"file_path": file_path, "format": fmt}),
            )

            broker = get_broker()
            await broker.publish(
                {
                    "report_id": str(report_id),
                    "report_type": report_type,
                    "file_url": file_path,
                    "format": fmt,
                },
                routing_key="report.generated",
            )

        except Exception as exc:
            await self._transition_status(
                session,
                report_id,
                ReportStatus.FAILED,
                error_message=str(exc),
            )

    @staticmethod
    def _get_media_type(fmt: str) -> str:
        mapping = {
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pdf": "application/pdf",
        }
        return mapping.get(fmt, "application/octet-stream")
