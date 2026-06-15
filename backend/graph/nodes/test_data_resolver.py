from backend.graph.state import TestContext, TestDataBlock


def _strategy_for_test_type(test_type: str) -> str:
    if test_type in {"negative", "boundary"}:
        return "fixture"
    return "factory"


def test_data_resolver(context: TestContext) -> TestContext:
    if not context.test_cases:
        raise ValueError("TestDataResolver requires context.test_cases")

    resolved: dict[str, TestDataBlock] = {}
    for test_case in context.test_cases:
        resolved_data = {
            group: [f"{test_case.id.lower()}_{requirement}" for requirement in values]
            for group, values in test_case.test_data_requirements.items()
        }
        resolved[test_case.id] = TestDataBlock(
            test_case_id=test_case.id,
            strategy=_strategy_for_test_type(test_case.type),
            resolved_data=resolved_data,
            teardown=[f"cleanup_{test_case.id.lower()}_data"],
        )

    context.test_data = resolved
    context.mark("test_data_resolved")
    return context
