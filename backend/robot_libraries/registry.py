from __future__ import annotations

from typing import Literal

from pydantic import Field

from backend.graph.state import StrictModel
from backend.reference_corpus.profiles import load_robot_keyword_registry


TELECOM_TRACE_LIBRARY = (
    "backend.robot_libraries.telecom_trace_library.TelecomTraceLibrary"
)


class RobotKeywordCapability(StrictModel):
    name: str
    library: str
    domain: str
    args: tuple[str, ...] = Field(default_factory=tuple)
    runtime: Literal["robot_framework"] = "robot_framework"
    risk_level: Literal["low", "medium", "high"] = "low"
    description: str


APPROVED_ROBOT_KEYWORDS: tuple[RobotKeywordCapability, ...] = (
    RobotKeywordCapability(
        name="Load Sanitized Trace",
        library=TELECOM_TRACE_LIBRARY,
        domain="telecom_trace",
        args=("fixture_path",),
        description="Loads a sanitized local trace fixture from the fixtures tree.",
    ),
    RobotKeywordCapability(
        name="Verify SIP Header Present",
        library=TELECOM_TRACE_LIBRARY,
        domain="telecom_trace",
        args=("message", "header"),
        description="Validates that a SIP message contains an expected header.",
    ),
    RobotKeywordCapability(
        name="Verify Trace Event Present",
        library=TELECOM_TRACE_LIBRARY,
        domain="telecom_trace",
        args=("protocol", "message"),
        description="Validates that a protocol/message event exists in a sanitized trace.",
    ),
    RobotKeywordCapability(
        name="Verify Trace Route",
        library=TELECOM_TRACE_LIBRARY,
        domain="telecom_trace",
        args=("protocol", "message", "source", "target"),
        description="Validates sanitized source and target placeholders for a trace event.",
    ),
    RobotKeywordCapability(
        name="Verify Minimum Event Count",
        library=TELECOM_TRACE_LIBRARY,
        domain="telecom_trace",
        args=("protocol", "minimum_count"),
        description="Validates a minimum number of sanitized events for a protocol.",
    ),
    RobotKeywordCapability(
        name="Verify Diameter Session Match",
        library=TELECOM_TRACE_LIBRARY,
        domain="telecom_trace",
        args=("request_message", "answer_message"),
        description=(
            "Validates matching Diameter Session-Id values for a "
            "request/answer pair."
        ),
    ),
    RobotKeywordCapability(
        name="Verify Diameter Result Code",
        library=TELECOM_TRACE_LIBRARY,
        domain="telecom_trace",
        args=("message", "result_code"),
        description="Validates an expected Diameter result code on a sanitized answer.",
    ),
    RobotKeywordCapability(
        name="Verify Flexible Sequence",
        library=TELECOM_TRACE_LIBRARY,
        domain="telecom_trace",
        args=("template_name",),
        description=(
            "Validates an approved event sequence while honoring configured "
            "flexible-order groups."
        ),
    ),
)


def list_robot_keyword_capabilities(
    *, domain: str | None = None, include_corpus: bool = False
) -> list[RobotKeywordCapability]:
    capabilities = [
        *APPROVED_ROBOT_KEYWORDS,
        *(_load_corpus_keyword_capabilities() if include_corpus else []),
    ]
    if domain is None:
        return capabilities
    normalized_domain = domain.strip().lower()
    return [
        capability
        for capability in capabilities
        if capability.domain == normalized_domain
    ]


def get_robot_keyword_capability(name: str) -> RobotKeywordCapability:
    normalized_name = name.strip().lower()
    for capability in list_robot_keyword_capabilities(include_corpus=True):
        if capability.name.lower() == normalized_name:
            return capability
    raise KeyError(f"Robot keyword capability is not approved: {name}")


def _load_corpus_keyword_capabilities() -> list[RobotKeywordCapability]:
    registry = load_robot_keyword_registry()
    raw_keywords = registry.get("keywords", [])
    if not isinstance(raw_keywords, list):
        return []

    capabilities: list[RobotKeywordCapability] = []
    seen = {capability.name.lower() for capability in APPROVED_ROBOT_KEYWORDS}
    for item in raw_keywords:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name or name.lower() in seen:
            continue
        args = item.get("args", [])
        domain = str(item.get("domain", "generic") or "generic")
        description = str(item.get("documentation", "") or "Sanitized project keyword from reference corpus.")
        risk_level = str(item.get("risk_level", "low") or "low")
        if risk_level not in {"low", "medium", "high"}:
            risk_level = "low"
        try:
            capability = RobotKeywordCapability(
                name=name,
                library=str(item.get("library", "sanitized_reference_corpus") or "sanitized_reference_corpus"),
                domain=domain,
                args=tuple(str(arg) for arg in args if isinstance(arg, str)),
                risk_level=risk_level,
                description=description[:500],
            )
        except Exception:
            continue
        capabilities.append(capability)
        seen.add(name.lower())
    return capabilities
