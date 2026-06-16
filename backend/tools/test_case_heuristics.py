from __future__ import annotations

from typing import Any

from backend.graph.state import CoveragePlan, RequirementAnalysis, TestCase
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalTestCaseHeuristicTool",
    isolation="process",
    description="Generates deterministic test cases from requirement and coverage data.",
)
class LocalTestCaseHeuristicTool(BaseTool):
    def invoke(self, **kwargs: Any) -> list[TestCase]:
        analysis = kwargs.get("requirement_analysis")
        coverage_plan = kwargs.get("coverage_plan")
        if not isinstance(analysis, RequirementAnalysis):
            raise TypeError(
                "LocalTestCaseHeuristicTool requires RequirementAnalysis"
            )
        if not isinstance(coverage_plan, CoveragePlan):
            raise TypeError("LocalTestCaseHeuristicTool requires CoveragePlan")
        return generate_test_cases(analysis=analysis, coverage_plan=coverage_plan)


def generate_test_cases(
    *,
    analysis: RequirementAnalysis,
    coverage_plan: CoveragePlan,
) -> list[TestCase]:
    return [
        TestCase(
            id="TC001",
            title=f"{analysis.business_action} - Happy Path",
            type="functional",
            priority="critical" if coverage_plan.risk_level == "critical" else "high",
            requirement_refs=["REQ-001"],
            preconditions=analysis.preconditions,
            steps=[
                f"Sign in as {analysis.actor}",
                f"Start {analysis.business_action}",
                "Submit valid data",
                "Verify the success response",
            ],
            expected_outcome="Primary user journey completes successfully",
            test_data_requirements={
                "users": ["valid_user"],
                "records": ["valid_record"],
            },
        ),
        TestCase(
            id="TC002",
            title=f"{analysis.business_action} - Rejected Input",
            type="negative",
            priority="high",
            requirement_refs=["REQ-002"],
            preconditions=analysis.preconditions,
            steps=[
                f"Sign in as {analysis.actor}",
                f"Start {analysis.business_action}",
                "Submit invalid or incomplete data",
                "Verify that the action is rejected clearly",
            ],
            expected_outcome="Invalid action is rejected without changing system state",
            test_data_requirements={
                "users": ["valid_user"],
                "records": ["invalid_record"],
            },
        ),
        TestCase(
            id="TC003",
            title=f"{analysis.business_action} - Boundary Condition",
            type="boundary",
            priority="medium",
            requirement_refs=["REQ-003"],
            preconditions=analysis.preconditions,
            steps=[
                f"Sign in as {analysis.actor}",
                "Prepare boundary-value data",
                f"Run {analysis.business_action}",
                "Verify boundary behavior",
            ],
            expected_outcome="Boundary values are handled according to requirements",
            test_data_requirements={
                "users": ["valid_user"],
                "records": ["boundary_record"],
            },
        ),
    ]
