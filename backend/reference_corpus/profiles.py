from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from backend.graph.artifacts import PROJECT_ROOT

CORPUS_ROOT = PROJECT_ROOT / "fixtures" / "reference_corpus"
NORMALIZED_ROOT = CORPUS_ROOT / "normalized"


def _load_json(relative_path: str) -> dict[str, Any]:
    path = NORMALIZED_ROOT / relative_path
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def load_robot_keyword_registry() -> dict[str, Any]:
    return _load_json("robot_keywords/keyword_registry.json")


@lru_cache(maxsize=1)
def load_robot_style_profile() -> dict[str, Any]:
    return _load_json("robot_style_profile/profile.json")


@lru_cache(maxsize=1)
def load_report_profile() -> dict[str, Any]:
    return _load_json("report_profile/profile.json")


@lru_cache(maxsize=1)
def load_execution_evidence_profile() -> dict[str, Any]:
    return _load_json("execution_evidence_profile/profile.json")


def profile_available(profile: dict[str, Any]) -> bool:
    summary = profile.get("summary")
    return isinstance(summary, dict) and any(bool(value) for value in summary.values())
