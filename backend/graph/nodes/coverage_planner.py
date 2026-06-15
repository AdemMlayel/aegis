from backend.graph.state import CoveragePlan, TestContext


def coverage_planner(context: TestContext) -> TestContext:
    if context.requirement_analysis is None:
        raise ValueError("CoveragePlanner requires context.requirement_analysis")
    if context.ticket is None:
        raise ValueError("CoveragePlanner requires context.ticket")

    ticket = context.ticket
    analysis = context.requirement_analysis

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

    context.coverage_plan = CoveragePlan(
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
    context.mark("coverage_planned")
    return context
