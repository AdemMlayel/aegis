# Current Blueprint Gap Analysis

## Overall status

AegisQA is a strong local architecture proof aligned with the approved blueprint. The full ticket → requirements → coverage → test cases → automation → validation → approval → execution → investigation → report → memory pipeline is real, runs end to end, and has been verified against a real self-hosted LLM (Nemotron-70B via vLLM) with zero silent fallback to the mock provider.

Estimated state:

- Local architecture-proof readiness: high — 300 passing tests, ruff clean, frontend builds clean.
- Reasoning-layer soundness: the heuristic↔LLM boundary is reconciled by a traceable adjudication layer (requirements and coverage), investigation confidence is a deterministic weighted-signal score, and all four LLM stages share a schema-derived JSON output contract verified to parse against the live model.
- Full enterprise blueprint compliance: partial, pending company providers and production infrastructure.

The remaining frontier is deliberate and known: every generated test currently asserts over resolved test data and expected-outcome strings — there is **no real system under test wired yet**. The pipeline genuinely runs and validates; it does not yet exercise a live application. That SUT wiring is the next phase, intentionally deferred until the reasoning core is solid.

## Implemented blueprint areas (code-verified)

| Blueprint area | Current status |
|---|---|
| FastAPI gateway | Implemented locally with governance middleware |
| React dashboard | Implemented, chat-first cockpit with live agent roster and chat sessions; builds clean (tsc + vite) |
| Agent → Skill → Tool boundary | Implemented (physically separate packages) |
| Tool registry | Implemented with typed results and audit metadata |
| Workflow graph | Implemented with validation retry, approval, execution, investigation, memory, reporting |
| Requirement/Coverage/TestCase/TestData agents | Implemented — deterministic heuristics + optional real-LLM drafting, reconciled by an adjudication layer (never stapled) |
| Adjudication layer (heuristic vs grounded-LLM) | Implemented for requirements and coverage — grounding gates, traceable per-decision notes, confidence blends shown line-by-line |
| Structured LLM output contract | Implemented — schema-derived JSON contract injected into all four prompts; verified 4/4 live-parse on Nemotron |
| Automation generation | Implemented — one case per derived requirement, real BuiltIn assertions, dry-run validated |
| Investigation | Implemented — deterministic weighted-signal evidence scorer, fully traceable `score = Σ(matched weights)/budget` |
| RAG | Implemented — seeded chunks + sanitized corpus + ingestion; **semantic token-bucketed** local embeddings, hybrid vector+lexical reranker; chat knowledge questions retrieve real chunks |
| Memory | Implemented locally with episodic archive/search |
| LLM provider abstraction | Implemented with mock, Ollama, OpenAI-compatible/vLLM boundaries; real Nemotron-70B verified end-to-end |
| Execution | Implemented through mock, local Robot (real subprocess + output.xml), and optional Docker Robot adapters |
| Self-Healing / Locator Repair Agent | Implemented — locator + keyword repair, similarity×stability scoring, human-gated (never auto-applies), grounded in the real keyword registry, chat-queryable |
| Conversational QA copilot | Implemented — scored intent classifier + optional LLM adjudication, show-stage-output, real RAG-backed knowledge answers |
| Observability/governance | Implemented as local in-memory/SQLite foundations |

## Remaining blueprint gaps

| Gap | Reason |
|---|---|
| Real system under test | No live application wired yet; generated tests assert over resolved data. This is the deliberate next phase. |
| Multi-signal investigation (network/HAR, DB snapshot, screenshots) | Deferred (Phase 3); scorer is ready for these signals when the inputs exist. |
| Memory-driven learning loop | Episodic store exists; similar-failure retrieval not yet wired into the investigation node. |
| Real Jira/Azure/GitLab connectors | Awaiting company API specs and credentials. |
| Enterprise SSO / JWT auth / RBAC at gateway | Capability model exists in code; **no auth middleware yet — the API is currently open.** Fine for local; must not reach a shared environment unguarded. |
| Production PostgreSQL | Adapter boundary exists; migrations/driver integration still future work. |
| Production vector DB + reranker (pgvector/Qdrant, ms-marco) | Local semantic vector path only. |
| Real Vault | Mock Vault-compatible interface only. |
| Enterprise CI/CD/CT | Tests/builds exist; enterprise pipeline not connected. |
| Agent simulation/optimizer, A2A protocol, agent registry DB | Not implemented; not needed for the current local proof. |

## Standing caveats (honesty notes)

- A few scoring constants are load-bearing and chosen by reasoning, not empirical calibration: the investigation `NORMALIZATION_WEIGHT` (93) and the adjudicator confidence blend weights (0.35 requirements, 0.30 coverage). They are traceable and documented in code, but "traceable to a hand-picked constant" is still a tuning judgment — calibrate or caveat before over-trusting the precise numbers.
- The semantic local embedding is a deterministic token-bucketed hash, not a learned model. It is a genuine improvement over the prior whole-text fingerprint (which produced anti-correlated vectors), but it is lexical-semantic, not contextual — a real embedding model (Ollama nomic-embed-text) is the production path.

## Current recommendation

Use the current state as a genuine architecture-and-reasoning proof: the brain is sound and provably so on controlled inputs. Do not claim real company integration readiness until provider contracts, credentials, and controlled environments are available — and state plainly that no live SUT is wired yet. The single highest-value next step is to connect one real system under test, which converts "the pipeline runs" into "the pipeline found a real defect."
