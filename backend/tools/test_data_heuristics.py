from __future__ import annotations

from typing import Any, Literal

from backend.graph.state import TestCase, TestDataBlock
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalTestDataHeuristicTool",
    isolation="process",
    description="Resolves deterministic test data blocks for generated test cases.",
)
class LocalTestDataHeuristicTool(BaseTool):
    def invoke(self, **kwargs: Any) -> dict[str, TestDataBlock]:
        test_cases = kwargs.get("test_cases")
        if not isinstance(test_cases, list) or not all(
            isinstance(test_case, TestCase) for test_case in test_cases
        ):
            raise TypeError("LocalTestDataHeuristicTool requires list[TestCase]")
        return resolve_test_data(test_cases=test_cases)


def resolve_test_data(*, test_cases: list[TestCase]) -> dict[str, TestDataBlock]:
    resolved: dict[str, TestDataBlock] = {}
    for test_case in test_cases:
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
    return resolved


def _strategy_for_test_type(
    test_type: str,
) -> Literal["factory", "fixture"]:
    if test_type in {"negative", "boundary"}:
        return "fixture"
    return "factory"
