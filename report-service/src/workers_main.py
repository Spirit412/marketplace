"""FastStream worker entry point for report-service.

Subscribes to report.generate.* events and processes them asynchronously.
"""

from src.engines.rabbitmq import get_broker
from src.services.report_service import ReportService

_broker = None


def _get_broker():
    global _broker
    if _broker is None:
        _broker = get_broker()
    return _broker


async def handle_report_generation(
    payload: dict,
) -> None:
    """Handle async report generation requests."""
    from src.core.database import _get_session_factory
    from src.engines.file_storage import LocalFileStorage
    from src.repositories.report_repo import ReportRepo
    from src.repositories.template_repo import ReportTemplateRepo

    session_factory = _get_session_factory()
    async with session_factory() as session:
        service = ReportService(ReportRepo(), ReportTemplateRepo(), LocalFileStorage())

        import uuid

        await service.process_generation(
            session,
            report_id=uuid.UUID(payload["report_id"]),
            report_type=payload["report_type"],
            fmt=payload["format"],
            parameters=payload.get("parameters", {}),
        )


def _register_subscriber() -> None:
    _get_broker().subscriber("report.generate.*")(handle_report_generation)


_register_subscriber()
