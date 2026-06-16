from __future__ import annotations

from typing import Any

from backend.graph.state import TestContext
from backend.integrations.git_handoff import GitExecutionResult, create_git_handoff
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalGitHandoffTool",
    isolation="process",
    description="Creates the local Git handoff payload and attempts branch/commit/PR when Git is available.",
    timeout_seconds=90,
    max_retries=0,
)
class LocalGitHandoffTool(BaseTool):
    def invoke(self, **kwargs: Any) -> GitExecutionResult:
        context = kwargs.get("context")
        reviewed_by = kwargs.get("reviewed_by")
        if not isinstance(context, TestContext):
            raise TypeError("LocalGitHandoffTool requires a TestContext")
        if not isinstance(reviewed_by, str) or not reviewed_by.strip():
            raise TypeError("LocalGitHandoffTool requires a reviewed_by string")
        return create_git_handoff(context, reviewed_by=reviewed_by)


__all__ = ["GitExecutionResult", "LocalGitHandoffTool"]
