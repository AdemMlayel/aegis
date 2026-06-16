import pytest

from backend.agents import agent_registry
from backend.graph.nodes.requirement_agent import requirement_agent
from backend.graph.state import TestContext as WorkflowContext
from backend.graph.state import TicketData
from backend.skills import skill_registry
from backend.tools import tool_registry


def _ticket() -> TicketData:
    return TicketData(
        id="REQ-BOUNDARY-1",
        title="Money Transfer Feature",
        description="As an authenticated customer, I want to transfer money.",
        acceptance_criteria=[
            "Transfer completes within 3 seconds",
            "Balance updates immediately",
        ],
        priority="high",
        labels=["banking", "payments"],
    )


def test_requirement_boundary_components_are_registered() -> None:
    assert agent_registry.has("RequirementAgent") is True
    assert skill_registry.has("AnalyzeRequirementSkill") is True
    assert tool_registry.has("LocalRequirementHeuristicTool") is True

    agent_spec = agent_registry.get("RequirementAgent").spec
    skill_spec = skill_registry.get("AnalyzeRequirementSkill").spec
    tool_spec = tool_registry.get("LocalRequirementHeuristicTool").spec

    assert agent_spec.skills == ("AnalyzeRequirementSkill",)
    assert skill_spec.tools == ("LocalRequirementHeuristicTool",)
    assert tool_spec.isolation == "process"


def test_requirement_graph_node_preserves_existing_heuristic_behavior() -> None:
    context = requirement_agent(WorkflowContext(created_by="pytest", ticket=_ticket()))

    assert context.workflow_status == "requirements_analyzed"
    assert context.requirement_analysis is not None
    assert context.requirement_analysis.business_action == "Money Transfer Feature"
    assert context.requirement_analysis.domain == "banking"
    assert context.requirement_analysis.actor == "customer"
    assert context.requirement_analysis.preconditions == [
        "User can access the target environment"
    ]
    assert context.requirement_analysis.expected_results == [
        "Transfer completes within 3 seconds",
        "Balance updates immediately",
    ]
    assert context.requirement_analysis.missing_fields == [
        "Error scenarios are not described",
        "Data constraints are not described",
    ]
    assert context.requirement_analysis.clarification_questions == [
        "Which error states should be tested?",
        "What input limits, formats, or currencies apply?",
    ]
    checklist = context.requirement_analysis.completeness_checklist
    assert checklist.actor_identified is True
    assert checklist.preconditions_defined is True
    assert checklist.expected_outcome_specified is True
    assert checklist.error_scenarios_mentioned is False
    assert checklist.data_constraints_defined is False
    assert checklist.performance_expectations_set is True


def test_requirement_agent_still_requires_ticket_data() -> None:
    with pytest.raises(ValueError, match="RequirementAgent requires context.ticket"):
        requirement_agent(WorkflowContext(created_by="pytest"))
