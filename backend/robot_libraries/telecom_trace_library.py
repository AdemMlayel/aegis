from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.graph.artifacts import PROJECT_ROOT

try:
    from robot.api.deco import keyword
except ImportError:  # pragma: no cover - exercised only without Robot installed.

    def keyword(name: str):
        def decorator(func):
            return func

        return decorator


FIXTURE_ROOT = (PROJECT_ROOT / "fixtures").resolve()


class TelecomTraceLibrary:
    """Approved Robot keywords for sanitized telecom trace fixtures."""

    def __init__(self) -> None:
        self._trace: dict[str, Any] | None = None

    @keyword("Load Sanitized Trace")
    def load_sanitized_trace(self, fixture_path: str) -> str:
        resolved_path = _resolve_fixture_path(fixture_path)
        try:
            payload = json.loads(resolved_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"Trace fixture is not valid JSON: {fixture_path}"
            ) from exc

        events = payload.get("events")
        if not isinstance(events, list) or not events:
            raise AssertionError(
                f"Trace fixture has no events: {payload.get('fixture_id', fixture_path)}"
            )
        self._trace = payload
        return str(payload.get("fixture_id", resolved_path.name))

    @keyword("Verify SIP Header Present")
    def verify_sip_header_present(self, message: str, header: str) -> bool:
        event = self._find_event(protocol="SIP", message=message)
        headers = event.get("headers")
        if not isinstance(headers, list):
            raise AssertionError(f"SIP message has no header list: {message}")
        if header not in headers:
            raise AssertionError(f"SIP header '{header}' is missing from {message}")
        return True

    @keyword("Verify Diameter Session Match")
    def verify_diameter_session_match(
        self,
        request_message: str,
        answer_message: str,
    ) -> bool:
        request = self._find_event(protocol="Diameter", message=request_message)
        answer = self._find_event(protocol="Diameter", message=answer_message)
        request_session = request.get("session_id")
        answer_session = answer.get("session_id")
        if not request_session or not answer_session:
            raise AssertionError(
                f"Diameter session id is missing for {request_message}/{answer_message}"
            )
        if request_session != answer_session:
            raise AssertionError(
                f"Diameter Session-Id mismatch for {request_message}/{answer_message}"
            )
        return True

    @keyword("Verify Diameter Result Code")
    def verify_diameter_result_code(self, message: str, result_code: str) -> bool:
        event = self._find_event(protocol="Diameter", message=message)
        actual_result_code = event.get("result_code")
        if actual_result_code != result_code:
            raise AssertionError(
                f"Diameter result code mismatch for {message}: expected {result_code}"
            )
        return True

    @keyword("Verify Flexible Sequence")
    def verify_flexible_sequence(self, template_name: str) -> bool:
        trace = self._require_trace()
        templates = trace.get("sequence_templates")
        if not isinstance(templates, dict) or template_name not in templates:
            raise AssertionError(f"Unknown sequence template: {template_name}")

        expected_sequence = templates[template_name]
        if not isinstance(expected_sequence, list) or not expected_sequence:
            raise AssertionError(f"Sequence template has no events: {template_name}")

        event_ids = [
            str(event.get("id"))
            for event in self._events()
            if isinstance(event.get("id"), str)
        ]
        missing = [
            event_id for event_id in expected_sequence if event_id not in event_ids
        ]
        if missing:
            raise AssertionError(
                f"Trace is missing expected sequence events: {', '.join(missing)}"
            )

        event_positions = {
            event_id: event_ids.index(event_id) for event_id in expected_sequence
        }
        flexible_group_by_event = _flexible_group_by_event(trace)
        last_position = -1
        index = 0
        while index < len(expected_sequence):
            event_id = expected_sequence[index]
            flexible_group = flexible_group_by_event.get(event_id)
            if flexible_group:
                group_events: list[str] = []
                while (
                    index < len(expected_sequence)
                    and expected_sequence[index] in flexible_group
                ):
                    group_events.append(expected_sequence[index])
                    index += 1
                group_positions = [
                    event_positions[group_event] for group_event in group_events
                ]
                if min(group_positions) < last_position:
                    raise AssertionError(
                        f"Trace event order violates sequence template: {template_name}"
                    )
                last_position = max(group_positions)
                continue

            event_position = event_positions[event_id]
            if event_position < last_position:
                raise AssertionError(
                    f"Trace event order violates sequence template: {template_name}"
                )
            last_position = event_position
            index += 1
        return True

    def _find_event(self, *, protocol: str, message: str) -> dict[str, Any]:
        normalized_protocol = protocol.strip().lower()
        normalized_message = message.strip().lower()
        for event in self._events():
            if (
                str(event.get("protocol", "")).strip().lower() == normalized_protocol
                and str(event.get("message", "")).strip().lower()
                == normalized_message
            ):
                return event
        raise AssertionError(f"Trace event not found: {protocol} {message}")

    def _events(self) -> list[dict[str, Any]]:
        trace = self._require_trace()
        events = trace.get("events")
        if not isinstance(events, list):
            raise AssertionError("Loaded trace has no events list")
        return [event for event in events if isinstance(event, dict)]

    def _require_trace(self) -> dict[str, Any]:
        if self._trace is None:
            raise AssertionError("Load Sanitized Trace must run before validation")
        return self._trace


def _resolve_fixture_path(fixture_path: str) -> Path:
    candidate = Path(fixture_path)
    if candidate.is_absolute():
        raise ValueError("Trace fixture path must be relative to the project")
    resolved = (PROJECT_ROOT / candidate).resolve()
    try:
        resolved.relative_to(FIXTURE_ROOT)
    except ValueError as exc:
        raise ValueError("Trace fixture path must stay under fixtures/") from exc
    if resolved.suffix.lower() != ".json":
        raise ValueError("Trace fixture must be a JSON file")
    if not resolved.is_file():
        raise FileNotFoundError(f"Trace fixture does not exist: {fixture_path}")
    return resolved


def _flexible_event_groups(trace: dict[str, Any]) -> list[set[str]]:
    groups = trace.get("flexible_order_groups", [])
    if not isinstance(groups, list):
        return []
    normalized_groups: list[set[str]] = []
    for group in groups:
        if isinstance(group, list):
            normalized_groups.append({str(event_id) for event_id in group})
    return normalized_groups


def _flexible_group_by_event(trace: dict[str, Any]) -> dict[str, set[str]]:
    group_by_event: dict[str, set[str]] = {}
    for group in _flexible_event_groups(trace):
        for event_id in group:
            group_by_event[event_id] = group
    return group_by_event
