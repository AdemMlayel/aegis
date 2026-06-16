import pytest

from backend.agents import agent_registry
from backend.graph.nodes.coverage_planner import coverage_planner
from backend.graph.nodes.requirement_agent import requirement_agent
from backend.graph.nodes.test_case_generator import (
    test_case_generator as run_test_case_generator,
)
from backend.graph.state import TestContext as WorkflowContext
from backend.graph.state import TicketData
from backend.skills import skill_registry
from backend.tools import tool_registry


def _context_with_requirements() -> WorkflowContext:
    context = WorkflowContext(
        created_by="pytest",
        ticket=TicketData(
            id="TC-BOUNDARY-1",
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


def _context_with_coverage() -> WorkflowContext:
    return coverage_planner(_context_with_requirements())


def test_test_case_boundary_components_are_registered() -> None:
    assert agent_registry.has("TestCaseGeneratorAgent") is True
    assert skill_registry.has("GenerateTestCasesSkill") is True
    assert tool_registry.has("LocalTestCaseHeuristicTool") is True

    agent_spec = agent_registry.get("TestCaseGeneratorAgent").spec
    skill_spec = skill_registry.get("GenerateTestCasesSkill").spec
    tool_spec = tool_registry.get("LocalTestCaseHeuristicTool").spec

    assert agent_spec.skills == ("GenerateTestCasesSkill",)
    assert skill_spec.tools == ("LocalTestCaseHeuristicTool",)
    assert tool_spec.isolation == "process"


def test_test_case_graph_node_preserves_existing_heuristic_behavior() -> None:
    context = run_test_case_generator(_context_with_coverage())

    assert context.workflow_status == "test_cases_generated"
    assert [test_case.id for test_case in context.test_cases] == [
        "TC001",
        "TC002",
        "TC003",
    ]
    assert [test_case.title for test_case in context.test_cases] == [
        "Money Transfer Feature - Happy Path",
        "Money Transfer Feature - Rejected Input",
        "Money Transfer Feature - Boundary Condition",
    ]
    assert [test_case.type for test_case in context.test_cases] == [
        "functional",
        "negative",
        "boundary",
    ]
    assert [test_case.priority for test_case in context.test_cases] == [
        "high",
        "high",
        "medium",
    ]
    assert context.test_cases[0].requirement_refs == ["REQ-001"]
    assert context.test_cases[0].preconditions == [
        "User can access the target environment"
    ]
    assert context.test_cases[0].steps == [
        "Sign in as customer",
        "Start Money Transfer Feature",
        "Submit valid data",
        "Verify the success response",
    ]
    assert context.test_cases[0].expected_outcome == (
        "Primary user journey completes successfully"
    )
    assert context.test_cases[0].test_data_requirements == {
        "users": ["valid_user"],
        "records": ["valid_record"],
    }
    assert context.test_cases[1].test_data_requirements == {
        "users": ["valid_user"],
        "records": ["invalid_record"],
    }
    assert context.test_cases[2].test_data_requirements == {
        "users": ["valid_user"],
        "records": ["boundary_record"],
    }


def test_test_case_generator_still_requires_requirement_analysis() -> None:
    with pytest.raises(
        ValueError,
        match="TestCaseGenerator requires context.requirement_analysis",
    ):
        run_test_case_generator(WorkflowContext(created_by="pytest"))


def test_test_case_generator_still_requires_coverage_plan() -> None:
    with pytest.raises(
        ValueError,
        match="TestCaseGenerator requires context.coverage_plan",
    ):
        run_test_case_generator(_context_with_requirements())
