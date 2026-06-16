from __future__ import annotations

from typing import Any

from backend.graph.artifacts import slug
from backend.graph.state import ApprovalBlock, AutomationBlock, utc_now
from backend.tools.base import BaseTool, tool_registry


@tool_registry.register(
    name="LocalHumanApprovalPolicyTool",
    isolation="process",
    description="Builds deterministic human approval requests from validation results.",
)
class LocalHumanApprovalPolicyTool(BaseTool):
    def invoke(self, **kwargs: Any) -> ApprovalBlock:
        automation = kwargs.get("automation")
        created_by = kwargs.get("created_by")
        ticket_id = kwargs.get("ticket_id")
        previous_comments = kwargs.get("previous_comments")

        if not isinstance(automation, dict) or not all(
            isinstance(block, AutomationBlock) for block in automation.values()
        ):
            raise TypeError(
                "LocalHumanApprovalPolicyTool requires dict[str, AutomationBlock]"
            )
        if not isinstance(created_by, str) or not created_by.strip():
            raise TypeError("LocalHumanApprovalPolicyTool requires created_by")
        if not isinstance(ticket_id, str) or not ticket_id.strip():
            raise TypeError("LocalHumanApprovalPolicyTool requires ticket_id")
        if not isinstance(previous_comments, list) or not all(
            isinstance(comment, str) for comment in previous_comments
        ):
            raise TypeError(
                "LocalHumanApprovalPolicyTool requires list[str] previous_comments"
            )

        return plan_human_approval(
            automation=automation,
            created_by=created_by,
            ticket_id=ticket_id,
            previous_comments=previous_comments,
        )


def plan_human_approval(
    *,
    automation: dict[str, AutomationBlock],
    created_by: str,
    ticket_id: str,
    previous_comments: list[str],
) -> ApprovalBlock:
    review_items = [
        automation_block.robot_file
        for automation_block in automation.values()
        if automation_block.validation.dry_run_passed is True
    ]
    all_items_ready = len(review_items) == len(automation)

    if all_items_ready:
        return ApprovalBlock(
            status="pending_review",
            requested_at=utc_now(),
            requested_by=created_by,
            review_items=review_items,
            git_branch=f"aegis/{slug(ticket_id)}",
            git_pr_url=None,
            comments=previous_comments,
            notes=[
                "Generated Robot files are validated and waiting for human review.",
                "Approval will attempt Git branch, commit, and PR creation.",
            ],
        )

    return ApprovalBlock(
        status="not_ready",
        requested_at=utc_now(),
        requested_by=created_by,
        review_items=review_items,
        comments=previous_comments,
        notes=[
            "One or more generated Robot files failed validation.",
            "Human review is blocked until validation passes.",
        ],
    )
