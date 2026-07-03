from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field

from backend.graph.state import (
    StrictModel,
    TicketData,
    TicketInputDatum,
    TicketServiceInteraction,
    TicketSource,
    TicketTechnicalDetails,
    TicketTestStep,
    TicketValidationRule,
    utc_now,
)
from backend.storage.mock_tickets import create_mock_ticket, get_mock_ticket_record
from backend.tickets.schema import StructuredTicketRecord


MAX_INTAKE_CHARS = 100_000
SUPPORTED_TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".conf",
    ".csv",
    ".html",
    ".ini",
    ".json",
    ".md",
    ".properties",
    ".robot",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

SENSITIVE_ASSIGNMENT_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?i)\b((?:api\s*)?token|password|passwd|pwd|secret|credential|authorization|bearer)"
            r"(\s*[:=]\s*)([^\s,#)]+)"
        ),
        r"\1\2VALUE_PLACEHOLDER",
    ),
    (
        re.compile(
            r"(?i)\b([A-Za-z_][A-Za-z0-9_]*(?:password|passwd|pwd|secret|token|"
            r"api[_-]?key|apikey|credential|authorization|bearer)[A-Za-z0-9_]*"
            r"\s*[:=]\s*)(['\"])(.*?)(\2)"
        ),
        r"\1\2VALUE_PLACEHOLDER\4",
    ),
    (
        re.compile(
            r"(?i)\b([A-Za-z_][A-Za-z0-9_]*(?:password|passwd|pwd|secret|token|"
            r"api[_-]?key|apikey|credential|authorization|bearer)[A-Za-z0-9_]*"
            r"\s*[:=]\s*)([^\s,#)]+)"
        ),
        r"\1VALUE_PLACEHOLDER",
    ),
)

REDACTION_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        "PRIVATE_KEY_PLACEHOLDER",
    ),
    (re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE), "URL_PLACEHOLDER"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"), "IP_ADDRESS_PLACEHOLDER"),
    (
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        "EMAIL_PLACEHOLDER",
    ),
    (re.compile(r"\b[A-Za-z]:\\[^\s'\"<>]+"), "LOCAL_PATH_PLACEHOLDER"),
    (re.compile(r"(?<![:\w])/[\w.-]+(?:/[\w.-]+)+"), "LOCAL_PATH_PLACEHOLDER"),
    (
        re.compile(r"\b(?:github_pat|ghp)_[A-Za-z0-9_]+\b", re.IGNORECASE),
        "TOKEN_PLACEHOLDER",
    ),
    (
        re.compile(r"\bsk(?:-proj)?-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE),
        "API_KEY_PLACEHOLDER",
    ),
    (
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}\b"),
        "Bearer TOKEN_PLACEHOLDER",
    ),
    (re.compile(r"\b[0-9a-fA-F]{16,}\b"), "HEX_IDENTIFIER_PLACEHOLDER"),
    (re.compile(r"\b\d{7,}\b"), "NUMERIC_IDENTIFIER_PLACEHOLDER"),
    (
        re.compile(r"\b[A-Za-z0-9][A-Za-z0-9-]{2,}(?:\.[A-Za-z0-9-]{2,}){1,}\b"),
        "HOSTNAME_PLACEHOLDER",
    ),
)

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "ticket_id": ("ticket id", "id"),
    "title": ("title", "summary"),
    "description": ("description", "overview", "scenario"),
    "business_objective": ("business objective", "business goal"),
    "test_objective": ("test objective", "test goal", "objective"),
    "system_under_test": ("system under test", "sut"),
    "feature_or_service_name": ("feature", "service", "feature or service"),
    "test_scope": ("test scope", "scope", "in scope"),
    "out_of_scope": ("out of scope", "out-of-scope"),
    "preconditions": ("preconditions", "precondition", "prerequisites"),
    "assumptions": ("assumptions", "assumption"),
    "environment": ("environment", "test environment"),
    "interfaces_involved": ("interfaces involved", "interfaces", "interface"),
    "input_data": ("input data", "test data", "payload"),
    "expected_outputs": ("expected outputs", "expected output", "expected results", "expected result"),
    "validation_rules": ("validation rules", "validation", "assertions"),
    "test_steps": ("test steps", "steps", "procedure", "manual steps"),
    "acceptance_criteria": ("acceptance criteria", "acceptance"),
    "risks_or_constraints": ("risks", "constraints", "risks or constraints"),
    "dependencies": ("dependencies", "dependency"),
    "required_tools": ("required tools", "tools", "automation tools"),
    "architecture_summary": ("architecture summary", "architecture"),
    "components_involved": ("components involved", "components"),
    "data_flow": ("data flow", "flow"),
    "api_or_service_interactions": ("api interactions", "service interactions", "api or service interactions"),
    "configuration_requirements": ("configuration requirements", "configuration", "config"),
    "security_constraints": ("security constraints", "security"),
    "logging_requirements": ("logging requirements", "logging"),
    "monitoring_requirements": ("monitoring requirements", "monitoring"),
    "error_handling_expectations": ("error handling expectations", "error handling"),
    "test_data_requirements": ("test data requirements", "test data requirements"),
}

