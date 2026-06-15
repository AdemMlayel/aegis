from backend.graph.artifacts import slug
from backend.graph.state import ApprovalBlock, TestContext, utc_now


def human_approval(context: TestContext) -> TestContext:
    if not context.automation:
        raise ValueError("HumanApproval requires context.automation")

    review_items = [
        automation.robot_file
        for automation in context.automation.values()
        if automation.validation.dry_run_passed is True
    ]
    all_items_ready = len(review_items) == len(context.automation)

    if all_items_ready:
        ticket_id = context.ticket.id if context.ticket else context.context_id
        context.approval = ApprovalBlock(
            status="pending_review",
            requested_at=utc_now(),
            requested_by=context.created_by,
            review_items=review_items,
            git_branch=f"aegis/{slug(ticket_id)}",
            git_pr_url=None,
            notes=[
                "Generated Robot files are validated and waiting for human review.",
                "Approval will attempt Git branch, commit, and PR creation.",
            ],
        )
        context.record_event(
            actor="system",
            event_type="approval_requested",
            summary="Generated automation is ready for human approval.",
            metadata={
                "review_item_count": len(review_items),
                "git_branch": context.approval.git_branch,
            },
        )
        context.mark("pending_human_review")
        return context

    context.approval = ApprovalBlock(
        status="not_ready",
        requested_at=utc_now(),
        requested_by=context.created_by,
        review_items=review_items,
        notes=[
            "One or more generated Robot files failed validation.",
            "Human review is blocked until validation passes.",
        ],
    )
    context.record_event(
        actor="system",
        event_type="approval_requested",
        summary="Generated automation is not ready for human approval.",
        metadata={"review_item_count": len(review_items)},
    )
    context.mark("approval_blocked")
    return context
