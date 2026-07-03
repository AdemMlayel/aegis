# AegisQA Frontend UX & Chatbot Interaction Spec

Status: living design doc. Maps the desired chat-first operations workspace to the
**current code** so we build only the gaps, not what already exists.

Verdict up front: the foundation is largely built. The chatbot already classifies
intent across 18 labels, splits read vs. write, surfaces confirmation-gated action
cards, and records a structured per-step workflow trace. The two high-value gaps
are (1) an explicit "here's what I understood — continue?" confirmation message
before mutating actions, and (2) **live** streaming of the execution trace (today
it is polled, not pushed). This doc tracks both to done.

---

## 1. Chatbot role — the user gateway

Requirement: the chatbot is the first contact point; the user should not need to
understand backend agents/tools/workflows. It translates a request into an intent
and hands it to the orchestrator. Supports read and write/execute actions.

Current state — **MET.**
- Entry point: `POST /api/v1/chat/sessions/{id}/messages` → `chat/service.py::handle_chat_message`.
- Pipeline: `classify_chat_intent` → `plan_actions` → `build_assistant_response`
  → `ChatMessage{intent, actions, metadata}`.
- Read intents return prose only (`action_planner.is_read_only_intent` → `[]` actions).
  Write intents return confirmation-gated `ChatAction` cards.
- The orchestrator boundary is real: chat never calls agents directly; write
  actions go through `services/workflow_control` and `graph/workflow`.

No work needed.

---

## 2. Intent understanding & classification

Requirement: classify intent before sending to the orchestrator; display the
interpreted intent when useful, especially for complex actions.

Current state — **MOSTLY MET; one gap.**
- 18 intents in `chat/schemas.py::ChatIntent`. Mapping to the spec's categories:
  - Ticket information request → `ticket_question`
  - Requirement extraction → covered by `workflow_start` (requirement stage) +
    `show_stage_output` / `validation_question`
  - Test estimation → `test_case_suggestion` / coverage via `show_stage_output`
  - Test generation / automation generation → `workflow_start` / `workflow_step`
  - Robot Framework help → `knowledge_question` / `system_knowledge`
  - Test execution → `execution_request`
  - Failure analysis → `investigation_question`
  - Report generation → `report_request`
  - General/help → `help`
  - Configuration/model → `system_question`
- Scored deterministic classifier (`intent_classifier.py::_score_intents`) with
  `STRONG_SIGNALS` phrase weighting; optional LLM adjudication layer
  (`llm_intent.py`) that can only *rescue read-only intents* — it may never
  override into a mutating intent (W9 governance, Phase 4).
- The classified intent IS returned to the UI: `ChatMessage.intent` +
  `metadata.confidence`.

GAP (G1): the chatbot does not emit a natural-language "I understood that you
want to X. I'll ask the orchestrator to start the Y workflow." sentence before a
complex/mutating action. The data is present; the prose is not. → **Part B1.**

---

## 3. Orchestrator interaction

Requirement: after intent detection, the chatbot sends to the orchestrator, which
decides which agent/skill/tool handles it. Frontend never calls agents directly.

Current state — **MET.**
- `_execute_action` in `service.py` dispatches to `create_workflow_session`,
  `resume_workflow_session`, `review_workflow_stage`, `run_post_approval_workflow`.
- Agent/skill/tool selection is the orchestrator's job (`graph/workflow.py`
  node sequence), not the frontend's. The frontend only POSTs intents/confirms.

No work needed.

---

## 4. Visible execution trace in chat

Requirement: while processing, the user sees structured workflow updates (not
random text): current step, status, agent/tool, short description, timestamp/
duration. Should not feel like a black box.

Current state — **PARTIALLY MET; the core gap.**
- The data model is exactly right. `WorkflowEvent` (frontend `types.ts`, backed by
  `storage` timeline) carries `{sequence, kind, stage, status, actor, message,
  metadata, created_at}` — i.e. step + status + actor + description + timestamp.
- `App.tsx` already renders these into a timeline.
- BUT events are **polled after the fact** via `listWorkflowTimeline(context_id,
  cursor)` on an interval. There is no push channel, so the user sees stages
  appear in batches on the poll tick rather than a live "Calling Requirement
  Analysis Agent…" ticker as it happens.

