import logging

from src.config.settings import settings
from src.engines.http_client import ReportClient
from src.engines.rabbitmq import publish_event

logger = logging.getLogger(__name__)


async def daily_report_job() -> None:
    """Generate daily summary report via report-service."""
    client = ReportClient(settings.REPORT_SERVICE_URL)

    report = await client.generate_daily_report()
    if report is not None:
        report_id = report.get("id", "unknown")
        await publish_event(
            "report.generated",
            {
                "report_id": report_id,
                "report_type": "daily",
                "timestamp": report.get("timestamp", ""),
            },
        )
        logger.info("Daily report generated: %s", report_id)
    else:
        logger.warning("Daily report generation failed")