ALL_SECTION_HEADINGS = {
    re.sub(r"[^a-z0-9]+", " ", alias.casefold()).strip()
    for aliases in SECTION_ALIASES.values()
    for alias in aliases
}

TOOL_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Robot Framework", ("robot", "keyword", ".robot")),
    ("Appium", ("appium", "android", "ios", "mobile", "device")),
    ("Wireshark", ("wireshark", "pcap", "packet", "trace")),
    ("REST API client", ("api", "rest", "http", "endpoint", "request", "response")),
    ("Selenium", ("selenium", "browser", "web ui", "click")),
    ("Database client", ("database", "db", "sql", "record", "table")),
    ("Log parser", ("log", "logging", "event", "monitoring")),
)

HARD_BLOCKER_PHRASES = (
    "cannot be automated",
    "not automatable",
    "manual only",
    "requires human judgement",
    "requires human judgment",
    "subjective assessment",
    "visual inspection only",
    "exploratory testing only",
)


class AutomationFeasibility(StrictModel):
    automatable: bool
    readiness: Literal["ready", "needs_clarification", "not_automatable"]
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_tools: list[str] = Field(default_factory=list)
    detected_domains: list[str] = Field(default_factory=list)


class TicketIntakeResult(StrictModel):
    ticket: StructuredTicketRecord
    assessment: AutomationFeasibility
    sanitized_excerpt: str
    redaction_count: int = 0


class SanitizedText(StrictModel):
    text: str
    redaction_count: int = 0


def intake_ticket_from_chat(
    *,
    actor: str,
    session_id: str,
    description: str | None = None,
    file_name: str | None = None,
    file_content: str | None = None,
) -> TicketIntakeResult:
    raw_text = _combine_intake_text(description=description, file_content=file_content)
    _validate_file_name(file_name)
    sanitized = sanitize_user_text(raw_text)
    if not sanitized.text.strip():
        raise ValueError("Ticket intake content is empty after sanitization")

    ticket = _ticket_from_text(
        sanitized.text,
        actor=actor,
        session_id=session_id,
        file_name=file_name,
    )
    assessment = assess_automation_feasibility(ticket=ticket, source_text=sanitized.text)
    status = "ready" if assessment.automatable else "blocked"
    persisted = _persist_unique_ticket(ticket.model_copy(update={"status": status}))
    return TicketIntakeResult(
        ticket=persisted,
        assessment=assessment,
        sanitized_excerpt=_safe_excerpt(sanitized.text, 600),
        redaction_count=sanitized.redaction_count,
    )


def sanitize_user_text(value: str) -> SanitizedText:
    text = value[:MAX_INTAKE_CHARS]
    total = 0
    for pattern, replacement in SENSITIVE_ASSIGNMENT_RULES:
        text, count = pattern.subn(replacement, text)
        total += count
    for pattern, replacement in REDACTION_RULES:
        text, count = pattern.subn(replacement, text)
        total += count
    text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    return SanitizedText(text=text, redaction_count=total)


