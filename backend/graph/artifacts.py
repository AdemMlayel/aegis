from __future__ import annotations

import re
from pathlib import Path

from backend.config.settings import settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ROOT = (
    Path(settings.generated_root).expanduser().resolve()
    if settings.generated_root
    else PROJECT_ROOT / "generated"
)
GENERATED_ROBOT_ROOT = GENERATED_ROOT / "robot"
GENERATED_CONTEXT_ROOT = GENERATED_ROOT / "contexts"
GENERATED_GIT_HANDOFF_ROOT = GENERATED_ROOT / "git_handoff"
GENERATED_AUDIT_ROOT = GENERATED_ROOT / "audit"
GENERATED_STORAGE_ROOT = GENERATED_ROOT / "storage"
GENERATED_EXECUTION_ROOT = GENERATED_ROOT / "execution"
GENERATED_MEMORY_ROOT = GENERATED_ROOT / "memory"
GENERATED_REPORT_PACKAGE_ROOT = GENERATED_ROOT / "report_packages"
GENERATED_ARTIFACT_ROOT = GENERATED_ROOT / "artifacts"
GENERATED_KNOWLEDGE_ROOT = GENERATED_ROOT / "knowledge"


def slug(value: str) -> str:
    slugged = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_").lower()
    return slugged or "untitled"


def relative_to_project(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def robot_output_dir(ticket_id: str) -> Path:
    return GENERATED_ROBOT_ROOT / slug(ticket_id)


def resolve_robot_file(ticket_id: str, file_name: str) -> Path:
    if Path(file_name).name != file_name:
        raise ValueError("Robot file names cannot include directory separators")
    if not file_name.endswith(".robot"):
        raise ValueError("Only .robot files can be read")

    root = GENERATED_ROBOT_ROOT.resolve()
    candidate = (robot_output_dir(ticket_id) / file_name).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("Robot file path escapes the generated artifact root") from exc
    return candidate


def execution_output_dir(context_id: str) -> Path:
    return GENERATED_EXECUTION_ROOT / slug(context_id)


def memory_output_dir() -> Path:
    return GENERATED_MEMORY_ROOT
