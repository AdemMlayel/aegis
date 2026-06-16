from __future__ import annotations

import pytest

from backend.agents import agent_registry
from backend.graph.nodes.human_approval import human_approval as run_human_approval
from backend.graph.state import (
    ApprovalBlock,
    AutomationBlock,
    AutomationValidation,
    TestContext as WorkflowContext,
    TicketData,
)
from backend.skills import skill_registry
from backend.tools import tool_registry


def _ready_context() -> WorkflowContext:
    return WorkflowContext(
        created_by="pytest",
        ticket=TicketData(id="APPROVE-READY-1", title="Ready Approval"),
        automation={
            "TC001": AutomationBlock(
                test_case_id="TC001",
                robot_file="generated/robot/approve_ready_1/TC001_ready.robot",
                data_reference_check_passed=True,
                validation=AutomationValidation(
                    artifact_exists=True,
                    dry_run_passed=True,
                    validation_attempts=1,
                ),
            ),
            "TC002": AutomationBlock(
                test_case_id="TC002",
                robot_file="generated/robot/approve_ready_1/TC002_ready.robot",
                data_reference_check_passed=True,
                validation=AutomationValidation(
                    artifact_exists=True,
                    dry_run_passed=True,
                    validation_attempts=1,
                ),
            ),
        },
    )


def _blocked_context() -> WorkflowContext:
    context = _ready_context()
    context.automation["TC002"].validation.dry_run_passed = None
    context.automation["TC002"].validation.dry_run_skipped_reason = (
        "Robot Framework CLI is not installed"
    )
    return context


def test_human_approval_boundary_components_are_registered() -> None:
    assert agent_registry.has("HumanApprovalAgent") is True
    assert skill_registry.has("RequestHumanApprovalSkill") is True
    assert tool_registry.has("LocalHumanApprovalPolicyTool") is True

    agent_spec = agent_registry.get("HumanApprovalAgent").spec
    skill_spec = skill_registry.get("RequestHumanApprovalSkill").spec
    tool_spec = tool_registry.get("LocalHumanApprovalPolicyTool").spec

    assert agent_spec.skills == ("RequestHumanApprovalSkill",)
    assert skill_spec.tools == ("LocalHumanApprovalPolicyTool",)
    assert tool_spec.isolation == "process"


def test_human_approval_graph_node_preserves_ready_approval_behavior() -> None:
    context = _ready_context()
    context.approval = ApprovalBlock(comments=["Please keep this note."])

    context = run_human_approval(context)

    assert context.workflow_status == "pending_human_review"
    assert context.approval is not None
    assert context.approval.status == "pending_review"
    assert context.approval.requested_by == "pytest"
    assert context.approval.review_items == [
        "generated/robot/approve_ready_1/TC001_ready.robot",
        "generated/robot/approve_ready_1/TC002_ready.robot",
    ]
    assert context.approval.git_branch == "aegis/approve_ready_1"
    assert context.approval.git_pr_url is None
    assert context.approval.comments == ["Please keep this note."]
    assert context.approval.notes == [
        "Generated Robot files are validated and waiting for human review.",
        "Approval will attempt Git branch, commit, and PR creation.",
    ]

    assert context.audit_log[-1].event_type == "approval_requested"
    assert context.audit_log[-1].summary == (
        "Generated automation is ready for human approval."
    )
    assert context.audit_log[-1].metadata == {
        "review_item_count": 2,
        "git_branch": "aegis/approve_ready_1",
    }


def test_human_approval_graph_node_preserves_blocked_approval_behavior() -> None:
    context = _blocked_context()

    context = run_human_approval(context)

    assert context.workflow_status == "approval_blocked"
    assert context.approval is not None
    assert context.approval.status == "not_ready"
    assert context.approval.review_items == [
        "generated/robot/approve_ready_1/TC001_ready.robot"
    ]
    assert context.approval.git_branch is None
    assert context.approval.notes == [
        "One or more generated Robot files failed validation.",
        "Human review is blocked until validation passes.",
    ]
    assert context.audit_log[-1].event_type == "approval_requested"
    assert context.audit_log[-1].summary == (
        "Generated automation is not ready for human approval."
    )
    assert context.audit_log[-1].metadata == {"review_item_count": 1}


def test_human_approval_uses_context_id_when_ticket_is_missing() -> None:
    context = _ready_context()
    context.ticket = None
    context.context_id = "CONTEXT-FALLBACK-1"

    context = run_human_approval(context)

    assert context.approval is not None
    assert context.approval.git_branch == "aegis/context_fallback_1"


def test_human_approval_still_requires_automation() -> None:
    with pytest.raises(ValueError, match="HumanApproval requires context.automation"):
        run_human_approval(WorkflowContext(created_by="pytest"))
