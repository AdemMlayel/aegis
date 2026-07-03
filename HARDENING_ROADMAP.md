# AegisQA Hardening Roadmap

Honest, code-verified review across six layers: **UX/UI, Orchestration, Chatbot,
Agents/Skills/Tools, Monitoring, Architecture.** Every finding cites real
`file:line`. Findings were produced by deep per-layer review and the two
highest-stakes claims were independently re-verified against source before
inclusion. Severity: **Critical** (trust/safety breaking) → **Warning**
(integrity/resilience) → **Suggestion** (robustness) → **Nitpick** (polish).

Goal: make the experience **trustworthy, fit-for-purpose, and easy to use** —
in that order. The single organizing principle: *the system must never present
degraded or unverified output as if it were real.*

---

## The one-paragraph verdict

The architecture is clean and the recent orchestrator hardening is genuinely
sound — the approval gate cannot be bypassed autonomously, governance
exceptions are correctly re-raised, and the deterministic scoring tools really
are LLM/RNG-free. But three things stand between this and "trustworthy":
(1) **silent mock fallback is invisible** — when a real LLM call fails the
system returns a deterministic mock as HTTP 200 with no log and no health
signal, so an operator sees "healthy" while 100% of output is fake;
(2) **auth is anonymous-admin by default** — permissive mode hands any caller a
QA_LEAD principal and strict mode trusts a spoofable `X-Aegis-Role` header,
which is a critical hole given the app was exposed over a public tunnel; and
(3) **the UI silently breaks/hangs** — no error boundary, no request timeouts,
all-or-nothing bootstrap. None are deep design flaws; all are containable with
the staged plan below.

---

## Severity tally

- **Critical (4):** M1 silent-fallback invisibility, M2 dishonest readiness,
  A1 default-permissive/spoofable auth, A2 no CORS.
- **Warning (12):** orchestration concurrency/recursion/retry-reset, ungoverned
  high-risk tool path, inert risk flags, UI resilience trio, chat actor
  spoofing + LLM-intent override, env-var override footgun, container-as-root.
- **Suggestion / Nitpick (remaining):** defense-in-depth + polish.

---

## CRITICAL — fix before any further exposure

### C1 (M1) — Silent mock fallback emits no log and no health signal
**`backend/intelligence/context.py:341-384`.** On any provider exception the
boundary builds a mock `LLMResponse(deterministic=True)` and returns it as a
**successful** call. It *is* persisted (`status="fallback"`,
`save_model_invocation` :404) and *is* counted in `/metrics`, but the fallback
site emits **zero** `log_event`/`logger` calls (grep-confirmed: no logging in
the module), `/health/ready` never probes the provider, and
`operational_health` (`backend/observability/health.py:63-123`) derives status
only from 5xx rate, agent-failure rate, and open circuits — none move on a
200 fallback. **This is the system's #1 trust risk made invisible.**
*Fix:* emit a WARNING log at the fallback site; add a dedicated
`aegisqa_model_fallback_total` counter; add a `mock_fallback` rate signal to
`operational_health` with a threshold; surface `fallback_from` to the UI
(see U-trust below).

### C2 (M2) — `/health/ready` doesn't check the LLM/embedding provider
**`backend/observability/health.py:17-60`.** Readiness checks only
`SELECT 1` + three numeric settings; it never calls the existing
`ollama_health()` (`backend/llm/ollama.py:85`). The compose healthcheck
(`docker-compose.yml:22`) hits this endpoint, so the container reports
**healthy while the model backend is down** (and therefore mock-falling-back).
*Fix:* when `default_llm_provider != "mock_llm"`, add a provider reachability
probe to readiness; fail-degrade (503) when unreachable.

### C3 (A1) — Default-permissive, header-spoofable auth = anonymous admin
**`backend/security/rbac.py:86-141`, `backend/config/settings.py:77`.** With
no auth headers and `AEGISQA_AUTH_MODE` unset (default `permissive`),
`get_current_principal` returns a hard-coded **QA_LEAD** holding
start/approve/execute/edit/read-audit. In `strict` mode it trusts
`X-Aegis-Role: admin` verbatim — no JWT, no signature, no proxy verification —
so any caller picks their own role. Given the recent public Cloudflare-tunnel
exposure, this is an exploitable anonymous-admin condition.
*Fix:* require real verified identity (JWT/mTLS/proxy-asserted header with a
shared secret) before role mapping; **refuse to start in permissive mode when
`environment != "local"`**; derive audited `actor` from the resolved principal,
never from request body.

