from __future__ import annotations

from backend.memory.base import EpisodicMemoryEntry, EpisodicMemoryStore

SEEDED_MEMORY_ENTRIES = [
    EpisodicMemoryEntry(
        memory_id="MEM-BANK-TRANSFER-001",
        title="Previous money transfer regression failure",
        summary=(
            "A previous transfer workflow passed the UI success message but failed to update the balance ledger. "
            "Regression coverage should verify source balance, target balance, audit record, and duplicate submission handling."
        ),
        tags=("banking", "payments", "transfer", "regression", "balance"),
        source_refs=("local://memory/money-transfer-regression.json",),
        outcome="failed",
    ),
    EpisodicMemoryEntry(
        memory_id="MEM-API-AUTH-001",
        title="API authorization negative-path lesson",
        summary=(
            "Authorization defects were previously missed when only valid sessions were tested. "
            "Include expired token, missing token, insufficient role, and malformed payload checks."
        ),
        tags=("api", "authorization", "negative", "security"),
        source_refs=("local://memory/api-authorization-negative-path.json",),
        outcome="failed",
    ),
    EpisodicMemoryEntry(
        memory_id="MEM-ROBOT-VALIDATION-001",
        title="Robot import validation issue",
        summary=(
            "Generated Robot suites previously failed because resource imports were not validated before review. "
            "Validation should confirm imports, keyword references, data references, and dry-run syntax."
        ),
        tags=("robot", "automation", "validation"),
        source_refs=("local://memory/robot-import-validation.json",),
        outcome="failed",
    ),
]

_memory_stores: dict[tuple[str, str | None], EpisodicMemoryStore] = {
    ("default", None): EpisodicMemoryStore(entries=list(SEEDED_MEMORY_ENTRIES)),
}


def get_local_memory_store(
    *,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
) -> EpisodicMemoryStore:
    if embedding_provider is None:
        return _memory_stores[("default", None)]
    key = (embedding_provider, embedding_model)
    if key not in _memory_stores:
        _memory_stores[key] = EpisodicMemoryStore(
            entries=list(SEEDED_MEMORY_ENTRIES),
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
        )
    return _memory_stores[key]
