import pytest

from backend.agents import agent_registry
from backend.graph.nodes.report_generator import report_generator as run_report_generator
from backend.graph.state import (
    ApprovalBlock,
    AutomationBlock,
    AutomationValidation,
    CoveragePlan,
    TestCase as WorkflowTestCase,
    TestContext as WorkflowContext,
    TicketData,
)
from backend.skills import skill_registry
from backend.tools import tool_registry


def _report_context() -> WorkflowContext:
    return WorkflowContext(
        created_by="pytest",
        ticket=TicketData(id="REPORT-READY-1", title="Report Ready"),
        coverage_plan=CoveragePlan(risk_level="high"),
        test_cases=[
            WorkflowTestCase(
                id="TC001",
                title="Ready Path",
                type="functional",
                priority="high",
                expected_outcome="Ready path completes",
            ),
            WorkflowTestCase(
                id="TC002",
                title="Blocked Path",
                type="negative",
                priority="high",
                expected_outcome="Blocked path is rejected",
            ),
        ],
        automation={
            "TC001": AutomationBlock(
                test_case_id="TC001",
                robot_file="generated/robot/report_ready_1/TC001_ready.robot",
                validation=AutomationValidation(
                    artifact_exists=True,
                    dry_run_passed=True,
                    validation_attempts=1,
                ),
            ),
            "TC002": AutomationBlock(
                test_case_id="TC002",
                robot_file="generated/robot/report_ready_1/TC002_blocked.robot",
                validation=AutomationValidation(
                    artifact_exists=True,
                    dry_run_passed=None,
                    dry_run_skipped_reason="Robot Framework CLI is not installed",
                ),
            ),
        },
        approval=ApprovalBlock(status="not_ready"),
    )


def test_report_boundary_components_are_registered() -> None:
    assert agent_registry.has("ReportGeneratorAgent") is True
    assert skill_registry.has("GenerateReportSkill") is True
    assert tool_registry.has("LocalReportGenerationTool") is True

    agent_spec = agent_registry.get("ReportGeneratorAgent").spec
    skill_spec = skill_registry.get("GenerateReportSkill").spec
    tool_spec = tool_registry.get("LocalReportGenerationTool").spec

    assert agent_spec.skills == ("GenerateReportSkill",)
    assert skill_spec.tools == ("LocalReportGenerationTool",)
    assert tool_spec.isolation == "process"


def test_report_graph_node_preserves_existing_summary_behavior() -> None:
    context = run_report_generator(_report_context())

    assert context.workflow_status == "report_generated"
    assert context.reports is not None
    assert context.reports.summary == (
        "Generated 2 starter test cases and 2 Robot automation files for "
        "REPORT-READY-1. Validated 1/2; approval status is not_ready."
    )
    assert context.reports.total_test_cases == 2
    assert context.reports.highest_risk == "high"
    assert context.reports.next_actions == [
        "Review requirement clarification questions",
        "Review generated Robot files through the automation file endpoint",
        "Replace the Git handoff stub with real branch and PR creation",
        "Add audit records for approval decisions",
    ]


def test_report_graph_node_preserves_unknown_ticket_fallback() -> None:
    context = _report_context()
    context.ticket = None

    context = run_report_generator(context)

    assert context.reports is not None
    assert "for unknown ticket." in context.reports.summary


def test_report_generator_still_requires_coverage_plan() -> None:
    with pytest.raises(
        ValueError,
        match="ReportGenerator requires context.coverage_plan",
    ):
        run_report_generator(WorkflowContext(created_by="pytest"))