### C4 (A2) — No CORS middleware on an unauthenticated API
**`backend/main.py:1-37`** (no `CORSMiddleware`). Combined with C3, a malicious
web page can drive state-changing POSTs (start/approve/execute workflow) from a
victim's browser. *Fix:* install `CORSMiddleware` with an explicit
frontend-origin allow-list; never `*` when exposed.

> **C3 + C4 + the spoofable rate-limit key (M-A3 below) are jointly an
> anonymous-admin-over-the-internet condition. Treat them as one gate.**

---

## WARNING — integrity & resilience

### Orchestration
- **W1 — No concurrency control on shared `context_id`.**
  `backend/storage/contexts.py:153` is a full-row UPSERT with no version/etag.
  `_run_stage` and the approval endpoint both load→mutate→save; two concurrent
  ops (resume + approve) are last-writer-wins and silently drop the loser.
  *Fix:* add a `row_version` column, conditional UPDATE, raise
  `WorkflowControlConflict` on mismatch.
- **W2 — TOCTOU double Git handoff.** `backend/api/routes/workflows.py:408`
  checks `status != "pending_review"`, then ~80 lines later runs
  `LocalGitHandoffTool` with no re-check/lock — two concurrent approvals both
  push/PR. *Fix:* guard with W1's conditional write; re-assert status
  immediately before handoff.
