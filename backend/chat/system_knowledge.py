"""Curated, code-accurate description of the AegisQA system itself.

This module lets the deterministic copilot answer conceptual "how does the
system work" questions — architecture, agents, workflow stages, governance,
knowledge/RAG, providers, and demo mode — without an LLM. Every fact here is
sourced from the actual implementation:

- Workflow stages: ``backend/graph/workflow.py`` (WORKFLOW_STAGE_SEQUENCE / NODE_SEQUENCE)
- Agents: ``backend/graph/nodes/`` and ``backend/governance/policy.py``
- Governance: ``backend/governance/`` and ``backend/tools/base.py``
- RAG/knowledge: ``backend/knowledge/`` and ``backend/intelligence/vector.py``
- Providers: ``backend/llm/``, ``backend/embeddings/``, ``backend/execution/``
- RBAC: ``backend/security/rbac.py``

Keep this in sync with the code. It is intentionally static and human-readable
so the copilot's system answers stay deterministic and auditable.
"""
from __future__ import annotations

# Each topic maps to a list of human-readable lines. ``overview`` is the default.
SYSTEM_KNOWLEDGE: dict[str, list[str]] = {
    "overview": [
        "AegisQA is a local/demo-ready, AI-native QA orchestration system. It drives a "
        "structured ticket through the full QA lifecycle and keeps every step auditable.",
        "Layered architecture: React dashboard -> FastAPI routes -> services -> workflow "
        "graph -> agents -> skills -> tools -> local provider (or future external provider).",
        "Core principle: the model proposes, the backend authorizes and executes, and a "
        "human confirms controlled actions. Nothing unsafe runs directly from model output.",
        "Ask me about: architecture, agents, workflow stages, governance, knowledge/RAG, "
        "providers, or demo mode.",
    ],
    "architecture": [
        "Architecture layers, top to bottom:",
        "- React dashboard: three-panel cockpit (sessions/tickets, chat + orchestration, agent config/governance).",
        "- FastAPI routes: typed API surface, capability-protected.",
        "- Services: coordinate persisted state around the workflow graph; they do not duplicate agent logic.",
        "- Workflow graph: a sequential, LangGraph-compatible node pipeline with per-node tracing.",
        "- Agents -> skills -> tools: each layer declares what the layer below it may do.",
        "- Providers: LLM, embedding, and execution providers behind stable interfaces.",
        "Persistence is local SQLite; generated artifacts live under a configurable generated root.",
    ],
    "agents": [
        "The workflow is realized by these agent/node roles (each traced individually):",
        "- load_ticket: ingests the structured ticket.",
        "- requirement_agent: parses the ticket into requirements + completeness checklist.",
        "- coverage_planner: plans coverage and risk rationale.",
        "- test_case_generator: produces functional, negative, and boundary cases.",
        "- test_data_resolver: declares and resolves sanitized test data with teardown.",
        "- automation_generator: emits Robot Framework artifacts.",
        "- validator + validation_retry_gate: dry-run validation with bounded retries.",
        "- human_approval: human-in-the-loop gate before execution.",
        "- execution_dispatcher: runs tests via the configured adapter.",
        "- investigation_coordinator: evidence-based failure analysis.",
        "- memory_archiver: archives the outcome for historical reference.",
        "- report_generator: technical report + executive summary.",
        "Each agent has a registered identity and policy (allowed skills, allowed providers, token budgets).",
    ],
    "workflow": [
        "The workflow runs eight ordered stages:",
        "1. ticket — load the structured ticket.",
        "2. requirements — analyze completeness and produce requirements.",
        "3. coverage — plan coverage tied to validation rules.",
        "4. tests — generate functional, negative, and boundary test cases.",
        "5. automation — generate Robot Framework artifacts.",
        "6. validation — dry-run validate; retry on failure (bounded), else flag for review.",
        "7. approval — human reviewer approves, requests changes, or blocks.",
        "8. report — execute, investigate, archive memory, and generate reports.",
        "Modes: autonomous, approval-required, and step-by-step. Controlled actions "
        "(start, run next stage, approve, execute) always require confirmation.",
    ],
    "governance": [
        "Governance is native to the backend (no external agent framework — see ADR 0001):",
        "- Agent/tool permissions: each agent policy declares allowed skills and providers; "
        "a skill may only call tools its execution context allows. Out-of-policy calls are denied.",
        "- Controlled tool execution: every tool call goes through the typed tool registry, "
        "which authorizes against policy, then records attempts, duration, and input/output hashes.",
        "- Model selection control: providers are restricted per agent policy.",
        "- Token/context monitoring: per-call, per-workflow, and org-daily token budgets with "
        "reservation/settlement; a gateway enforces rate limits and provider circuit breakers.",
        "- Redaction: sensitive values are sanitized to placeholders before reaching prompts.",
        "- RBAC: capability-based roles (viewer, qa_engineer, qa_lead, admin); strict auth mode available.",
    ],
    "knowledge": [
        "The knowledge/RAG layer grounds answers in a synthetic, sanitized corpus:",
        "- Documents under fixtures/knowledge are auto-ingested, chunked (~900 chars), and embedded.",
        "- Storage is a local in-memory vector store; retrieval combines vector similarity with "
        "a deterministic hybrid reranker (lexical overlap + tag match) and returns cited chunks.",
        "- Embeddings use a local Ollama model when available, falling back to deterministic "
        "local hash embeddings (used in demo mode and tests).",
        "- Separately, a sanitized reference corpus yields normalized profiles (Robot keywords, "
        "style, report, execution evidence) that the agents consume — raw sensitive input stays quarantined.",
        "Verify retrieval with: python scripts/verify_rag_corpus.py",
    ],
    "providers": [
        "Providers sit behind stable interfaces so local and future external backends are interchangeable:",
        "- LLM: mock_llm (deterministic), ollama (local), openai_compatible (external).",
        "- Embeddings: ollama_nomic_embed_text (local model) and local_hash_embeddings (deterministic fallback).",
        "- Execution: mock (deterministic), robot (local Robot CLI), robot_docker (optional Docker isolation).",
        "- Tickets: a local Jira-shaped demo source; the connector contract can be swapped for a real provider.",
        "Each agent's policy controls which providers it may use.",
    ],
    "demo_mode": [
        "Deterministic demo mode makes presentations reproducible without external services.",
        "Enable it with AEGISQA_DETERMINISTIC_DEMO_MODE=true. It selects:",
        "- LLM: mock_llm",
        "- Embeddings: local_hash_embeddings",
        "- Execution: mock",
        "- Ticket source: demo",
        "Use Ollama mode instead when the local chat and embedding models are installed.",
    ],
}

