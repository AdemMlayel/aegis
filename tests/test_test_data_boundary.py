import pytest

from backend.agents import agent_registry
from backend.graph.nodes.coverage_planner import coverage_planner
from backend.graph.nodes.requirement_agent import requirement_agent
from backend.graph.nodes.test_case_generator import (
    test_case_generator as run_test_case_generator,
)
from backend.graph.nodes.test_data_resolver import (
    test_data_resolver as run_test_data_resolver,
)
from backend.graph.state import TestContext as WorkflowContext
from backend.graph.state import TicketData
from backend.skills import skill_registry
from backend.tools import tool_registry


def _context_with_test_cases() -> WorkflowContext:
    context = WorkflowContext(
        created_by="pytest",
        ticket=TicketData(
            id="TD-BOUNDARY-1",
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
    return run_test_case_generator(context)


def test_test_data_boundary_components_are_registered() -> None:
    assert agent_registry.has("TestDataResolverAgent") is True
    assert skill_registry.has("ResolveTestDataSkill") is True
    assert tool_registry.has("LocalTestDataHeuristicTool") is True

    agent_spec = agent_registry.get("TestDataResolverAgent").spec
    skill_spec = skill_registry.get("ResolveTestDataSkill").spec
    tool_spec = tool_registry.get("LocalTestDataHeuristicTool").spec

    assert agent_spec.skills == ("ResolveTestDataSkill",)
    assert skill_spec.tools == ("LocalTestDataHeuristicTool",)
    assert tool_spec.isolation == "process"


def test_test_data_graph_node_preserves_existing_heuristic_behavior() -> None:
    context = run_test_data_resolver(_context_with_test_cases())

    assert context.workflow_status == "test_data_resolved"
    assert set(context.test_data) == {"TC001", "TC002", "TC003"}
    assert context.test_data["TC001"].test_case_id == "TC001"
    assert context.test_data["TC001"].strategy == "factory"
    assert context.test_data["TC001"].resolved_data == {
        "users": ["tc001_valid_user"],
        "records": ["tc001_valid_record"],
    }
    assert context.test_data["TC001"].teardown == ["cleanup_tc001_data"]

    assert context.test_data["TC002"].test_case_id == "TC002"
    assert context.test_data["TC002"].strategy == "fixture"
    assert context.test_data["TC002"].resolved_data == {
        "users": ["tc002_valid_user"],
        "records": ["tc002_invalid_record"],
    }
    assert context.test_data["TC002"].teardown == ["cleanup_tc002_data"]

    assert context.test_data["TC003"].test_case_id == "TC003"
    assert context.test_data["TC003"].strategy == "fixture"
    assert context.test_data["TC003"].resolved_data == {
        "users": ["tc003_valid_user"],
        "records": ["tc003_boundary_record"],
    }
    assert context.test_data["TC003"].teardown == ["cleanup_tc003_data"]


def test_test_data_resolver_still_requires_test_cases() -> None:
    with pytest.raises(
        ValueError,
        match="TestDataResolver requires context.test_cases",
    ):
        run_test_data_resolver(WorkflowContext(created_by="pytest"))
