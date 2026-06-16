from __future__ import annotations

from typing import Any

from backend.graph.state import CoveragePlan, RequirementAnalysis, TicketData
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalCoverageHeuristicTool",
    isolation="process",
    description="Plans coverage with deterministic local risk and test-type heuristics.",
)
class LocalCoverageHeuristicTool(BaseTool):
    def invoke(self, **kwargs: Any) -> CoveragePlan:
        ticket = kwargs.get("ticket")
        analysis = kwargs.get("requirement_analysis")
        if not isinstance(ticket, TicketData):
            raise TypeError("LocalCoverageHeuristicTool requires a TicketData ticket")
        if not isinstance(analysis, RequirementAnalysis):
            raise TypeError(
                "LocalCoverageHeuristicTool requires RequirementAnalysis"
            )
        return plan_coverage(ticket=ticket, analysis=analysis)


def plan_coverage(*, ticket: TicketData, analysis: RequirementAnalysis) -> CoveragePlan:
    if ticket.priority == "critical":
        risk_level = "critical"
        criticality = 10
    elif ticket.priority == "high" or analysis.domain == "banking":
        risk_level = "high"
        criticality = 8
    elif ticket.priority == "low":
        risk_level = "low"
        criticality = 3
    else:
        risk_level = "medium"
        criticality = 5

    required_types = ["functional", "negative"]
    if risk_level in {"high", "critical"}:
        required_types.append("boundary")
    if analysis.completeness_checklist.performance_expectations_set:
        required_types.append("performance")

    return CoveragePlan(
        risk_level=risk_level,
        business_criticality=criticality,
        test_types_required=required_types,
        coverage_matrix={
            "REQ-001 primary success path": ["TC001"],
            "REQ-002 invalid or rejected input": ["TC002"],
            "REQ-003 boundary condition": ["TC003"],
        },
        regression_tests_to_rerun=[],
        estimated_automation_effort="medium" if risk_level != "critical" else "high",
        prioritization_order=["TC001", "TC002", "TC003"],
    )
