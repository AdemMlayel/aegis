"""Interpreted-intent confirmation preamble (G1 / Part B1).

When the copilot plans a mutating action (start/advance/approve/execute), the
spec wants the assistant to first say, in plain language, what it understood and
what it will ask the orchestrator to do -- BEFORE the confirmation-gated action
card. This makes "what the chatbot understood" legible in the conversation
instead of only living in the message payload's `intent` field.

This is deterministic prose keyed off the already-decided ``ChatActionKind`` --
it does NOT re-interpret the message or change what action runs. It is a
transparency layer over the existing (governed, confirmation-gated) action plan,
so it cannot surface or trigger anything the planner did not already decide.
"""
from __future__ import annotations

from backend.chat.schemas import ChatAction

# Maps the decided action kind to (what-I-understood, what-I-will-ask-for).
# Phrased so a non-technical user understands the intent and a technical user
# sees which orchestrator step it maps to.
_PREAMBLE_BY_KIND: dict[str, str] = {
    "start_workflow": (
        "I understood that you want to start the QA automation workflow for this "
        "ticket. I'll ask the orchestrator to create an approval-required "
        "workflow session and run requirement analysis first."
    ),
    "run_next_stage": (
        "I understood that you want to advance the workflow. I'll ask the "
        "orchestrator to run the next stage and pause again at the stage "
        "boundary for your review."
    ),
    "approve_pending_stage": (
        "I understood that you want to approve the stage that is waiting for "
        "review. I'll ask the orchestrator to record your approval and unblock "
        "the next stage."
    ),
    "execute_workflow": (
        "I understood that you want to execute the approved tests. I'll ask the "
        "orchestrator to run them through the configured execution adapter and "
        "collect the results."
    ),
}


def interpreted_intent_preamble(actions: list[ChatAction]) -> str | None:
    """Return a plain-language confirmation preamble for planned mutating actions.

    Returns ``None`` when there is nothing to confirm (read-only turns, or a
    mutating intent that produced no actionable card -- e.g. missing context),
    so the caller leaves the normal deterministic answer untouched.

    When several actions are planned (rare), the first one drives the preamble;
    a trailing note mentions that more than one confirmation is queued.
    """
    confirmable = [a for a in actions if a.requires_confirmation]
    if not confirmable:
        return None
    primary = confirmable[0]
    base = _PREAMBLE_BY_KIND.get(primary.kind)
    if base is None:
        return None
    suffix = " Please confirm below to continue, or cancel to take no action."
    if len(confirmable) > 1:
        suffix = (
            f" Please confirm below to continue (one of {len(confirmable)} "
            "queued actions), or cancel to take no action."
        )
    return f"{base}{suffix}"