# Keyword routing to a sub-topic. First match wins; order matters (specific first).
TOPIC_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("workflow", ("workflow", "stage", "stages", "pipeline", "lifecycle", "steps")),
    ("agents", ("agent", "agents", "node", "nodes", "roles", "orchestrat")),
    ("governance", ("governance", "permission", "policy", "audit", "rbac", "role", "budget", "token", "safety", "guardrail")),
    ("knowledge", ("rag", "knowledge", "corpus", "embedding", "vector", "retrieval", "memory")),
    ("providers", ("provider", "providers", "llm", "model", "ollama", "execution adapter", "adapter")),
    ("demo_mode", ("demo mode", "deterministic", "demo", "presentation")),
    ("architecture", ("architecture", "design", "layer", "layers", "structure", "component", "elements", "overview", "how does the system", "what is aegis")),
]


def resolve_system_topic(normalized_message: str) -> str:
    """Pick the most relevant system-knowledge topic for a message."""
    for topic, needles in TOPIC_KEYWORDS:
        for needle in needles:
            if needle in normalized_message:
                return topic
    return "overview"


def system_knowledge_lines(topic: str) -> list[str]:
    return SYSTEM_KNOWLEDGE.get(topic, SYSTEM_KNOWLEDGE["overview"])


def system_topics() -> list[str]:
    return [topic for topic in SYSTEM_KNOWLEDGE if topic != "overview"]