def assess_automation_feasibility(
    *,
    ticket: TicketData,
    source_text: str,
) -> AutomationFeasibility:
    lowered = source_text.casefold()
    reasons: list[str] = []
    blockers: list[str] = []
    missing: list[str] = []
    score = 0.0

    if ticket.test_steps:
        score += 0.24
        reasons.append("Explicit test steps are available.")
    else:
        missing.append("clear ordered test steps")

    if ticket.expected_outputs or ticket.acceptance_criteria:
        score += 0.2
        reasons.append("Observable expected outputs or acceptance criteria are present.")
    else:
        missing.append("expected outputs or acceptance criteria")

    if ticket.validation_rules:
        score += 0.14
        reasons.append("Validation rules/assertions are present.")
    else:
        missing.append("validation rules/assertions")

    if ticket.input_data or "fixture" in lowered or "payload" in lowered:
        score += 0.1
        reasons.append("Input or fixture data is described.")
    else:
        missing.append("input/test data")

    if ticket.interfaces_involved or ticket.technical.api_or_service_interactions:
        score += 0.1
        reasons.append("Interfaces or service interactions are identified.")

    recommended_tools = _detect_tools(source_text)
    if recommended_tools:
        score += 0.12
        reasons.append("Automation/tooling signals were detected.")
    else:
        missing.append("required automation tools or interface type")

    if ticket.preconditions:
        score += 0.06
        reasons.append("Preconditions are described.")
    else:
        missing.append("preconditions")

    if ticket.test_objective or ticket.business_objective:
        score += 0.04
        reasons.append("The test objective is stated.")

    for phrase in HARD_BLOCKER_PHRASES:
        if phrase in lowered:
            blockers.append(f"Scenario states `{phrase}`.")

    if "captcha" in lowered or "one-time password" in lowered or "otp" in lowered:
        blockers.append("Contains interactive anti-automation or one-time verification flow.")
    if "production only" in lowered:
        blockers.append("Scenario appears to require a production-only environment.")

    confidence = max(0.05, min(score, 0.98))
    automatable = confidence >= 0.55 and not blockers
    if automatable:
        readiness: Literal["ready", "needs_clarification", "not_automatable"] = "ready"
    elif blockers:
        readiness = "not_automatable"
    else:
        readiness = "needs_clarification"

    if not recommended_tools and automatable:
        recommended_tools = ["Robot Framework"]

    return AutomationFeasibility(
        automatable=automatable,
        readiness=readiness,
        confidence=round(confidence, 2),
        reasons=reasons,
        blockers=blockers,
        missing_information=missing[:8],
        recommended_tools=recommended_tools,
        detected_domains=_detect_domains(source_text),
    )


def _ticket_from_text(
    text: str,
    *,
    actor: str,
    session_id: str,
    file_name: str | None,
) -> StructuredTicketRecord:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8].upper()
    today = utc_now().date().isoformat()
    source_label = Path(file_name).suffix.lower() if file_name else "description"
    title = _first_scalar(text, "title") or _title_from_text(text)
    description = _first_scalar(text, "description") or _first_paragraph(text)
    test_steps = _extract_steps(text)
    expected_outputs = _list_section(text, "expected_outputs")
    acceptance_criteria = _list_section(text, "acceptance_criteria") or expected_outputs[:]
    validation_rules = _validation_rules_from_text(text, expected_outputs, acceptance_criteria)
    input_data = _input_data_from_text(text)
    required_tools = _merge_unique([
        *_list_section(text, "required_tools"),
        *_detect_tools(text),
    ])
    interfaces = _list_section(text, "interfaces_involved")
    technical = _technical_details_from_text(text)

    return StructuredTicketRecord(
        id=_generated_ticket_id(text, digest),
        title=title,
        description=description,
        business_objective=_first_scalar(text, "business_objective")
        or "Translate the uploaded manual scenario into governed QA automation.",
        test_objective=_first_scalar(text, "test_objective") or title,
        system_under_test=_first_scalar(text, "system_under_test") or "SYSTEM_UNDER_TEST_PLACEHOLDER",
        feature_or_service_name=_first_scalar(text, "feature_or_service_name") or "FEATURE_OR_SERVICE_PLACEHOLDER",
        test_scope=_list_section(text, "test_scope") or [title],
        out_of_scope=_list_section(text, "out_of_scope"),
        preconditions=_list_section(text, "preconditions"),
        assumptions=_list_section(text, "assumptions")
        or ["Uploaded content was sanitized before ticket creation."],
        environment=_first_scalar(text, "environment") or "TEST_ENVIRONMENT",
        interfaces_involved=interfaces or _infer_interfaces(text),
        input_data=input_data,
        expected_outputs=expected_outputs or acceptance_criteria,
        validation_rules=validation_rules,
        test_steps=test_steps,
        acceptance_criteria=acceptance_criteria,
        risks_or_constraints=_list_section(text, "risks_or_constraints"),
        dependencies=_list_section(text, "dependencies"),
        required_tools=required_tools,
        priority=_priority_from_text(text),
        status="ready",
        created_date=today,
        last_updated_date=today,
        labels=_merge_unique(["chat-intake", "uploaded-scenario", source_label.lstrip(".")]),
        assignee=actor,
        source=TicketSource.DEMO,
        raw_url=f"chat://sessions/{session_id}/ticket-intake/{digest}",
        technical=technical,
    )


