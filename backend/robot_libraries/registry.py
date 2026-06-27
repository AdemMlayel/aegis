from __future__ import annotations

from typing import Literal

from pydantic import Field

from backend.graph.state import StrictModel


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
    *, domain: str | None = None
) -> list[RobotKeywordCapability]:
    if domain is None:
        return list(APPROVED_ROBOT_KEYWORDS)
    normalized_domain = domain.strip().lower()
    return [
        capability
        for capability in APPROVED_ROBOT_KEYWORDS
        if capability.domain == normalized_domain
    ]


def get_robot_keyword_capability(name: str) -> RobotKeywordCapability:
    normalized_name = name.strip().lower()
    for capability in APPROVED_ROBOT_KEYWORDS:
        if capability.name.lower() == normalized_name:
            return capability
    raise KeyError(f"Robot keyword capability is not approved: {name}")
