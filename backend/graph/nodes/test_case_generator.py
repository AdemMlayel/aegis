from backend.graph.state import TestCase, TestContext


def test_case_generator(context: TestContext) -> TestContext:
    if context.requirement_analysis is None:
        raise ValueError("TestCaseGenerator requires context.requirement_analysis")
    if context.coverage_plan is None:
        raise ValueError("TestCaseGenerator requires context.coverage_plan")

    analysis = context.requirement_analysis
    context.test_cases = [
        TestCase(
            id="TC001",
            title=f"{analysis.business_action} - Happy Path",
            type="functional",
            priority="critical"
            if context.coverage_plan.risk_level == "critical"
            else "high",
            requirement_refs=["REQ-001"],
            preconditions=analysis.preconditions,
            steps=[
                f"Sign in as {analysis.actor}",
                f"Start {analysis.business_action}",
                "Submit valid data",
                "Verify the success response",
            ],
            expected_outcome="Primary user journey completes successfully",
            test_data_requirements={"users": ["valid_user"], "records": ["valid_record"]},
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
            test_data_requirements={"users": ["valid_user"], "records": ["invalid_record"]},
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
            test_data_requirements={"users": ["valid_user"], "records": ["boundary_record"]},
        ),
    ]
    context.mark("test_cases_generated")
    return context
