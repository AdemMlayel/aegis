from __future__ import annotations

import shutil
from importlib.util import find_spec

import pytest

from backend.agents import agent_registry
from backend.graph.nodes.automation_generator import (
    automation_generator as run_automation_generator,
)
from backend.graph.nodes.coverage_planner import coverage_planner
from backend.graph.nodes.requirement_agent import requirement_agent
from backend.graph.nodes.test_case_generator import (
    test_case_generator as run_test_case_generator,
)
from backend.graph.nodes.test_data_resolver import (
    test_data_resolver as run_test_data_resolver,
)
from backend.graph.nodes.validator import validator as run_validator
from backend.graph.state import TestContext as WorkflowContext
from backend.graph.state import TicketData
from backend.skills import skill_registry
from backend.tools import tool_registry


def _context_with_automation() -> WorkflowContext:
    context = WorkflowContext(
        created_by="pytest",
        ticket=TicketData(
            id="VAL-BOUNDARY-1",
            title="Money Transfer Feature",
            description="As an authenticated customer, I want to transfer money.",
            acceptance_criteria=[
                "Transfer completes within 3 seconds",
                "Balance updates immediately",
            ],
            priority="high",
            labels=["banking", "payments"],
        ),
    )
    context = requirement_agent(context)
    context = coverage_planner(context)
    context = run_test_case_generator(context)
    context = run_test_data_resolver(context)
    return run_automation_generator(context)


def _robot_available() -> bool:
    return shutil.which("robot") is not None or find_spec("robot") is not None


def test_validation_boundary_components_are_registered() -> None:
    assert agent_registry.has("ValidatorAgent") is True
    assert skill_registry.has("ValidateAutomationSkill") is True
    assert tool_registry.has("LocalRobotValidationTool") is True
    assert tool_registry.has("ValidationSummaryTool") is True

    agent_spec = agent_registry.get("ValidatorAgent").spec
    skill_spec = skill_registry.get("ValidateAutomationSkill").spec
    tool_spec = tool_registry.get("LocalRobotValidationTool").spec
    summary_tool_spec = tool_registry.get("ValidationSummaryTool").spec

    assert agent_spec.skills == ("ValidateAutomationSkill",)
    assert skill_spec.tools == (
        "LocalRobotValidationTool",
        "ValidationSummaryTool",
    )
    assert tool_spec.isolation == "process"
    assert summary_tool_spec.isolation == "in_process"


def test_validation_graph_node_preserves_existing_robot_validation() -> None:
    context = run_validator(_context_with_automation())

    assert set(context.automation) == {"TC001", "TC002", "TC003"}
    assert all(block.data_reference_check_passed for block in context.automation.values())
    assert all(block.validation.artifact_exists for block in context.automation.values())

    validation = context.automation["TC001"].validation
    summary = context.validation_summary
    assert summary is not None
    assert summary.total_artifacts == 3
    assert summary.passed_artifacts == 3
    assert summary.failed_artifacts == 0
    assert summary.requirement_coverage_percent == 100
    assert summary.artifact_pass_percent == 100
    assert summary.data_reference_percent == 100
    assert summary.missing_requirements == []
    assert summary.quality_score >= 90
    if _robot_available():
        assert context.workflow_status == "automation_validated"
        assert validation.dry_run_passed is True
        assert validation.validation_attempts == 1
        assert validation.errors == []
    else:
        assert context.workflow_status == "automation_validated"
        assert validation.dry_run_passed is True
        assert validation.dry_run_skipped_reason == (
            "Robot Framework CLI is not installed; local structural validation was used"
        )
        assert validation.validation_attempts == 1
        assert validation.errors == []


def test_validation_reports_missing_test_data_reference() -> None:
    context = _context_with_automation()
    context.test_data.pop("TC002")

    context = run_validator(context)

    assert context.workflow_status == "automation_validation_failed"
    assert context.validation_summary is not None
    assert context.validation_summary.status == "failed"
    assert context.validation_summary.data_reference_percent == 67
    assert context.validation_summary.failed_artifacts == 1
    assert context.automation["TC002"].data_reference_check_passed is False
    assert "Missing resolved test data for TC002" in (
        context.automation["TC002"].validation.errors
    )


def test_validation_reports_missing_robot_artifact() -> None:
    context = _context_with_automation()
    context.automation["TC001"].robot_file = "generated/robot/missing.robot"

    context = run_validator(context)

    assert context.workflow_status == "automation_validation_failed"
    assert context.validation_summary is not None
    assert context.validation_summary.status == "failed"
    assert context.validation_summary.artifact_pass_percent == 67
    assert context.automation["TC001"].validation.artifact_exists is False
    assert context.automation["TC001"].validation.dry_run_passed is False
    assert context.automation["TC001"].validation.validation_attempts == 0
    assert "Generated Robot file does not exist: generated/robot/missing.robot" in (
        context.automation["TC001"].validation.errors
    )


def test_validation_summary_fails_uncovered_planned_requirement() -> None:
    context = _context_with_automation()
    assert context.coverage_plan is not None
    context.coverage_plan.coverage_matrix["REQ-999 audit trail"] = ["TC999"]

    context = run_validator(context)

    assert context.validation_summary is not None
    assert context.validation_summary.status == "failed"
    assert context.validation_summary.requirement_coverage_percent == 75
    assert context.validation_summary.missing_requirements == [
        "REQ-999 audit trail"
    ]
    assert context.validation_summary.passed_artifacts == 3


def test_validator_still_requires_automation() -> None:
    with pytest.raises(ValueError, match="Validator requires context.automation"):
        run_validator(WorkflowContext(created_by="pytest"))
