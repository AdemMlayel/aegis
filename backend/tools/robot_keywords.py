from __future__ import annotations

from typing import Any

from backend.robot_libraries.registry import list_robot_keyword_capabilities
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="RobotKeywordCapabilityTool",
    isolation="process",
    description="Lists approved Robot Framework keyword capabilities.",
)
class RobotKeywordCapabilityTool(BaseTool):
    def invoke(self, **kwargs: Any) -> list[dict[str, object]]:
        domain = kwargs.get("domain")
        if domain is not None and not isinstance(domain, str):
            raise TypeError("RobotKeywordCapabilityTool requires a string domain")

        capabilities = list_robot_keyword_capabilities(domain=domain, include_corpus=True)
        return [capability.model_dump(mode="json") for capability in capabilities]