def _technical_details_from_text(text: str) -> TicketTechnicalDetails:
    interactions = [
        TicketServiceInteraction(
            name=f"interaction_{index}",
            source="ACTOR_PLACEHOLDER",
            target="INTERNAL_SERVICE_PLACEHOLDER",
            protocol=_protocol_hint(item),
            operation=item,
            expected_result="Expected interaction result is validated by generated assertions.",
        )
        for index, item in enumerate(_list_section(text, "api_or_service_interactions"), start=1)
    ]
    return TicketTechnicalDetails(
        architecture_summary=_first_scalar(text, "architecture_summary") or "",
        components_involved=_list_section(text, "components_involved"),
        data_flow=_list_section(text, "data_flow"),
        api_or_service_interactions=interactions,
        configuration_requirements=_list_section(text, "configuration_requirements"),
        security_constraints=_list_section(text, "security_constraints"),
        logging_requirements=_list_section(text, "logging_requirements"),
        monitoring_requirements=_list_section(text, "monitoring_requirements"),
        error_handling_expectations=_list_section(text, "error_handling_expectations"),
        test_data_requirements=_list_section(text, "test_data_requirements"),
    )


def _generated_ticket_id(text: str, digest: str) -> str:
    explicit = _first_scalar(text, "ticket_id")
    if explicit:
        cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", explicit).strip("-").upper()
        if cleaned:
            return cleaned[:48]
    return f"CHAT-UPLOAD-{digest}"


def _persist_unique_ticket(ticket: StructuredTicketRecord) -> StructuredTicketRecord:
    if get_mock_ticket_record(ticket.id) is None:
        return create_mock_ticket(ticket)
    for index in range(2, 100):
        candidate = ticket.model_copy(update={"id": f"{ticket.id}-{index}"})
        if get_mock_ticket_record(candidate.id) is None:
            return create_mock_ticket(candidate)
    raise ValueError("Could not allocate a unique uploaded ticket ID")


def _combine_intake_text(*, description: str | None, file_content: str | None) -> str:
    chunks = [item.strip() for item in (description, file_content) if item and item.strip()]
    if not chunks:
        raise ValueError("Provide a description or a supported text file")
    combined = "\n\n".join(chunks)
    if len(combined) > MAX_INTAKE_CHARS:
        combined = combined[:MAX_INTAKE_CHARS]
    return combined


def _validate_file_name(file_name: str | None) -> None:
    if not file_name:
        return
    suffix = Path(file_name).suffix.lower()
    if suffix not in SUPPORTED_TEXT_SUFFIXES:
        raise ValueError(
            "Unsupported upload type. Use a text-like scenario file such as .txt, .md, .robot, .json, .xml, .html, .csv, .yaml or .yml."
        )


def _first_scalar(text: str, field_name: str) -> str:
    aliases = SECTION_ALIASES.get(field_name, ())
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for alias in aliases:
            match = re.match(rf"(?i)^\s*{re.escape(alias)}\s*[:\-]\s*(.+)$", stripped)
            if match:
                return _clean_item(match.group(1))[:500]
    items = _list_section(text, field_name)
    return items[0] if items else ""


def _list_section(text: str, field_name: str) -> list[str]:
    aliases = SECTION_ALIASES.get(field_name, ())
    lines = text.splitlines()
    collected: list[str] = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_section and collected:
                break
            continue
        heading, inline = _heading_for_line(stripped)
        if heading:
            if in_section:
                break
            if heading in {_normalize_heading(alias) for alias in aliases}:
                in_section = True
                if inline:
                    collected.extend(_split_items(inline))
                continue
        elif in_section:
            collected.extend(_split_items(stripped))
    return _merge_unique([item for item in collected if item])


def _extract_steps(text: str) -> list[TicketTestStep]:
    raw_steps = _list_section(text, "test_steps")
    if not raw_steps:
        raw_steps = [
            _clean_item(match.group(1))
            for line in text.splitlines()
            if (match := re.match(r"^\s*(?:step\s*)?\d+[\.)]\s+(.+)$", line, re.IGNORECASE))
        ]
    expected = _list_section(text, "expected_outputs")
    steps: list[TicketTestStep] = []
    for index, item in enumerate(raw_steps[:30], start=1):
        steps.append(
            TicketTestStep(
                order=index,
                action=item,
                expected_result=expected[min(index - 1, len(expected) - 1)]
                if expected
                else "Observed result matches the ticket acceptance criteria.",
            )
        )
    return steps


def _validation_rules_from_text(
    text: str,
    expected_outputs: list[str],
    acceptance_criteria: list[str],
) -> list[TicketValidationRule]:
    rules = _list_section(text, "validation_rules")
    if not rules:
        rules = [*expected_outputs[:3], *acceptance_criteria[:3]]
    return [
        TicketValidationRule(
            id=f"VR-{index:03d}",
            description=item,
            severity="high" if _contains_any(item, ("must", "shall", "critical")) else "info",
        )
        for index, item in enumerate(_merge_unique(rules)[:12], start=1)
    ]


