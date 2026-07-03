from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }
        event_data = getattr(record, "aegis_event", None)
        if isinstance(event_data, dict):
            payload.update(event_data)
        else:
            payload["message"] = record.getMessage()
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True, default=str)


def configure_structured_logging() -> None:
    logger = logging.getLogger("aegisqa")
    if any(
        getattr(handler, "_aegisqa_json_handler", False)
        for handler in logger.handlers
    ):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    handler._aegisqa_json_handler = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = True


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    **fields: object,
) -> None:
    logger.log(
        level,
        event,
        extra={"aegis_event": {"event": event, **fields}},
    )
