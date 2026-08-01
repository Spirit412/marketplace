import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ReportClient:
    """Client for report-service HTTP API."""

    def __init__(self, base_url: str, system_token: str, timeout: int = 30) -> None:
        self._base_url = base_url
        self._system_token = system_token
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._system_token}"}

    async def generate_daily_report(self) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.post(
                    f"{self._base_url}/reports/",
                    json={"report_type": "sales_daily", "parameters": {}},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                report: dict[str, Any] = resp.json()
            except Exception as exc:
                logger.warning("Failed to generate daily report: %s", exc)
                return None
            else:
                return report
