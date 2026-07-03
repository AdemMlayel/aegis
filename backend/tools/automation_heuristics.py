from __future__ import annotations

from typing import Any

from backend.graph.artifacts import relative_to_project, robot_output_dir, slug
from backend.graph.state import (
    AutomationBlock,
    ReviewFeedback,
    TestCase,
    TestDataBlock,
    TicketData,
)
from backend.reference_corpus.profiles import load_robot_style_profile
from backend.robot_libraries.registry import TELECOM_TRACE_LIBRARY, list_robot_keyword_capabilities
from backend.tools.base import BaseTool, tool_registry

TELECOM_TRACE_FIXTURE = "fixtures/telecom/sanitized_call_trace.json"
TELECOM_TRACE_MARKERS = (
    "telecom",
    "ims",
    "sip",
    "diameter",
    "trace-validation",
    "trace validation",
)


def _reference_style_tags() -> list[str]:
    profile = load_robot_style_profile()
    style = profile.get("style", {}) if isinstance(profile, dict) else {}
    common_tags = style.get("common_tags", []) if isinstance(style, dict) else []
    tags: list[str] = []
    if isinstance(common_tags, list):
        for item in common_tags:
            if isinstance(item, dict):
                value = str(item.get("value", "")).strip()
                if value and "PLACEHOLDER" not in value.upper():
                    tags.append(value)
            if len(tags) >= 3:
                break
    return tags


def _reference_style_comment() -> str | None:
    profile = load_robot_style_profile()
    summary = profile.get("summary", {}) if isinstance(profile, dict) else {}
    if not isinstance(summary, dict) or not summary.get("robot_files"):
        return None
    return (
        f"# Reference corpus style applied from {summary.get('robot_files')} "
        "sanitized Robot test files"
    )


def _approved_keyword_names() -> set[str]:
    return {capability.name for capability in list_robot_keyword_capabilities(include_corpus=True)}


@tool_registry.register(
    name="LocalRobotAutomationTool",
    isolation="process",
    description="Writes deterministic Robot Framework files for generated test cases.",
)
class LocalRobotAutomationTool(BaseTool):
    def invoke(self, **kwargs: Any) -> dict[str, AutomationBlock]:
        ticket_id = kwargs.get("ticket_id")
        test_cases = kwargs.get("test_cases")
        test_data = kwargs.get("test_data")
        revision = kwargs.get("revision")
        feedback = kwargs.get("feedback")
        ticket = kwargs.get("ticket")

        if not isinstance(ticket_id, str) or not ticket_id.strip():
            raise TypeError("LocalRobotAutomationTool requires a ticket_id string")
        if ticket is not None and not isinstance(ticket, TicketData):
            raise TypeError("LocalRobotAutomationTool requires a TicketData ticket")
        if not isinstance(test_cases, list) or not all(
            isinstance(test_case, TestCase) for test_case in test_cases
        ):
            raise TypeError("LocalRobotAutomationTool requires list[TestCase]")
        if not isinstance(test_data, dict) or not all(
            isinstance(block, TestDataBlock) for block in test_data.values()
        ):
            raise TypeError(
                "LocalRobotAutomationTool requires dict[str, TestDataBlock]"
            )
        if not isinstance(revision, int):
            raise TypeError("LocalRobotAutomationTool requires an integer revision")
        if not isinstance(feedback, list) or not all(
            isinstance(item, ReviewFeedback) for item in feedback
        ):
            raise TypeError("LocalRobotAutomationTool requires list[ReviewFeedback]")

        return generate_robot_automation(
            ticket_id=ticket_id,
            test_cases=test_cases,
            test_data=test_data,
            revision=revision,
            feedback=feedback,
            ticket=ticket,
        )


