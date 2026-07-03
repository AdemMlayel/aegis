"""Tests for the show_stage_output chat intent and its render handlers.

Covers the bug where "show me the requirements so I can approve them" routed to
approval_request (and returned a canned "a human should inspect the output" line)
instead of actually rendering the stage artifact, and where naming a stage like
"do the coverage" fell through to the unknown/RAG fallback instead of running it.
"""
from __future__ import annotations

from unittest import mock

import pytest

from backend.chat import response_builder
from backend.chat.intent_classifier import classify_chat_intent
from backend.chat.response_builder import build_assistant_response
from backend.chat.schemas import ChatSession
from backend.graph.state import TestContext as WorkflowContext
from backend.graph.state import TicketData
from backend.graph.workflow import run_workflow


# --- Classifier routing --------------------------------------------------- #

@pytest.mark.parametrize(
    "message",
    [
        "Show me the requirement so I can approve them",
        "Show me the requirements so I can approve them",
        "show me the requirements",
        "show the requirements",
        "show me the coverage",
        "view the coverage",
        "show me the test cases",
        "show me the test case",
        "show me the stage output",
        "what did the stage produce",
    ],
)
def test_show_requests_route_to_show_stage_output(message: str) -> None:
    assert classify_chat_intent(message).intent == "show_stage_output"


@pytest.mark.parametrize(
    "message",
    [
        "Do the coverage",
        "do coverage",
        "run coverage",
        "run the coverage",
        "run the requirements stage",
        "run the validation",
        "do the report",
    ],
)
def test_named_stage_commands_route_to_workflow_step(message: str) -> None:
    assert classify_chat_intent(message).intent == "workflow_step"


def test_show_request_does_not_shadow_existing_intents() -> None:
    """The new intent must not steal action/approval/suggestion routing."""
    assert classify_chat_intent("approve requirements").intent == "approval_request"
    assert classify_chat_intent("approve it").intent == "approval_request"
    assert classify_chat_intent("run next stage").intent == "workflow_step"
    assert classify_chat_intent("continue").intent == "workflow_step"
    assert (
        classify_chat_intent("suggest test cases for this ticket").intent
        == "test_case_suggestion"
    )
    assert classify_chat_intent("what is the status").intent == "workflow_status"


# --- Render handlers ------------------------------------------------------- #

@pytest.fixture(scope="module")
def populated_context() -> WorkflowContext:
    """A real, fully-run workflow context with all stage artifacts populated."""
    return run_workflow(
        WorkflowContext(
            created_by="pytest",
            ticket=TicketData(
                id="FAKE-456",
                title="Money Transfer Feature",
                description="As an authenticated customer, I want to transfer money.",
                acceptance_criteria=[
                    "Transfer completes within 3 seconds",
                    "Balance updates immediately",
                ],
                priority="high",
                labels=["banking", "payments"],
            ),
        )
    )


def _respond(message: str, context: WorkflowContext) -> str:
    classified = classify_chat_intent(message)
    session = ChatSession(created_by="pytest", context_id=context.context_id)
    with mock.patch.object(response_builder, "load_context", return_value=context):
        return build_assistant_response(session=session, classified=classified)


def test_show_requirements_renders_real_artifact(populated_context) -> None:
    out = _respond("show me the requirements", populated_context)
    assert "Requirements stage output:" in out
    analysis = populated_context.requirement_analysis
    assert analysis is not None
    # The real business action and domain must appear — not a canned message.
    assert analysis.business_action in out
    assert analysis.domain in out
    assert "Completeness checklist:" in out
    # Must NOT be the old canned approval deflection.
    assert "a human reviewer should inspect" not in out.lower()


def test_show_coverage_renders_real_artifact(populated_context) -> None:
    out = _respond("show me the coverage", populated_context)
    assert "Coverage stage output:" in out
    plan = populated_context.coverage_plan
    assert plan is not None
    assert plan.risk_level in out
    assert "Coverage matrix" in out


def test_show_test_cases_renders_real_artifact(populated_context) -> None:
    out = _respond("show me the test cases", populated_context)
    assert "Tests stage output" in out
    # At least one real generated test case id should be rendered.
    assert any(case.id in out for case in populated_context.test_cases)


def test_show_stage_output_without_context_is_actionable() -> None:
    classified = classify_chat_intent("show me the requirements")
    session = ChatSession(created_by="pytest")  # no context attached
    with mock.patch.object(response_builder, "load_context", return_value=None):
        out = build_assistant_response(session=session, classified=classified)
    assert "Open or start a workflow first" in out


def test_explicit_stage_keyword_overrides_pending_review(populated_context) -> None:
    """Asking for coverage explicitly renders coverage even if requirements is the
    most-recent / pending-review stage."""
    out = _respond("show me the coverage", populated_context)
    assert "Coverage stage output:" in out
    assert "Requirements stage output:" not in out
