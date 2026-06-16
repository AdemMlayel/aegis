import pytest

from backend.agents import AgentRegistrationError, AgentRegistry, BaseAgent
from backend.execution import (
    BaseExecutionAdapter,
    ExecutionAdapterRegistrationError,
    ExecutionAdapterRegistry,
    MockExecutionAdapter,
    execution_adapter_registry,
)
from backend.graph.state import TestContext as WorkflowContext
from backend.skills import BaseSkill, SkillRegistrationError, SkillRegistry
from backend.tools import BaseTool, ToolRegistrationError, ToolRegistry


def test_agent_registry_registers_metadata_and_creates_instances() -> None:
    registry = AgentRegistry()

    @registry.register(
        name="DemoAgent",
        skills=["DemoSkill"],
        description="Runs a demo agent",
        version="1.2.3",
    )
    class DemoAgent(BaseAgent):
        def run(self, context: WorkflowContext) -> WorkflowContext:
            context.mark("demo_agent_ran")
            return context

    assert registry.has("DemoAgent") is True
    assert registry.get("DemoAgent") is DemoAgent
    assert registry.list_specs()[0].name == "DemoAgent"
    assert registry.list_specs()[0].skills == ("DemoSkill",)
    assert registry.list_specs()[0].version == "1.2.3"

    agent = registry.create("DemoAgent", skill_registry="skills")
    result = agent.run(WorkflowContext(created_by="pytest"))

    assert isinstance(agent, DemoAgent)
    assert agent.skill_registry == "skills"
    assert result.workflow_status == "demo_agent_ran"


def test_skill_registry_registers_metadata_and_creates_instances() -> None:
    registry = SkillRegistry()

    @registry.register(name="DemoSkill", tools=["DemoTool"])
    class DemoSkill(BaseSkill):
        def execute(self, context: WorkflowContext) -> WorkflowContext:
            context.mark("demo_skill_executed")
            return context

    skill = registry.create("DemoSkill", tool_registry="tools")
    result = skill.execute(WorkflowContext(created_by="pytest"))

    assert isinstance(skill, DemoSkill)
    assert skill.tool_registry == "tools"
    assert registry.list_specs()[0].tools == ("DemoTool",)
    assert result.workflow_status == "demo_skill_executed"


def test_tool_registry_registers_metadata_and_creates_instances() -> None:
    registry = ToolRegistry()

    @registry.register(name="DemoTool", isolation="process")
    class DemoTool(BaseTool):
        def invoke(self, **kwargs: object) -> dict[str, object]:
            return {"received": kwargs}

    tool = registry.create("DemoTool")

    assert isinstance(tool, DemoTool)
    assert registry.list_specs()[0].isolation == "process"
    assert tool.invoke(ticket_id="MOCK-101") == {
        "received": {"ticket_id": "MOCK-101"}
    }


def test_execution_adapter_registry_registers_metadata_and_creates_instances() -> None:
    registry = ExecutionAdapterRegistry()

    @registry.register(
        name="DemoAdapter",
        engine="local",
        capabilities=["demo"],
        description="Runs demo execution",
        version="1.2.3",
    )
    class DemoAdapter(BaseExecutionAdapter):
        def execute(
            self,
            context: WorkflowContext,
            *,
            actor: str,
            env: str,
            branch: str | None = None,
            tags=(),
        ) -> WorkflowContext:
            context.mark(f"demo_adapter_{env}_{actor}")
            return context

    adapter = registry.create("DemoAdapter")
    result = adapter.execute(WorkflowContext(created_by="pytest"), actor="ci", env="dev")

    assert isinstance(adapter, DemoAdapter)
    assert registry.list_specs()[0].name == "DemoAdapter"
    assert registry.list_specs()[0].engine == "local"
    assert registry.list_specs()[0].capabilities == ("demo",)
    assert registry.list_specs()[0].version == "1.2.3"
    assert result.workflow_status == "demo_adapter_dev_ci"


def test_default_mock_execution_adapter_is_registered() -> None:
    assert execution_adapter_registry.has("mock") is True
    assert execution_adapter_registry.get("mock") is MockExecutionAdapter
    assert execution_adapter_registry.list_specs()[0].name == "mock"


def test_registries_reject_duplicates_and_empty_names() -> None:
    agent_registry = AgentRegistry()
    skill_registry = SkillRegistry()
    tool_registry = ToolRegistry()
    execution_registry = ExecutionAdapterRegistry()

    @agent_registry.register(name="DuplicateAgent")
    class DuplicateAgent(BaseAgent):
        def run(self, context: WorkflowContext) -> WorkflowContext:
            return context

    with pytest.raises(AgentRegistrationError):
        agent_registry.register(name="DuplicateAgent")(DuplicateAgent)
    with pytest.raises(AgentRegistrationError):
        agent_registry.register(name=" ")

    @skill_registry.register(name="DuplicateSkill")
    class DuplicateSkill(BaseSkill):
        def execute(self, context: WorkflowContext) -> WorkflowContext:
            return context

    with pytest.raises(SkillRegistrationError):
        skill_registry.register(name="DuplicateSkill")(DuplicateSkill)
    with pytest.raises(SkillRegistrationError):
        skill_registry.register(name="")

    @tool_registry.register(name="DuplicateTool")
    class DuplicateTool(BaseTool):
        def invoke(self, **kwargs: object) -> object:
            return kwargs

    with pytest.raises(ToolRegistrationError):
        tool_registry.register(name="DuplicateTool")(DuplicateTool)
    with pytest.raises(ToolRegistrationError):
        tool_registry.register(name="\t")

    @execution_registry.register(name="DuplicateAdapter")
    class DuplicateAdapter(BaseExecutionAdapter):
        def execute(
            self,
            context: WorkflowContext,
            *,
            actor: str,
            env: str,
            branch: str | None = None,
            tags=(),
        ) -> WorkflowContext:
            return context

    with pytest.raises(ExecutionAdapterRegistrationError):
        execution_registry.register(name="DuplicateAdapter")(DuplicateAdapter)
    with pytest.raises(ExecutionAdapterRegistrationError):
        execution_registry.register(name=" ")


def test_registries_reject_wrong_base_classes() -> None:
    class NotAnAgent:
        pass

    class NotASkill:
        pass

    class NotATool:
        pass

    class NotAnExecutionAdapter:
        pass

    with pytest.raises(TypeError):
        AgentRegistry().register(name="BadAgent")(NotAnAgent)
    with pytest.raises(TypeError):
        SkillRegistry().register(name="BadSkill")(NotASkill)
    with pytest.raises(TypeError):
        ToolRegistry().register(name="BadTool")(NotATool)
    with pytest.raises(TypeError):
        ExecutionAdapterRegistry().register(name="BadAdapter")(NotAnExecutionAdapter)
