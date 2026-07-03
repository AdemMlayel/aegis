"""Phase 4 agent/tool governance regressions.

Covers W6 (ungoverned high-risk tool denial + system-scope allowance), W8 (git
handoff path-traversal re-check), and S5 (retry allowlist defaults to no-retry).
"""
from __future__ import annotations

import pytest

from backend.governance.context import system_tool_scope
from backend.governance.policy import AgentPolicyDenied, agent_policy_engine
from backend.integrations.git_handoff import _safe_review_items
from backend.tools.base import (
    BaseTool,
    ToolExecutionError,
    execute_tool,
)


def test_high_risk_tool_denied_outside_governed_scope() -> None:
    """W6: a high-risk tool must not run on the ungoverned (execution is None)
    direct-API path."""
    with pytest.raises(AgentPolicyDenied, match="cannot run outside a governed"):
        agent_policy_engine.authorize_tool(None, "LocalGitHandoffTool", risk_tier="high")


def test_low_risk_tool_allowed_outside_governed_scope() -> None:
    """W6: low/medium tools remain usable on the direct path (no regression)."""
    # Should not raise.
    agent_policy_engine.authorize_tool(None, "SomeReadOnlyTool", risk_tier="low")


def test_high_risk_tool_allowed_inside_system_tool_scope() -> None:
    """W6: an explicit, RBAC-gated system scope authorizes the named high-risk
    tool (this is how the approval endpoint runs the Git handoff)."""
    from backend.governance.context import current_agent_execution

    with system_tool_scope(tool_names=("LocalGitHandoffTool",), caller="test"):
        # Should not raise -- the tool is explicitly system-authorized.
        agent_policy_engine.authorize_tool(
            current_agent_execution(),
            "LocalGitHandoffTool",
            risk_tier="high",
        )


def test_system_scope_does_not_authorize_other_tools() -> None:
    """W6: the system scope authorizes ONLY its named tools, nothing else."""
    from backend.governance.context import current_agent_execution

    with system_tool_scope(tool_names=("LocalGitHandoffTool",), caller="test"):
        execution = current_agent_execution()
        # A different high-risk tool is still denied (no skill graph + not named).
        with pytest.raises(AgentPolicyDenied):
            agent_policy_engine.authorize_tool(
                execution, "SomeOtherHighRiskTool", risk_tier="high"
            )


def test_safe_review_items_drops_traversal_paths() -> None:
    """W8: review items that escape the generated robot root are dropped and
    recorded as errors rather than force-added."""
    from backend.graph.artifacts import GENERATED_ROBOT_ROOT, relative_to_project

    # Build the in-root path from the actual configured robot root so the test
    # is independent of where GENERATED_ROOT points (the suite may relocate it).
    inside = relative_to_project(GENERATED_ROBOT_ROOT / "ticket_x" / "TC001.robot")
    errors: list[str] = []
    items = [
        inside,  # inside root -> kept
        "../../etc/passwd",  # traversal -> dropped
        "/etc/shadow",  # absolute escape -> dropped
        "backend/main.py",  # inside project but outside robot root -> dropped
    ]
    safe = _safe_review_items(items, errors)
    assert safe == [inside]
    assert len(errors) == 3
    assert all("escapes the generated robot root" in e for e in errors)


class _BoomTool(BaseTool):
    calls = 0

    def invoke(self, **kwargs: object) -> str:
        type(self).calls += 1
        raise RuntimeError("boom")


def test_tool_does_not_retry_by_default() -> None:
    """S5: with an empty retryable_exceptions allowlist, a failing tool runs
    exactly once even if max_retries were > 0 -- side-effecting tools must not
    silently double-execute."""
    from backend.tools.base import ToolSpec

    _BoomTool.calls = 0
    _BoomTool.spec = ToolSpec(name="_BoomTool", max_retries=3, retryable_exceptions=())
    with pytest.raises(ToolExecutionError):
        execute_tool(_BoomTool())
    assert _BoomTool.calls == 1


def test_tool_retries_only_allowlisted_exception() -> None:
    """S5: when a tool opts in via retryable_exceptions, it retries up to
    max_retries for that exception type."""
    from backend.tools.base import ToolSpec

    _BoomTool.calls = 0
    _BoomTool.spec = ToolSpec(
        name="_BoomTool", max_retries=2, retryable_exceptions=(RuntimeError,)
    )
    with pytest.raises(ToolExecutionError):
        execute_tool(_BoomTool())
    # 1 initial attempt + 2 retries.
    assert _BoomTool.calls == 3


def test_require_human_approval_enforced_when_opted_in(monkeypatch) -> None:
    """W7: with enforcement on, an approval-required agent refuses to run until
    the workflow context carries a granted approval -- the flag is no longer
    inert metadata."""
    from unittest import mock

    from backend.agents import base as agent_base
    from backend.agents.base import BaseAgent, agent_registry
    from backend.graph.state import ApprovalBlock, TestContext

    @agent_registry.register(
        name="W7ProbeAgent",
        risk_tier="critical",
        require_human_approval=True,
    )
    class _W7ProbeAgent(BaseAgent):
        def run(self, context: TestContext) -> TestContext:
            context.mark("w7_probe_ran")
            return context

    try:
        agent = agent_registry.create("W7ProbeAgent")
        with mock.patch.object(
            agent_base.settings, "enforce_agent_human_approval", True
        ):
            # No approval yet -> denied.
            with pytest.raises(AgentPolicyDenied, match="requires human approval"):
                agent.run(TestContext(created_by="pytest"))

            # Granted approval -> allowed.
            approved = TestContext(
                created_by="pytest",
                approval=ApprovalBlock(status="approved", git_status="not_started"),
            )
            result = agent.run(approved)
            assert result.workflow_status == "w7_probe_ran"

        # Enforcement off (default) -> the flag does not block.
        with mock.patch.object(
            agent_base.settings, "enforce_agent_human_approval", False
        ):
            result = agent.run(TestContext(created_by="pytest"))
            assert result.workflow_status == "w7_probe_ran"
    finally:
        agent_registry._agents.pop("W7ProbeAgent", None)
