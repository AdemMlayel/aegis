from __future__ import annotations

from backend.knowledge.base import KnowledgeChunk, KnowledgeStore

LOCAL_KNOWLEDGE_CHUNKS = [
    KnowledgeChunk(
        chunk_id="KB-QA-001",
        title="Requirement completeness checklist",
        source="local://knowledge/qa_requirement_rules.md",
        tags=("requirements", "qa", "checklist"),
        text=(
            "Requirements should identify the actor, preconditions, expected outcome, "
            "error handling, data constraints, and measurable performance expectations. "
            "Missing items should produce clarification questions before automation is promoted."
        ),
    ),
    KnowledgeChunk(
        chunk_id="KB-BANK-001",
        title="Banking and payment risk guidance",
        source="local://knowledge/banking_payment_risk.md",
        tags=("banking", "payments", "risk", "regression"),
        text=(
            "Money transfer, payment, and balance update workflows should be treated as high risk. "
            "Coverage should include success, rejected input, boundary values, audit trail, duplicate submission, "
            "and regression checks for balance consistency."
        ),
    ),
    KnowledgeChunk(
        chunk_id="KB-ROBOT-001",
        title="Robot Framework automation structure",
        source="local://knowledge/robot_structure.md",
        tags=("robot", "automation", "validation"),
        text=(
            "Generated Robot suites should separate test cases, reusable keywords/resources, and data references. "
            "Validation should check file existence, imports, keyword references, and dry-run syntax when Robot is available."
        ),
    ),
    KnowledgeChunk(
        chunk_id="KB-APPROVAL-001",
        title="Human approval gate policy",
        source="local://knowledge/human_approval_policy.md",
        tags=("approval", "governance", "audit"),
        text=(
            "Generated automation must remain in pending review until validation passes. Human reviewers should approve, "
            "request changes, or block execution before Git handoff or execution promotion."
        ),
    ),
    KnowledgeChunk(
        chunk_id="KB-API-001",
        title="API workflow QA guidance",
        source="local://knowledge/api_workflow_qa.md",
        tags=("api", "integration", "negative", "boundary"),
        text=(
            "API-focused stories should test authorization, request validation, idempotency, timeout handling, "
            "response schema compatibility, and side-effect rollback on failure."
        ),
    ),
]


def get_local_knowledge_store() -> KnowledgeStore:
    return KnowledgeStore(LOCAL_KNOWLEDGE_CHUNKS)
