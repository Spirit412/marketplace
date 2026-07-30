from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str
    service: str
    timestamp: str
    checks: dict[str, dict[str, Any]] = {}


@dataclass
class HealthManager:
    service_name: str
    _checks: dict[str, Any] = field(default_factory=dict)

    def register(self, name: str, checker: Any) -> None:
        self._checks[name] = checker

    async def check(self) -> HealthStatus:
        results: dict[str, dict[str, Any]] = {}
        all_healthy = True

        for name, checker in self._checks.items():
            try:
                await checker()
                results[name] = {"status": "healthy"}
            except Exception as exc:
                results[name] = {"status": "unhealthy", "error": str(exc)}
                all_healthy = False

        return HealthStatus(
            status="healthy" if all_healthy else "degraded",
            service=self.service_name,
            timestamp=datetime.now(UTC).isoformat(),
            checks=results,
        )
