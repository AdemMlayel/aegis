from __future__ import annotations

from collections.abc import Iterable

from backend.execution.base import BaseExecutionAdapter, execution_adapter_registry
from backend.graph.execution import run_mock_execution
from backend.graph.state import TestContext


@execution_adapter_registry.register(
    name="mock",
    engine="local",
    capabilities=("deterministic", "robot-artifact-aware", "no-browser"),
    description="Runs the local deterministic mock execution profile.",
)
class MockExecutionAdapter(BaseExecutionAdapter):
    def execute(
        self,
        context: TestContext,
        *,
        actor: str,
        env: str,
        branch: str | None = None,
        tags: Iterable[str] = (),
    ) -> TestContext:
        return run_mock_execution(context, actor=actor, env=env)
