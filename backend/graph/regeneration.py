from backend.graph import nodes
from backend.graph.state import TestContext


def regenerate_after_changes(context: TestContext, *, actor: str) -> TestContext:
    context = nodes.automation_generator(context)
    context = nodes.validator(context)
    context = nodes.human_approval(context)
    context.record_event(
        actor=actor,
        event_type="automation_regenerated",
        summary="Automation was regenerated after reviewer feedback.",
        metadata={
            "automation_revision": context.automation_revision,
            "review_item_count": len(context.approval.review_items)
            if context.approval
            else 0,
        },
    )
    return context
