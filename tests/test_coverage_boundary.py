import pytest

from backend.agents import agent_registry
from backend.graph.nodes.coverage_planner import coverage_planner
from backend.graph.nodes.requirement_agent import requirement_agent
from backend.graph.state import TestContext as WorkflowContext
from backend.graph.state import TicketData
from backend.skills import skill_registry
from backend.tools import tool_registry


def _context_with_requirements() -> WorkflowContext:
    context = WorkflowContext(
        created_by="pytest",
        ticket=TicketData(
            id="COV-BOUNDARY-1",
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
    return requirement_agent(context)


def test_coverage_boundary_components_are_registered() -> None:
    assert agent_registry.has("CoveragePlannerAgent") is True
    assert skill_registry.has("PlanCoverageSkill") is True
    assert tool_registry.has("LocalCoverageHeuristicTool") is True

    agent_spec = agent_registry.get("CoveragePlannerAgent").spec
    skill_spec = skill_registry.get("PlanCoverageSkill").spec
    tool_spec = tool_registry.get("LocalCoverageHeuristicTool").spec

    assert agent_spec.skills == ("PlanCoverageSkill",)
    assert skill_spec.tools == ("LocalCoverageHeuristicTool",)
    assert tool_spec.isolation == "process"


def test_coverage_graph_node_derives_matrix_from_real_requirements() -> None:
    context = coverage_planner(_context_with_requirements())

    assert context.workflow_status == "coverage_planned"
    assert context.coverage_plan is not None
    assert context.coverage_plan.risk_level == "high"
    assert context.coverage_plan.business_criticality == 8
    # Base functional+negative, plus boundary (high risk), plus performance
    # (acceptance criteria mention "within 3 seconds").
    assert "functional" in context.coverage_plan.test_types_required
    assert "negative" in context.coverage_plan.test_types_required
    assert "boundary" in context.coverage_plan.test_types_required
    assert "performance" in context.coverage_plan.test_types_required
    # The matrix is now DERIVED from the ticket's real acceptance criteria, not
    # the old hardcoded REQ-001/2/3 placeholders.
    matrix = context.coverage_plan.coverage_matrix
    assert matrix["REQ-001 Money Transfer Feature — primary success path"] == ["TC001"]
    assert matrix["REQ-002 Transfer completes within 3 seconds"] == ["TC002"]
    assert matrix["REQ-003 Balance updates immediately"] == ["TC003"]
    assert context.coverage_plan.regression_tests_to_rerun == []
    assert context.coverage_plan.estimated_automation_effort == "medium"
    assert context.coverage_plan.prioritization_order == ["TC001", "TC002", "TC003"]
    # Confidence is now propagated from requirement analysis, not a fixed literal.
    assert 0.0 < context.coverage_plan.confidence <= 1.0
    assert any("confidence:" in note for note in context.coverage_plan.risk_rationale)


def test_coverage_planner_still_requires_requirement_analysis() -> None:
    with pytest.raises(
        ValueError,
        match="CoveragePlanner requires context.requirement_analysis",
    ):
        coverage_planner(WorkflowContext(created_by="pytest"))


def test_coverage_planner_still_requires_ticket_data() -> None:
    context = _context_with_requirements()
    context.ticket = None

    with pytest.raises(ValueError, match="CoveragePlanner requires context.ticket"):
        coverage_planner(context)