GAP (G2): no live stream. → **Part B2** (Server-Sent Events endpoint +
EventSource client, with the existing poll as fallback).

---

## 5. Human-in-the-loop behavior

Requirement: for important actions, ask for approval before continuing (generate,
execute, overwrite, regenerate, save, close). Actions: Approve / Edit /
Regenerate / Continue / Stop / Ask a question.

Current state — **MET for the core gates; partial on the verb set.**
- Confirmation gating is real: every mutating `ChatAction` has
  `requires_confirmation=True` and `status="pending_confirmation"` until the user
  confirms via `/actions/{id}/confirm` (or cancels via `/cancel`).
- `ChatActionKind` covers start_workflow, run_next_stage, approve_pending_stage,
  execute_workflow.
- Approve / Continue (run next) / Stop (cancel) all exist. Edit (artifact editing)
  exists in `ConversationWorkspace`. Regenerate exists (`regenerateWorkflowStage`).
- "Ask a question" is implicit (the user just types) rather than an explicit
  affordance on the action card.

Minor gap (G3, Suggestion): unify the approval verb set on the action card UI so
Approve/Edit/Regenerate/Continue/Stop/Ask are consistent affordances. Lower
priority than G1/G2.

---

## 6. Main frontend experience (chat-centered)

Requirement: dashboard centered on chat. Select ticket → view details → ask →
start workflow → track progress → review artifacts → approve/edit → execute →
review pass/fail → follow-up → final report. Chat combines conversation +
timeline + agent status + approval checkpoints + artifacts + results.

Current state — **MOSTLY MET; layout still split.**
- All the pieces exist: `WorkspaceNav` (ticket sidebar), `ConversationWorkspace`
  (chat + timeline + artifacts + validation/exec results + approvals),
  `CopilotPanel` (chat), `AgentRoster` (live agent/governance strip).
- Prior phases moved toward chat-first, but `CopilotPanel` and
  `ConversationWorkspace` still coexist as two surfaces rather than one unified
  primary column.

Gap (G4, Suggestion): consolidate to a single primary chat column that hosts the
conversation, inline timeline, approval cards, and artifact previews. Larger UX
refactor; sequence after G1/G2 land.

---

## 7. Example user flow → endpoint trace

The spec's 18-step flow maps cleanly onto existing endpoints:

1. Select ticket → `GET /tickets/demo`
2-4. Ask + intent → `POST /chat/.../messages` (`ticket_question` →
   `build_assistant_response`)
5-6. Progress + requirement summary → workflow events + `show_stage_output`
7-8. "How many tests" → `test_case_suggestion` / coverage stage output
9-11. "Generate automation" + approval → `workflow_start` action card → confirm
12-13. Generation trace + scripts → workflow events + artifact previews
14-17. "Continue with execution" + confirm → `execute_workflow` action → confirm
18. Results (total/passed/failed/failure detail/fixes/next) → `execution` +
   `investigation` blocks already returned in context.

So the flow is supported end-to-end today. What's missing is the *feel*: the
intent-echo sentence (G1) and the live ticker (G2).

---

## 8. Design requirement — understandable to non-technical, detailed for technical

The user should always know: what the chatbot understood, what the orchestrator is
doing, which agent/tool is active, what data is being read, what action is
performed, what needs approval, what result was produced.

Current state: 6 of 7 are already exposed (intent echo in payload, timeline,
agent roster, action cards, results). The missing piece is making "what the
chatbot understood" and "what the orchestrator is doing right now" *legible in the
conversation in real time* — exactly G1 + G2.

---

## Gap summary & build order

| ID | Gap | Severity | Plan |
|----|-----|----------|------|
| G1 | No interpreted-intent confirmation message before mutating actions | Warning | **Part B1 — now** |
| G2 | Execution trace is polled, not streamed live | Warning | **Part B2 — now** |
| G3 | Approval verb set not fully unified on action cards | Suggestion | later |
| G4 | Chat not yet a single unified primary column | Suggestion | later |

This pass implements **G1 and G2**. G3/G4 are UX refactors deferred to a
follow-up once the streaming + intent-echo behavior is validated live.