def _input_data_from_text(text: str) -> list[TicketInputDatum]:
    items = _list_section(text, "input_data")
    data: list[TicketInputDatum] = []
    for index, item in enumerate(items[:20], start=1):
        name, separator, value = item.partition(":")
        data.append(
            TicketInputDatum(
                name=_safe_name(name) if separator else f"input_{index}",
                value=value.strip() if separator and value.strip() else "VALUE_PLACEHOLDER",
                description=item if not separator else "",
            )
        )
    return data


def _heading_for_line(line: str) -> tuple[str | None, str]:
    match = re.match(r"^\s*(?:#+\s*)?([A-Za-z][A-Za-z0-9 /_-]{1,80})\s*[:\-]\s*(.*)$", line)
    if match:
        heading = _normalize_heading(match.group(1))
        if heading in ALL_SECTION_HEADINGS:
            return heading, match.group(2).strip()
    heading = _normalize_heading(line.strip("*# "))
    if heading in ALL_SECTION_HEADINGS:
        return heading, ""
    return None, ""


def _split_items(value: str) -> list[str]:
    stripped = _clean_item(value)
    if not stripped:
        return []
    if ";" in stripped:
        return [_clean_item(item) for item in stripped.split(";") if _clean_item(item)]
    return [stripped]


def _clean_item(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^\s*(?:[-*]|\d+[\.)])\s*", "", value)).strip()


def _normalize_heading(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _title_from_text(text: str) -> str:
    for line in text.splitlines():
        cleaned = _clean_item(line)
        if cleaned and not _heading_for_line(cleaned)[0]:
            return cleaned[:120]
    return "Uploaded test scenario"


def _first_paragraph(text: str) -> str:
    paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    if not paragraphs:
        return "Uploaded test scenario."
    return re.sub(r"\s+", " ", paragraphs[0])[:2000]


def _priority_from_text(text: str) -> Literal["low", "medium", "high", "critical"]:
    lowered = text.casefold()
    if "critical" in lowered or "p0" in lowered:
        return "critical"
    if "high" in lowered or "p1" in lowered:
        return "high"
    if "low" in lowered or "p3" in lowered:
        return "low"
    return "medium"


def _detect_tools(text: str) -> list[str]:
    lowered = text.casefold()
    return [
        tool
        for tool, hints in TOOL_HINTS
        if any(hint in lowered for hint in hints)
    ]


def _detect_domains(text: str) -> list[str]:
    lowered = text.casefold()
    domains: Counter[str] = Counter()
    mapping = {
        "api": ("api", "rest", "endpoint", "request", "response"),
        "mobile": ("mobile", "appium", "android", "ios", "device"),
        "telecom_trace": ("sip", "diameter", "ims", "pcap", "wireshark", "trace"),
        "ui": ("browser", "selenium", "web ui", "click"),
        "data": ("database", "sql", "record", "table"),
        "logs_monitoring": ("log", "monitor", "metric", "event"),
    }
    for domain, hints in mapping.items():
        if any(hint in lowered for hint in hints):
            domains[domain] += 1
    return list(domains) or ["generic"]


def _infer_interfaces(text: str) -> list[str]:
    lowered = text.casefold()
    interfaces: list[str] = []
    if any(term in lowered for term in ("api", "endpoint", "rest", "http")):
        interfaces.append("INTERNAL_API_ENDPOINT")
    if any(term in lowered for term in ("mobile", "appium", "device")):
        interfaces.append("MOBILE_DEVICE_INTERFACE")
    if any(term in lowered for term in ("pcap", "packet", "trace", "wireshark")):
        interfaces.append("TRACE_ANALYSIS_INTERFACE")
    if any(term in lowered for term in ("database", "db", "sql")):
        interfaces.append("DATABASE_REFERENCE")
    return interfaces


def _protocol_hint(value: str) -> str:
    lowered = value.casefold()
    if "sip" in lowered:
        return "SIP"
    if "diameter" in lowered:
        return "Diameter"
    if "http" in lowered or "api" in lowered:
        return "HTTPS"
    return "PROTOCOL_PLACEHOLDER"


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    lowered = value.casefold()
    return any(needle in lowered for needle in needles)


def _merge_unique(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _clean_item(value)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(cleaned)
    return output


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip()).strip("_").lower()
    return cleaned or "input"


def _safe_excerpt(text: str, limit: int) -> str:
    return re.sub(r"\s+", " ", text.strip())[:limit]