- **W3 — LangGraph recursion-limit divergence (active path crashes where the
  tested mental-model path wouldn't).** `backend/graph/workflow.py` invokes the
  compiled graph with no `config`, so LangGraph uses `recursion_limit=25`.
  `max_validation_retries` caps at `le=5` (`state.py:621`) → up to
  `13 + 5×3 = 28 > 25` → `GraphRecursionError`, raised *outside* `_invoke_node`
  so it carries no stage attribution. `SequentialWorkflow` has no such cap.
  *Fix:* pass `config={"recursion_limit": len(NODE_SEQUENCE) +
  max_validation_retries*3 + 5}`; catch `GraphRecursionError` and attribute it
  to the `validation` stage.
- **W4 — LangGraph silently discards pre-crash artifacts.** LangGraph copies
  state per super-step; on a node exception the outer `context` ref is the
  unmutated input, and `run_and_persist_workflow_start` persists *that* — so
  requirements/coverage/tests produced before the crash are lost. Sequential
  (mutate-by-reference) would keep them: a real behavioral divergence.
  *Fix:* attach a checkpointer or thread a shared mutable carrier; at minimum
  document it.
- **W5 — `validation_retry_count` is never reset → non-idempotent re-runs.**
  Incremented at `validation_retry_gate.py:38`, reset nowhere. After a
  `request_changes`→rerun or artifact edit, a context that previously exhausted
  retries enters validation already maxed and skips repair while still being
  marked completed. *Fix:* reset count (and `graph_iteration`) in
  `_invalidate_from_stage` and `_invalidate_after_artifact_edit`.

### Agents / Skills / Tools
- **W6 — High-risk tools run UN-authorized on the direct API path.**
  `backend/governance/policy.py:118-124 authorize_tool` returns silently when
  `execution is None`. The approval endpoint calls
  `tool_registry.execute("LocalGitHandoffTool", ...)` **outside any agent
  scope** → the highest-risk, state-changing tool runs with zero tool
  authorization. *Fix:* treat `execution is None` as **deny** for high-risk
  tools, or require state-changing tools to run inside a governed scope.
- **W7 — `risk_tier` / `require_human_approval` are inert metadata.**
  `backend/agents/base.py:32-34` flow into `AgentPolicy` but are never read at
  runtime — nothing blocks on them. `ValidatorAgent`/`AutomationGeneratorAgent`
  advertise `require_human_approval=True` but it does nothing. *Fix:* enforce
  in `governed_run`, or stop advertising it as a control.
- **W8 — Git handoff force-adds reviewer-controlled paths with no traversal
  re-check.** `backend/integrations/git_handoff.py:160` runs `git add -f --
  <review_items>` (bypasses `.gitignore`) without re-validating each item
  resolves inside `GENERATED_ROBOT_ROOT`. *Fix:* assert
  `.relative_to(GENERATED_ROBOT_ROOT)` per item before force-add.

### Chatbot
- **W9 — LLM intent classifier can override into a *mutating* intent.**
  `backend/chat/intent_classifier.py:463-472` trusts the LLM label (incl.
  `execution_request`, `approval_request`) at confidence ≥ 0.5 — contradicting
  `llm_intent.py`'s "classification only, never proposes actions." Still
  confirmation-gated, so no auto-execute, but a prompt-injected message can
  surface a destructive action card. *Fix:* intersect the LLM override with
  read-only intents; keep mutating intents rule-driven only.
- **W10 — Chat audit actor is unverified client input.**
  `backend/chat/service.py:243-253,307-317` record `append_audit_event(
  actor=actor, ...)` from the request body. *Fix:* derive from
  `principal.user_id` (couples with C3).

### UX/UI
- **W11 — No error boundary; any render throw white-screens the app.**
  `frontend/src/main.tsx:6-10` (zero `componentDidCatch`/
  `getDerivedStateFromError` in the tree). `ConversationWorkspace.tsx` is a
  1,655-line tree dereferencing deeply nested optionals. *Fix:* add an
  `ErrorBoundary` around `<App/>` + per-tab boundaries.
- **W12 — No request timeout; UI can hang on `busy` forever.**
  `frontend/src/api.ts` (no `AbortController`/`signal` anywhere). A hung
  backend pins the spinner and disables every control with no error. *Fix:*
  `AbortController` + 30s timeout in the fetch wrapper.
- **W13 — All-or-nothing bootstrap.** `frontend/src/App.tsx:287-360`
  `Promise.all([...12 calls...])` — one telemetry 500 blanks the entire
  dashboard (tickets, workflows, chat) even though they loaded. *Fix:*
  `Promise.allSettled` for the telemetry group; set each state slice
  independently.

---

## SUGGESTION — robustness (abbreviated; full list in review notes)

- **S1 (orchestration):** add a hard iteration ceiling to the `while True`
  validation loops (`workflow.py:150,394`) independent of the mutable counter.
- **S2:** mirror `_apply_honest_completion`'s evidence-gating in the manual
  `_run_stage` path (`workflow_control.py:523`) — it currently marks failed
  validation as a completed stage.
- **S3:** per-node timeout in `_invoke_node` (only leaf I/O is timed today).
- **S4 (tools):** scrub the Robot dry-run subprocess env
  (`tools/robot_validation.py:134 os.environ.copy()`) to PATH+PYTHONPATH only;
  secrets currently leak into the subprocess.
- **S5 (tools):** tool retry contract — add a `retryable_exceptions` allowlist
  so side-effecting tools can't double-write on retry
  (`tools/base.py:162-196`; latent — all tools use `max_retries=0` today).
- **S6 (chat):** apply the deterministic path's `_KNOWLEDGE_RELEVANCE_FLOOR`
  (0.33) to the LLM grounding retrieval (`chat/llm_responder.py:31-45`), which
  currently injects top-4 chunks with no floor.
- **S7 (monitoring):** rate-limit/quota key on authenticated principal + client
  IP, not spoofable headers (`observability/middleware.py:38-67`); add a global
  ceiling. (Pairs with C3.)
- **S8 (monitoring):** circuit breaker — add an explicit half-open single-probe
  instead of hard-reset-on-timeout (`governance/gateway.py:53-80`); don't count
  `CircuitOpenError` as a provider failure.
- **S9 (architecture):** `_load_local_env` uses `os.environ.setdefault`
  (`settings.py:10-31`) — a stray exported `AEGISQA_*` silently overrides
  `.env`. Log every shadowed key, or make `.env` authoritative.
- **S10 (architecture):** provider boundary footgun —
  `openai_compatible_context_window` defaults to `0` (clamp disabled), so a
  real vLLM call that exceeds context 400s → silent mock. Default a real window
  or refuse the external provider without one. Add
  `AEGISQA_ALLOW_MOCK_FALLBACK=false` to fail-closed.
- **S11 (deploy):** container runs as **root** with source bind-mounted and
  Redis unauthenticated (`Dockerfile`, `docker-compose.yml:18-20,44-46`).
  Non-root `USER`, drop bind-mount for non-dev, don't publish internal ports,
  password Redis.
- **S12 (UX trust):** surface intent + confidence on chat messages
  (`CopilotPanel.tsx:81-109` — data already present in `message.intent` /
  `message.metadata.confidence`); add a **MOCK/deterministic badge** when
  `call.deterministic === true` and a workspace banner when
  `configured_llm_provider !== llm_provider`
  (`ConversationWorkspace.tsx:1589`). *This is the UI half of C1.*
- **S13 (UX):** polling errors are swallowed (`App.tsx:153,184,427`
  `.catch(() => null)`) — add a "live updates paused" badge after N failures.
- **S14 (UX):** label heuristic confidence percentages as "heuristic score"
  (`ConversationWorkspace.tsx:603,1338,1436`) to match the backend's honest
  framing.

## NITPICK
- N1: honest-completion predicate treats `dry_run_passed is None` as pass
  (`workflow.py:282` — use `is True`).
- N2: self-healing `suggestion_id` uses salted builtin `hash()`
  (`tools/self_healing.py:149,232`) — not stable across processes; use
  `hashlib`.
- N3: data-resolver "teardown" strings are never executed
  (`tools/test_data_heuristics.py:35`) — wire them or drop the implied contract.
- N4: registry misses raise bare `KeyError`
  (`agents/base.py:179`, `skills/base.py:73`, `tools/base.py:106`) — raise the
  typed registration error; emit a failed audit record on tool-registry miss.
- N5: accessibility — chat input/send button lack `aria-label`; global error
  banner lacks `role="alert"` (`CopilotPanel.tsx:113-121`, `App.tsx:853`).
- N6: add `maxLength={10000}` to chat/workflow inputs (backend caps at 10k →
  oversized paste returns a raw 422).
- N7: broaden ruff selectors (`S`,`B`), commit a hash-pinned lockfile, add
  `pip-audit` to CI (`pyproject.toml`).

---

## Staged roadmap (sequence chosen by trust-impact × effort)

**Phase 1 — Trust floor (do first; small, high-impact).**
Make degradation impossible to hide and close the exposure hole.
- C1 silent-fallback log + metric + health signal
- C2 honest readiness (provider probe)
- C3 + C4 + S7 auth + CORS + non-spoofable rate key (the exposure gate)
- S12 UI: mock-vs-real badge + provider-mismatch banner (UI half of C1)
- S10 provider context-window default + `ALLOW_MOCK_FALLBACK=false`

**Phase 2 — Resilience floor (UI can't silently break/hang).**
- W11 error boundary, W12 request timeouts, W13 allSettled bootstrap
- S13 stale-data badge

**Phase 3 — Orchestration integrity.**
- W1 optimistic concurrency, W2 approval TOCTOU
- W3 recursion limit, W4 partial-artifact persistence, W5 retry-count reset
- S1/S2/N1 loop ceilings + honest manual-stage completion

**Phase 4 — Agent/tool governance & supply chain.**
- W6 deny ungoverned high-risk tools, W7 enforce/retire risk flags,
  W8 git traversal check, W9/W10 chat intent + actor, S4/S5 subprocess env +
  retry allowlist
- S11 deploy hardening, N7 supply chain

**Phase 5 — Polish. SHIPPED.** N2 process-stable suggestion ids (blake2b),
N3 teardown rendered as an executable `[Teardown]` clause (dry-run verified),
N4 typed registry-miss errors + tool-miss WARNING, N5 input aria-labels,
N6 `maxLength={10000}` on chat/workflow inputs, S14 "Heuristic confidence"
labels, S6 relevance floor on LLM grounding retrieval, S8 half-open
single-probe circuit breaker (open-circuit not counted as a provider failure).

Each phase is independently shippable and leaves the suite green
(**302 passed** baseline). Phase 1 alone moves the system from "looks healthy
while lying" to "tells you the truth about its own degradation" — the single
biggest trust win available.
