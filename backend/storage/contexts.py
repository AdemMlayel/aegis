from __future__ import annotations

from pathlib import Path

from backend.graph.artifacts import GENERATED_CONTEXT_ROOT
from backend.graph.state import TestContext


def _context_path(context_id: str) -> Path:
    return GENERATED_CONTEXT_ROOT / f"{context_id}.json"


def save_context(context: TestContext) -> Path:
    GENERATED_CONTEXT_ROOT.mkdir(parents=True, exist_ok=True)
    path = _context_path(context.context_id)
    path.write_text(context.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_context(context_id: str) -> TestContext | None:
    path = _context_path(context_id)
    if not path.is_file():
        return None
    return TestContext.model_validate_json(path.read_text(encoding="utf-8"))
