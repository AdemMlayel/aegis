# Milestone 8B — Conversational QA Copilot

## Summary

Milestone 8B adds a governed chatbot layer on top of the existing deterministic AegisQA workflow cockpit.

The chatbot does not replace the workflow engine. It acts as an interaction layer that can answer questions, explain state, and propose controlled actions. Actions that change state or trigger execution require explicit confirmation.

## Implemented backend modules

```text
backend/chat/
  __init__.py
  action_planner.py
  intent_classifier.py
  response_builder.py
  safety.py
  schemas.py
  service.py
  session_store.py
```

## Implemented API route

```text
backend/api/routes/chat.py
```

Registered in:

```text
backend/main.py
```

## New API endpoints

```text
POST /api/v1/chat/sessions
GET  /api/v1/chat/sessions/{session_id}
POST /api/v1/chat/sessions/{session_id}/messages
POST /api/v1/chat/sessions/{session_id}/actions/{action_id}/confirm
```

## Supported intent categories

```text
system_question
help
ticket_question
workflow_start
workflow_status
workflow_step
artifact_question
validation_question
approval_request
execution_request
investigation_question
report_request
knowledge_question
unknown
```

## Controlled chat actions

```text
start_workflow
resume_workflow
run_next_stage
approve_pending_stage
execute_workflow
```

All controlled actions are represented as explicit `ChatAction` objects and require confirmation before execution.

## Safety model

Read-only questions can be answered immediately:

```text
system status
provider status
ticket explanation
workflow status
artifact explanation
validation explanation
investigation summary
report summary
safe corpus grounding status
```

Controlled actions require confirmation:

```text
starting a workflow
running the next stage
approving a pending stage
executing tests
```

The chatbot never directly calls external company systems. It reuses the existing backend workflow and provider interfaces.

## Frontend changes

Added:

```text
frontend/src/components/CopilotPanel.tsx
```

Updated:

```text
frontend/src/api.ts
frontend/src/types.ts
frontend/src/App.tsx
frontend/src/styles.css
```

The frontend now includes a floating AegisQA Copilot panel with:

- message history
- quick suggestions
- user input
- confirmation buttons for controlled actions
- context-aware workflow linking

## Verification

```bash
python -m pytest -q
# 151 passed

python -m compileall -q backend scripts tests
# passed

cd frontend
npm ci
npm run build
# build successful
```

## Remaining 8B gaps

This is a strong first 8B implementation, but not the final conversational product. Remaining improvements:

1. Add persisted chat session listing endpoint.
2. Add richer artifact-specific Q&A with selected test case context.
3. Add request-changes actions from chat.
4. Add regenerate-stage action from chat.
5. Add full package approval action from chat.
6. Add multilingual intent examples.
7. Add stronger UI docking instead of only floating panel.
8. Add better streaming/typing UX.
9. Add more detailed source/evidence cards in chat responses.
10. Add chat evaluation tests.

## Architecture rule preserved

```text
Chatbot = interaction layer
Workflow engine = deterministic controller
Tools/providers = governed execution boundary
Human confirmation = required for controlled actions
```
