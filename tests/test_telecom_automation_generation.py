from pathlib import Path

import pytest

from backend.graph.artifacts import PROJECT_ROOT
from backend.graph.state import (
    ReviewFeedback,
    TestCase as WorkflowTestCase,
    TestDataBlock as WorkflowTestDataBlock,
    TicketData,
)
from backend.robot_libraries.registry import TELECOM_TRACE_LIBRARY
from backend.robot_libraries.telecom_trace_library import TelecomTraceLibrary
from backend.tickets.sources import DemoTicketSource
from backend.tools.automation_heuristics import (
    TELECOM_TRACE_FIXTURE,
    generate_robot_automation,
)
from backend.tools.robot_validation import validate_robot_automation


def _test_case() -> WorkflowTestCase:
    return WorkflowTestCase(
        id="TC900",
        title="Validate Sanitized IMS Call Trace",
        type="functional",
        priority="critical",
        preconditions=["Sanitized trace fixture is available"],
        steps=["Load the sanitized trace and validate SIP/Diameter evidence"],
        expected_outcome="Sanitized IMS call trace validations pass",
    )


def _test_data(test_case_id: str) -> dict[str, WorkflowTestDataBlock]:
    return {
        test_case_id: WorkflowTestDataBlock(
            test_case_id=test_case_id,
            strategy="fixture",
            resolved_data={"trace_fixture": [TELECOM_TRACE_FIXTURE]},
        )
    }


def test_telecom_trace_library_validates_sanitized_fixture() -> None:
    library = TelecomTraceLibrary()

    fixture_id = library.load_sanitized_trace(TELECOM_TRACE_FIXTURE)

    assert fixture_id == "SANITIZED_CALL_TRACE_FIXTURE"
    assert library.verify_sip_header_present("INVITE", "Call-ID") is True
    assert (
        library.verify_sip_header_present("INVITE", "P-Asserted-Identity")
        is True
    )
    assert library.verify_diameter_session_match("LIR", "LIA") is True
    assert (
        library.verify_diameter_result_code(
            "LIA",
            "SUCCESS_RESULT_CODE_PLACEHOLDER",
        )
        is True
    )
    assert library.verify_flexible_sequence("IMS_CALL_FLOW_TEMPLATE") is True


def test_telecom_trace_library_rejects_path_traversal() -> None:
    library = TelecomTraceLibrary()

    with pytest.raises(ValueError, match="fixtures"):
        library.load_sanitized_trace("../backend/config/settings.py")


def test_telecom_ticket_generates_keyword_based_robot() -> None:
    ticket = DemoTicketSource().fetch("DEMO-TELCO-IMS-001")
    assert ticket is not None
    test_case = _test_case()

    automation = generate_robot_automation(
        ticket_id=ticket.id,
        ticket=ticket,
        test_cases=[test_case],
        test_data=_test_data(test_case.id),
        revision=1,
        feedback=[],
    )

    robot_file = PROJECT_ROOT / automation[test_case.id].robot_file
    content = robot_file.read_text(encoding="utf-8")

    assert f"Library           {TELECOM_TRACE_LIBRARY}" in content
    assert f"${{TRACE_FIXTURE}}    {TELECOM_TRACE_FIXTURE}" in content
    assert "    Load Sanitized Trace    ${TRACE_FIXTURE}" in content
    assert "    Verify SIP Header Present    INVITE    Call-ID" in content
    assert (
        "    Verify SIP Header Present    INVITE    P-Asserted-Identity"
        in content
    )
    assert "    Verify Diameter Session Match    LIR    LIA" in content
    assert (
        "    Verify Diameter Result Code    LIA    SUCCESS_RESULT_CODE_PLACEHOLDER"
        in content
    )
    assert "    Verify Flexible Sequence    IMS_CALL_FLOW_TEMPLATE" in content


def test_non_telecom_ticket_keeps_generic_robot_generation() -> None:
    ticket = TicketData(
        id="GENERIC-AUTO-001",
        title="Generic checkout workflow",
        description="Validate a normal web checkout path.",
        labels=["commerce"],
    )
    test_case = _test_case()

    automation = generate_robot_automation(
        ticket_id=ticket.id,
        ticket=ticket,
        test_cases=[test_case],
        test_data=_test_data(test_case.id),
        revision=1,
        feedback=[
            ReviewFeedback(
                requested_by="reviewer",
                comment="Keep the generic Robot output intact.",
            )
        ],
    )

    robot_file = PROJECT_ROOT / automation[test_case.id].robot_file
    content = robot_file.read_text(encoding="utf-8")

    assert "Library           BuiltIn" in content
    assert "    Log    Step 1: Load the sanitized trace" in content
    assert "TelecomTraceLibrary" not in content


def test_robot_dryrun_accepts_generated_telecom_suite() -> None:
    ticket = DemoTicketSource().fetch("DEMO-TELCO-IMS-001")
    assert ticket is not None
    test_case = _test_case()
    test_data = _test_data(test_case.id)

    automation = generate_robot_automation(
        ticket_id=ticket.id,
        ticket=ticket,
        test_cases=[test_case],
        test_data=test_data,
        revision=1,
        feedback=[],
    )

    validated = validate_robot_automation(
        automation=automation,
        test_data=test_data,
    )

    validation = validated[test_case.id].validation
    assert validation.artifact_exists is True
    assert validation.dry_run_passed is True
    assert validation.errors == []
    assert Path(validated[test_case.id].robot_file).suffix == ".robot"