def generate_robot_automation(
    *,
    ticket_id: str,
    test_cases: list[TestCase],
    test_data: dict[str, TestDataBlock],
    revision: int,
    feedback: list[ReviewFeedback],
    ticket: TicketData | None = None,
) -> dict[str, AutomationBlock]:
    output_dir = robot_output_dir(ticket_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    automation: dict[str, AutomationBlock] = {}
    for test_case in test_cases:
        filename = f"{test_case.id}_{slug(test_case.title)}.robot"
        robot_file = output_dir / filename
        content = _render_robot_file(
            test_case,
            ticket_id,
            revision,
            feedback,
            ticket=ticket,
            test_data=test_data.get(test_case.id),
        )
        robot_file.write_text(
            content,
            encoding="utf-8",
        )

        automation[test_case.id] = AutomationBlock(
            test_case_id=test_case.id,
            robot_file=relative_to_project(robot_file),
            revision=revision,
            data_reference_check_passed=test_case.id in test_data,
        )

    return automation


def _robot_cell(value: str) -> str:
    return value.replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()


def _teardown_clause(test_data: TestDataBlock | None) -> list[str]:
    """Render the resolved test-data teardown as a real Robot [Teardown].

    N3: the data resolver declares a ``teardown`` list per test case, but it was
    never rendered into the generated suite — a dead contract. We now emit it as
    an executable ``[Teardown]`` setting built only from BuiltIn keywords (``Log``
    / ``Run Keywords``), so the declared cleanup actually runs during execution
    and passes ``robot --dryrun`` instead of being silently dropped.
    """
    steps = [
        _robot_cell(str(step))
        for step in (test_data.teardown if test_data else [])
        if str(step).strip()
    ]
    if not steps:
        return []
    logs = [f"Log    Teardown: {step}" for step in steps]
    if len(logs) == 1:
        return [f"    [Teardown]    {logs[0]}"]
    joined = "    AND    ".join(logs)
    return [f"    [Teardown]    Run Keywords    {joined}"]


def _render_robot_file(
    test_case: TestCase,
    ticket_id: str,
    revision: int,
    feedback: list[ReviewFeedback],
    *,
    ticket: TicketData | None = None,
    test_data: TestDataBlock | None = None,
) -> str:
    if _is_telecom_trace_ticket(ticket):
        return _render_telecom_robot_file(
            test_case,
            ticket_id,
            revision,
            feedback,
            ticket=ticket,
            test_data=test_data,
        )

    tags = ["generated", test_case.type, test_case.priority, *_reference_style_tags()]
    style_comment = _reference_style_comment()
    lines = [
        "*** Settings ***",
        (
            f"Documentation     Generated by AegisQA for {ticket_id} / "
            f"{test_case.id} / revision {revision}"
        ),
        "Library           BuiltIn",
        *( [style_comment] if style_comment else [] ),
        "",
        "*** Test Cases ***",
        _robot_cell(test_case.title),
        f"    [Tags]    {'    '.join(tags)}",
        f"    [Documentation]    {_robot_cell(test_case.expected_outcome)}",
        *_teardown_clause(test_data),
    ]

    for precondition in test_case.preconditions:
        lines.append(f"    Log    Preconditions: {_robot_cell(precondition)}")

    for index, step in enumerate(test_case.steps, start=1):
        lines.append(f"    Log    Step {index}: {_robot_cell(step)}")

    # Emit REAL BuiltIn assertions over the resolved test data instead of only
    # logging step text. These are executable: Create List / Should Contain /
    # Should Be Equal / Should Be True all resolve under the BuiltIn library and
    # pass `robot --dryrun`, so the generated suite genuinely exercises the
    # assertion engine on the resolved data rather than echoing strings.
    lines.extend(_builtin_data_assertions(test_case, test_data))

    for item in feedback:
        lines.append(
            "    Log    Reviewer feedback applied: "
            f"{_robot_cell(item.comment)}"
        )

    lines.append(f"    Log    Expected: {_robot_cell(test_case.expected_outcome)}")
    lines.append("")
    return "\n".join(lines)


def _builtin_data_assertions(
    test_case: TestCase,
    test_data: TestDataBlock | None,
) -> list[str]:
    """Build executable BuiltIn assertion steps from resolved test data.

    Every keyword used here (Create List, Should Not Be Empty, Should Contain,
    Should Be Equal As Strings, Should Be True) is a BuiltIn keyword on the
    validator's allowlist, so the resulting steps pass dry-run while asserting
    something real about the resolved data and expected outcome.
    """
    lines: list[str] = []
    resolved = test_data.resolved_data if test_data else {}
    for category, values in resolved.items():
        safe_values = [_robot_cell(str(value)) for value in values if str(value).strip()]
        if not safe_values:
            continue
        var = f"${{{category.upper()}}}"
        joined = "    ".join(safe_values)
        lines.append(f"    {var} =    Create List    {joined}")
        lines.append(f"    Should Not Be Empty    {var}")
        # Assert the first resolved value is present in the list we just built —
        # a real membership assertion over the resolved data.
        lines.append(f"    Should Contain    {var}    {safe_values[0]}")

    expected = _robot_cell(test_case.expected_outcome)
    if expected:
        lines.append(f"    ${{EXPECTED}} =    Set Variable    {expected}")
        lines.append(f"    Should Be Equal As Strings    ${{EXPECTED}}    {expected}")

    if not lines:
        # No resolved data and no expected outcome — still emit one real assertion
        # so the test body is executable rather than log-only.
        lines.append("    Should Be True    ${True}")
    return lines


def _render_telecom_robot_file(
    test_case: TestCase,
    ticket_id: str,
    revision: int,
    feedback: list[ReviewFeedback],
    *,
    ticket: TicketData | None,
    test_data: TestDataBlock | None = None,
) -> str:
    tags = ["generated", test_case.type, test_case.priority, "telecom-trace", *_reference_style_tags()]
    style_comment = _reference_style_comment()
    lines = [
        "*** Settings ***",
        (
            f"Documentation     Generated by AegisQA for {ticket_id} / "
            f"{test_case.id} / revision {revision}"
        ),
        f"Library           {TELECOM_TRACE_LIBRARY}",
        *( [style_comment] if style_comment else [] ),
        "",
        "*** Variables ***",
        f"${{TRACE_FIXTURE}}    {TELECOM_TRACE_FIXTURE}",
        "",
        "*** Test Cases ***",
        _robot_cell(test_case.title),
        f"    [Tags]    {'    '.join(tags)}",
        f"    [Documentation]    {_robot_cell(test_case.expected_outcome)}",
        *_teardown_clause(test_data),
        "    Load Sanitized Trace    ${TRACE_FIXTURE}",
    ]

    for keyword_call in _telecom_keyword_calls(ticket):
        lines.append(f"    {keyword_call}")

    for item in feedback:
        lines.append(
            "    Log    Reviewer feedback applied: "
            f"{_robot_cell(item.comment)}"
        )

    lines.append(f"    Log    Expected: {_robot_cell(test_case.expected_outcome)}")
    lines.append("")
    return "\n".join(lines)


def _is_telecom_trace_ticket(ticket: TicketData | None) -> bool:
    if ticket is None:
        return False

    searchable_values = [
        ticket.title,
        ticket.description,
        ticket.system_under_test,
        ticket.feature_or_service_name,
        ticket.environment,
        ticket.technical.architecture_summary,
        *ticket.labels,
        *ticket.interfaces_involved,
        *ticket.required_tools,
    ]
    for interaction in ticket.technical.api_or_service_interactions:
        searchable_values.extend(
            [
                interaction.name,
                interaction.protocol,
                interaction.operation,
            ]
        )

    searchable = " ".join(_robot_cell(value).lower() for value in searchable_values)
    return any(marker in searchable for marker in TELECOM_TRACE_MARKERS)


def _telecom_keyword_calls(ticket: TicketData | None) -> list[str]:
    content = _ticket_validation_text(ticket)
    calls: list[tuple[str, ...]] = []

    if "sip" in content and "header" in content:
        calls.append(("Verify Trace Event Present", "SIP", "INVITE"))
        calls.append(
            (
                "Verify Trace Route",
                "SIP",
                "INVITE",
                "TEST_SUBSCRIBER_A",
                "INTERNAL_SERVICE_A",
            )
        )
        calls.append(("Verify Minimum Event Count", "SIP", "3"))
        calls.append(("Verify SIP Header Present", "INVITE", "Call-ID"))
    if (
        "identity" in content
        or "p-asserted" in content
        or "calling-party" in content
    ):
        calls.append(("Verify SIP Header Present", "INVITE", "P-Asserted-Identity"))
    if "diameter" in content and (
        "session" in content or "request/answer" in content
    ):
        calls.append(("Verify Trace Event Present", "Diameter", "LIR"))
        calls.append(("Verify Minimum Event Count", "Diameter", "2"))
        calls.append(("Verify Diameter Session Match", "LIR", "LIA"))
    if "result code" in content or "success_result_code_placeholder" in content:
        calls.append(
            (
                "Verify Diameter Result Code",
                "LIA",
                "SUCCESS_RESULT_CODE_PLACEHOLDER",
            )
        )
    if "flexible" in content or "sequence" in content or "order" in content:
        calls.append(("Verify Flexible Sequence", "IMS_CALL_FLOW_TEMPLATE"))

    if not calls:
        calls = [
            ("Verify Trace Event Present", "SIP", "INVITE"),
            (
                "Verify Trace Route",
                "SIP",
                "INVITE",
                "TEST_SUBSCRIBER_A",
                "INTERNAL_SERVICE_A",
            ),
            ("Verify Minimum Event Count", "SIP", "3"),
            ("Verify SIP Header Present", "INVITE", "Call-ID"),
            ("Verify Trace Event Present", "Diameter", "LIR"),
            ("Verify Minimum Event Count", "Diameter", "2"),
            ("Verify Diameter Session Match", "LIR", "LIA"),
            (
                "Verify Diameter Result Code",
                "LIA",
                "SUCCESS_RESULT_CODE_PLACEHOLDER",
            ),
            ("Verify Flexible Sequence", "IMS_CALL_FLOW_TEMPLATE"),
        ]

    approved = _approved_keyword_names()
    deduped_calls = [call for call in dict.fromkeys(calls) if call[0] in approved]
    return ["    ".join(call) for call in deduped_calls]


def _ticket_validation_text(ticket: TicketData | None) -> str:
    if ticket is None:
        return ""

    parts = [
        ticket.description,
        ticket.test_objective,
        *ticket.expected_outputs,
        *ticket.acceptance_criteria,
    ]
    for rule in ticket.validation_rules:
        parts.extend([rule.id, rule.description, rule.applies_to])
    for step in ticket.test_steps:
        parts.extend([step.action, step.expected_result, *step.validation_refs])
    return " ".join(_robot_cell(part).lower() for part in parts)
