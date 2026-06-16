from __future__ import annotations

import backend.tools.human_approval_policy  # Registers LocalHumanApprovalPolicyTool.
from backend.graph.state import ApprovalBlock, TestContext
from backend.skills.base import BaseSkill, skill_registry
from backend.tools.base import ToolRegistry, tool_registry as default_tool_registry


@skill_registry.register(
    name="RequestHumanApprovalSkill",
    tools=["LocalHumanApprovalPolicyTool"],
    description="Creates a human approval request from validated automation.",
)
class RequestHumanApprovalSkill(BaseSkill):
    def __init__(self, *, tool_registry: ToolRegistry | None = None) -> None:
        super().__init__(tool_registry=tool_registry or default_tool_registry)

    def execute(self, context: TestContext) -> TestContext:
        if not context.automation:
            raise ValueError("HumanApproval requires context.automation")

        previous_comments = context.approval.comments if context.approval else []
        ticket_id = context.ticket.id if context.ticket else context.context_id
        tool = self.tool_registry.create("LocalHumanApprovalPolicyTool")
        approval = tool.invoke(
            automation=context.automation,
            created_by=context.created_by,
            ticket_id=ticket_id,
            previous_comments=previous_comments,
        )
        if not isinstance(approval, ApprovalBlock):
            raise TypeError("Human approval tools must return ApprovalBlock")

        context.approval = approval
        if context.approval.status == "pending_review":
            context.record_event(
                actor="system",
                event_type="approval_requested",
                summary="Generated automation is ready for human approval.",
                metadata={
                    "review_item_count": len(context.approval.review_items),
                    "git_branch": context.approval.git_branch,
                },
            )
            context.mark("pending_human_review")
            return context

        context.record_event(
            actor="system",
            event_type="approval_requested",
            summary="Generated automation is not ready for human approval.",
            metadata={"review_item_count": len(context.approval.review_items)},
        )
        context.mark("approval_blocked")
        return context
