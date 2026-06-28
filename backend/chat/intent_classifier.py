from __future__ import annotations

import re

from pydantic import Field

from backend.chat.schemas import ChatIntent
from backend.graph.state import StrictModel


class ClassifiedIntent(StrictModel):
    intent: ChatIntent
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    ticket_id: str | None = None
    context_id: str | None = None
    normalized_message: str


def classify_chat_intent(message: str) -> ClassifiedIntent:
    normalized = " ".join(message.strip().lower().split())
    ticket_id = _extract_ticket_id(message)
    context_id = _extract_context_id(message)

    if not normalized:
        return ClassifiedIntent(intent="unknown", confidence=0.0, normalized_message=normalized)

    if _contains_any(normalized, ["help", "what can you do", "how can you help"]):
        intent: ChatIntent = "help"
        confidence = 0.95
    elif _contains_any(normalized, ["mocked", "mock", "real", "provider", "providers", "configured", "system status", "active mode"]):
        intent = "system_question"
        confidence = 0.82
    elif _contains_any(normalized, ["analyze", "analyse", "start", "begin workflow", "run workflow", "create workflow"]):
        intent = "workflow_start"
        confidence = 0.88
    elif _contains_any(normalized, ["next step", "continue", "resume", "run next", "run next stage"]):
        intent = "workflow_step"
        confidence = 0.82
    elif _contains_any(normalized, ["where are we", "workflow status", "current status", "progress", "next stage", "completed stages"]):
        intent = "workflow_status"
        confidence = 0.86
    elif _contains_any(normalized, ["approve", "approval"]):
        intent = "approval_request"
        confidence = 0.82
    elif _contains_any(normalized, ["execute", "run tests", "run the tests", "execution"]):
        intent = "execution_request"
        confidence = 0.86
    elif _contains_any(normalized, ["robot", "artifact", "generated file", "automation file", "keyword", "keywords"]):
        intent = "artifact_question"
        confidence = 0.78
    elif _contains_any(normalized, ["validation", "validate", "dry run", "why did validation"]):
        intent = "validation_question"
        confidence = 0.82
    elif _contains_any(normalized, ["why did it fail", "failure", "failed", "investigate", "root cause", "evidence"]):
        intent = "investigation_question"
        confidence = 0.80
    elif _contains_any(normalized, ["report", "summary", "pm summary", "executive summary"]):
        intent = "report_request"
        confidence = 0.82
    elif _contains_any(normalized, ["ticket", "requirement", "missing", "acceptance", "criteria", "risk"]):
        intent = "ticket_question"
        confidence = 0.76
    elif _contains_any(normalized, ["knowledge", "rag", "memory", "corpus", "sanitized"]):
        intent = "knowledge_question"
        confidence = 0.74
    else:
        intent = "unknown"
        confidence = 0.40

    return ClassifiedIntent(
        intent=intent,
        confidence=confidence,
        ticket_id=ticket_id,
        context_id=context_id,
        normalized_message=normalized,
    )


def _contains_any(value: str, needles: list[str]) -> bool:
    return any(needle in value for needle in needles)


def _extract_ticket_id(message: str) -> str | None:
    match = re.search(r"\b[A-Z][A-Z0-9]+-[A-Z0-9-]+-\d+\b|\b[A-Z]{2,}-\d+\b", message)
    return match.group(0) if match else None


def _extract_context_id(message: str) -> str | None:
    match = re.search(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        message,
        flags=re.IGNORECASE,
    )
    return match.group(0) if match else None
