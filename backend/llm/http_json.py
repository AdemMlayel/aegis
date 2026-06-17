from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class LLMHTTPError(RuntimeError):
    pass


def post_json(
    *,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **(headers or {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise LLMHTTPError(f"LLM provider returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise LLMHTTPError(f"LLM provider request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise LLMHTTPError("LLM provider request timed out") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMHTTPError("LLM provider returned invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise LLMHTTPError("LLM provider returned a non-object JSON payload")
    return parsed
