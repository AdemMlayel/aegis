# ADR 0001 — Agent Governance Approach

- Status: Accepted
- Date: 2026-06-29
- Decision makers: AegisQA architecture
- Scope: How AegisQA governs multi-agent behavior (permissions, audit, model
  selection, token/context limits, redaction, safe execution, RBAC readiness)

## Context

AegisQA orchestrates a multi-agent QA workflow. The brief asked whether the project
should adopt an external agent-governance framework — for example the NVIDIA NeMo Agent
Toolkit, LangGraph governance patterns, or custom policy middleware — to strengthen
control over what agents and tools may do.

We evaluated the governance capabilities the project actually needs against what is
already implemented.

### Governance capabilities required

1. Agent/tool permission control
2. Tool execution audit
3. Model selection control
4. Context length monitoring
5. Token consumption monitoring
6. Prompt/version tracking
7. Redaction and sensitive-data protection
8. Human-readable orchestration trace
9. Safe execution boundaries
10. Deterministic demo mode
11. Role-based access readiness

### What already exists in the codebase

The backend already implements a native, lightweight governance layer:

| Capability | Implementation | Location |
|---|---|---|
| Agent/tool permission control | `AgentPolicyEngine` — per-agent allowed skills, allowed providers, skill→tool authorization chain | `backend/governance/policy.py` |
| Tool execution audit | Typed `ToolRegistry.execute` authorizes against policy, then records attempts, duration, input/output hashes | `backend/tools/base.py` |
| Model selection control | Provider allow-lists per agent policy; denial on out-of-policy provider | `backend/governance/policy.py` |
| Token / context monitoring | Token reservation/settlement, per-call / per-workflow / org-daily budgets | `backend/governance/tokens.py`, `backend/storage/token_governance.py` |
| Rate limiting & resilience | Gateway rate limiter + per-provider circuit breaker | `backend/governance/gateway.py` |
| Prompt/version tracking | Prompt registry with named, versioned templates; recorded on the trace | `backend/prompts/`, intelligence trace |
| Orchestration trace | Per-node `trace_node` start/complete/failed records | `backend/graph/workflow.py` |
| Safe execution boundaries | Tools never run from raw model output; model proposes, backend authorizes and executes | `backend/tools/base.py` |
| Deterministic demo mode | Selects mock LLM, local hash embeddings, mock execution, demo tickets | `backend/config/settings.py` |
| RBAC readiness | Capability-based roles (viewer / qa_engineer / qa_lead / admin); strict auth mode | `backend/security/rbac.py` |
| Redaction | Sanitized fixtures and placeholder-only corpus; sensitive-data sanitizer script | `scripts/sanitize_sensitive_data_repo.py`, fixtures |

In short, every required capability is already present in a form that is small,
auditable, and fits the current local/demo maturity.

## Options considered

### Option A — Adopt NVIDIA NeMo Agent Toolkit now

NeMo Agent Toolkit is a capable framework for building and governing agentic systems.
However:

- It is a heavy dependency to introduce into a project whose stated posture is a local
  architecture proof, not a production deployment.
- Its governance primitives substantially overlap what AegisQA already implements
  natively (permissions, audit, budgets). Adopting it now would mean either running two
  governance layers or rewriting working, tested code to fit the framework's model.
- It expands the dependency and supply-chain surface and the operational learning curve
  without closing a capability gap that exists today.
- The project's own gap analysis explicitly defers production infrastructure; a heavy
  governance framework belongs with that later phase, not now.

### Option B — Adopt LangGraph governance patterns more deeply

The workflow already uses a LangGraph-compatible sequential graph with per-node tracing
and a fallback when LangGraph is absent. Leaning harder on LangGraph-native checkpointing
and interrupts could help once human-in-the-loop and durable resumption become
requirements. This is a natural future step but not required to meet current needs, and
it does not replace the policy/budget/audit layer already in place.

### Option C — Keep and document the existing custom governance layer (chosen)

Treat the existing native layer as the governance approach for this stage. It already
covers all eleven required capabilities, is fully under our control, is tested by the
existing suite, and adds no external dependency. Close small gaps incrementally.

## Decision

**Adopt Option C.** Do not integrate NeMo Agent Toolkit at this stage. The existing
native governance layer (policy engine + typed tool registry + token gateway + RBAC +
deterministic demo mode + orchestration trace) is the right approach for the current
maturity. We document it as the system of record and make its rules retrievable through
the RAG corpus so the assistant can explain them.

This is a reversible decision. The policy engine and tool registry present clear
boundaries; if production scale later justifies an external framework, those boundaries
are the integration seams.

## Minimal, justified implementation in this pass

Because the layer already exists, the work in this pass is consolidation and verification
rather than new framework integration:

- Documented the governance rules as a retrievable synthetic knowledge document
  (`fixtures/knowledge/governance/governance_and_safety_rules.md`).
- Confirmed the skill→tool authorization path denies ungoverned or out-of-policy tool
  calls (covered by the existing governance/observability boundary tests).
- Recorded this ADR so the decision and its rationale are explicit and auditable.

No new runtime dependency was added.

## Future path

Revisit an external governance toolkit (NeMo or equivalent) only when one of these
triggers occurs:

1. Real external system integration begins (live connectors, production credentials).
2. Durable, resumable human-in-the-loop workflows become a hard requirement
   (favor deeper LangGraph checkpointing/interrupts first).
3. Multi-tenant production scale requires centralized policy distribution and an agent
   registry database.

Until then, the native layer is sufficient, smaller, and fully auditable.

## Consequences

- Positive: no new heavy dependency; full control and auditability; all required
  capabilities met today; clear future seams.
- Negative: governance features are bespoke, so the team owns their maintenance and must
  keep this ADR and the governance knowledge document in sync with the code.
