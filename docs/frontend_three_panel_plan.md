# Frontend Three-Panel Plan (Deferred Work)

This document is the plan and scaffolding guide for the three-panel interface described in
the hardening brief (section 3). It was intentionally **deferred** in the backend-and-below
hardening pass so the most verifiable work (cleanup, synthetic data, RAG, governance,
docs) could land first. This file is the hand-off for the next pass.

## Key finding: this is a refactor, not a rewrite

The current frontend already implements most of what the brief asks for. Inventorying
`frontend/src` against the brief:

| Brief panel | Already present | Component |
|---|---|---|
| Left — sessions/tickets | Partial | `WorkspaceNav` (ticket + workflow list, search, filter) |
| Middle — chat + orchestration | Yes | `ConversationWorkspace`, `CopilotPanel`, live `listWorkflowTimeline` polling, `RobotArtifactViewer` |
| Right — agents/config/governance | Yes | `AgentConfigPanel` (per-agent model routing, governance catalog, token budget, provider health) |

The backend already exposes every endpoint the three panels need — there is **no missing
backend work** for this UI:

- `listDemoTickets`, `listWorkflows`, `getWorkflow` — session/ticket history
- `createChatSession`, `sendChatMessage`, `createWorkflowSession` — chat + ticket-linked sessions
- `listWorkflowTimeline` — orchestration trace (already polled every ~2.2s)
- `listExecutionRuns`, `listExecutionEvents` — execution results
- `getAgentGovernanceCatalog`, `getAgentModelProfiles` — agents + per-agent model selection
- `getTokenBudgetStatus`, `getObservabilitySummary`, `getOperationalHealth` — governance/usage

So the remaining work is **structural**: split `App.tsx` (currently ~850 lines) into the
three-panel component tree the brief names, relabel for clarity, and add explicit session
history. It is not a green-field build.

## Target component tree

```
App
├── LeftPanel
│   ├── SessionHistory        # chat sessions, newest first
│   ├── TicketHistory         # demo tickets, selectable
│   └── NewSessionButton      # start chat / start ticket-linked workflow
├── ChatGateway (middle)
│   ├── MessageList           # assistant + user turns (from CopilotPanel)
│   ├── PromptInput
│   ├── OrchestrationTimeline # from listWorkflowTimeline (exists)
│   └── ToolExecutionCard     # per tool/agent step status
└── RightPanel
    ├── AgentMonitor          # agent list + active/idle status
    ├── AgentConfigPanel      # per-agent model selection (exists)
    ├── GovernancePanel       # permissions, audit indicators (catalog exists)
    ├── TokenUsagePanel       # token budget status (exists)
    └── SessionContextPanel   # current context summary, max-context usage
```

## Progress log

This pass made low-risk clarity improvements toward the three-panel target, verified by
isolated `tsc` parse-checks (full type-check/build still requires `npm install`, which is
blocked in the authoring sandbox):

- Left panel: `WorkspaceNav` now groups the list into **Sessions** (workflow runs) and
  **Tickets (no session yet)** with labeled headers and counts, so ticket-based vs.
  standalone items are visually distinct. Added a `kind` discriminator to the workspace
  item model and matching CSS (`.workspace-group`, `.workspace-group-label`).
- Middle panel: added a labeled `.panel-banner` header ("Assistant gateway &
  orchestration") above the center column that also shows the active session id + status,
  or "No active session" when idle.
- Both edits parse clean under `tsc` (no TS1xxx syntax errors); remaining LSP noise is
  only missing React types from the absent `node_modules`.

Remaining phases (F1 full extraction into `LeftPanel`/`ChatGateway`/`RightPanel`
wrappers, F2 session linkage, F3 orchestration polish, F4 build verification) are still
open and should be done where `npm run build` can run.

## Phased plan

### Phase F1 — Extract panels (no behavior change)
1. Move the left-rail JSX out of `App.tsx` into `LeftPanel` wrapping the existing
   `WorkspaceNav`. Add a `SessionHistory` list backed by `listWorkflows` +
   chat sessions, with a clear visual split: chat sessions vs ticket-based sessions vs
   "New session".
2. Move the middle area into `ChatGateway` composing `MessageList`, `PromptInput`,
   `OrchestrationTimeline`, and `ToolExecutionCard`.
3. Move the right rail into `RightPanel` composing the existing `AgentConfigPanel` plus
   new thin `AgentMonitor`, `GovernancePanel`, `TokenUsagePanel`, `SessionContextPanel`
   sections (most data is already fetched in `refreshBootstrap`).
4. Keep all existing `api.ts` calls; centralize any stragglers there.

### Phase F2 — Session/ticket linkage
1. Selecting a ticket opens or creates a chat context bound to that ticket
   (`createChatSession({ ticket_id })` already supports this).
2. Persist and restore the active session (the app already stores
   `aegisqa:lastContextId` in localStorage).
3. Make the active ticket/session visually unambiguous (header chip + highlighted row).
4. Add empty states for "no sessions yet" and "no ticket selected".

### Phase F3 — Orchestration visibility polish
1. Render timeline events as typed steps: retrieving knowledge, analyzing ticket,
   calling tool, agent active, result generated — with success/warning/error styling.
2. Show per-tool execution cards using the audit metadata the backend already records.
3. Surface retrieved RAG citations inline when a chat answer used knowledge refs.

### Phase F4 — Verification
1. `npm run build` green (tsconfig already fixed to `moduleResolution: "Bundler"`).
2. Manual smoke: select ticket → start workflow → watch timeline → approve → execute →
   read report, all three panels updating live.
3. Type-check clean (`tsc --noEmit`).

## Constraints (unchanged from backend rules)

- Frontend calls backend APIs only; no direct external-system access.
- Do not expose sensitive internal data in any panel.
- Keep labels professional and consistent.
- No new heavy UI dependency without justification (current stack: React 19 + Vite +
  lucide-react only).

## Why deferred

The brief's section 3 is the highest-effort, highest-risk slice and depends on visual
judgment best done interactively. Everything it needs on the backend already exists and is
verified, so deferring it carries no hidden risk — it is a contained, well-scoped refactor
that can be executed in its own pass against this plan.
