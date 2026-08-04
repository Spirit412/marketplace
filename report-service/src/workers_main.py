"""FastStream worker entry point for report-service.

Subscribes to report.generate.* events and processes them asynchronously.
"""

from typing import Any
from uuid import UUID

from src.core.database import _get_session_factory
from src.engines.file_storage import LocalFileStorage
from src.engines.rabbitmq import get_broker
from src.repositories.report_repo import ReportRepo
from src.repositories.template_repo import ReportTemplateRepo
from src.services.report_service import ReportService


async def handle_report_generation(
    payload: dict[str, Any],
) -> None:
    """Handle async report generation requests."""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        service = ReportService(ReportRepo(), ReportTemplateRepo(), LocalFileStorage())

        await service.process_generation(
            session,
            report_id=UUID(payload["report_id"]),
            report_type=payload["report_type"],
            fmt=payload["format"],
            parameters=payload.get("parameters", {}),
        )


def _register_subscriber() -> None:
    get_broker().subscriber("report.generate.*")(handle_report_generation)


_register_subscriber()
