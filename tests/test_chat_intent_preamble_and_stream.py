"""Part B regressions: interpreted-intent preamble (B1/G1) + live SSE trace (B2/G2)."""
from __future__ import annotations

import asyncio
import json

from fastapi.testclient import TestClient

from backend.api.routes import workflow_control as wc
from backend.chat.intent_preamble import interpreted_intent_preamble
from backend.chat.schemas import ChatAction
from backend.main import app
from backend.storage.workflow_events import WorkflowEvent, append_workflow_event


# --- B1: interpreted-intent confirmation preamble ------------------------- #
def test_preamble_none_when_no_confirmable_actions() -> None:
    assert interpreted_intent_preamble([]) is None
    blocked = ChatAction(
        kind="start_workflow",
        label="x",
        description="y",
        requires_confirmation=False,
    )
    assert interpreted_intent_preamble([blocked]) is None


def test_preamble_text_for_each_mutating_kind() -> None:
    for kind, fragment in [
        ("start_workflow", "start the QA automation workflow"),
        ("run_next_stage", "advance the workflow"),
        ("approve_pending_stage", "approve the stage"),
        ("execute_workflow", "execute the approved tests"),
    ]:
        action = ChatAction(kind=kind, label="x", description="y")  # type: ignore[arg-type]
        text = interpreted_intent_preamble([action])
        assert text is not None
        assert fragment in text
        assert "confirm" in text.lower()


def test_chat_workflow_start_message_leads_with_interpreted_intent() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/chat/sessions",
        json={"created_by": "chat-tester", "ticket_id": "DEMO-TELCO-IMS-001"},
    )
    session_id = created.json()["session"]["session_id"]

    planned = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "actor": "chat-tester",
            "message": "Analyze this ticket",
            "ticket_id": "DEMO-TELCO-IMS-001",
        },
    )
    assert planned.status_code == 200
    assistant = planned.json()["message"]
    # The action is still planned and confirmation-gated...
    assert assistant["intent"] == "workflow_start"
    assert assistant["actions"][0]["kind"] == "start_workflow"
    # ...and the message now leads with the plain-language interpreted intent.
    assert "I understood that you want to" in assistant["content"]
    assert "start the QA automation workflow" in assistant["content"]


def test_read_only_message_has_no_preamble() -> None:
    client = TestClient(app)
    created = client.post("/api/v1/chat/sessions", json={"created_by": "chat-tester"})
    session_id = created.json()["session"]["session_id"]
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"actor": "chat-tester", "message": "what are the workflow stages"},
    )
    body = response.json()["message"]
    assert body["actions"] == []
    assert "I understood that you want to" not in body["content"]


# --- B2: SSE live trace --------------------------------------------------- #
def test_sse_pack_formats_event_record() -> None:
    event = WorkflowEvent(
        sequence=7,
        id="evt-1",
        context_id="ctx-1",
        kind="stage",
        stage="requirements",
        status="completed",
        actor="system",
        message="Requirements extracted",
        created_at=__import__("backend.graph.state", fromlist=["utc_now"]).utc_now(),
    )
    record = wc._sse_pack(event)
    assert record.startswith("id: 7\n")
    assert "event: workflow_event\n" in record
    assert record.endswith("\n\n")
    # The data line round-trips to the same event.
    data_line = [ln for ln in record.splitlines() if ln.startswith("data: ")][0]
    payload = json.loads(data_line[len("data: ") :])
    assert payload["sequence"] == 7
    assert payload["message"] == "Requirements extracted"


def test_event_stream_emits_backlog_then_closes_on_terminal() -> None:
    context_id = "sse-ctx-terminal"
    append_workflow_event(
        context_id=context_id,
        kind="stage",
        actor="system",
        message="stage ran",
        stage="requirements",
        status="completed",
    )
    append_workflow_event(
        context_id=context_id,
        kind="control",
        actor="system",
        message="workflow finished",
        status="completed",
    )

    class _FakeRequest:
        async def is_disconnected(self) -> bool:
            return False

    async def _collect() -> list[str]:
        chunks: list[str] = []
        async for chunk in wc._workflow_event_stream(context_id, _FakeRequest(), 0):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(asyncio.wait_for(_collect(), timeout=5))
    joined = "".join(chunks)
    # Both backlog events stream, then a terminal control event ends the stream.
    assert "stage ran" in joined
    assert "workflow finished" in joined
    assert "event: stream_end" in joined


def test_event_stream_stops_immediately_when_client_disconnected() -> None:
    class _GoneRequest:
        async def is_disconnected(self) -> bool:
            return True

    async def _collect() -> list[str]:
        chunks: list[str] = []
        async for chunk in wc._workflow_event_stream("any-ctx", _GoneRequest(), 0):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(asyncio.wait_for(_collect(), timeout=5))
    # Only the initial retry hint is emitted before the disconnect check returns.
    assert chunks == ["retry: 1500\n\n"]
