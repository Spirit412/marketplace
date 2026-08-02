"""Centralized logging setup — plain text or single-line JSON.

Format is chosen via settings.LOG_FORMAT ("text" | "json"); JSON is meant
for log shippers (ELK, Loki, and similar) that expect one JSON object per
line. Both honor settings.LOG_LEVEL, previously declared on every service's
Settings but never actually wired up to anything -- logging worked by
accident, through Python's zero-config "handler of last resort" (stderr,
WARNING+ only, no formatting, no way to change the level).
"""

from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import UTC, datetime
from typing import Any

_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
}


class JsonFormatter(logging.Formatter):
    """One JSON object per line: timestamp, level, service, logger, message.

    Plus exception.{type,message,traceback} when the record carries one,
    plus anything passed via logging's `extra=` under an "extra" key.
    """

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "service": self._service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            payload["exception"] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(exc_value) if exc_value else None,
                "traceback": "".join(
                    traceback.format_exception(exc_type, exc_value, exc_tb)
                ),
            }
        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RECORD_ATTRS
        }
        if extra:
            payload["extra"] = extra
        return json.dumps(payload, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    def __init__(self, service_name: str) -> None:
        super().__init__(
            fmt=f"%(asctime)s {service_name} %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def configure_logging(
    service_name: str, log_format: str, log_level: str = "info"
) -> None:
    """Configure the root logger, and re-point uvicorn's own loggers at it.

    Call once, at module import time in main.py (before `app = FastAPI(...)`)
    -- not inside lifespan, which only runs once uvicorn is already serving.
    uvicorn's CLI builds its `Config` (which runs uvicorn's own
    `logging.config.dictConfig`, wiring up "uvicorn"/"uvicorn.access" with
    their own colored-console handlers) *before* it imports the ASGI app
    string, so this function actually runs after uvicorn's defaults are
    already installed. It deliberately strips those loggers' own handlers
    and lets them propagate to root instead, so access logs share the same
    format (and destination) as application logs rather than bypassing it.
    """
    formatter: logging.Formatter = (
        JsonFormatter(service_name)
        if log_format.strip().lower() == "json"
        else TextFormatter(service_name)
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    level = getattr(logging, log_level.strip().upper(), logging.INFO)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True
