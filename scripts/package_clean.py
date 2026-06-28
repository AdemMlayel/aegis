from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {
    ".git",
    ".pytest_cache",
    ".pytest_tmp",
    ".ruff_cache",
    ".tools",
    ".venv",
    ".incoming_robot_libs",
    "__pycache__",
    "custom_libs",
    "node_modules",
    "dist",
    "generated",
    "aegisqa.egg-info",
    "aegis-sensitive-data",
    "data",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_FILES = {".env", "lld.docx"}


def should_skip(path: Path) -> bool:
    return (
        path.name in EXCLUDE_FILES
        or any(part in EXCLUDE_DIRS for part in path.parts)
        or path.suffix in EXCLUDE_SUFFIXES
    )


def default_target() -> Path:
    candidate = ROOT.parent / "aegisqa-clean"
    if candidate.resolve() == ROOT.resolve():
        return ROOT.parent / "aegisqa-clean-package"
    return candidate


def copy_clean(target: Path) -> None:
    target = target.resolve()
    if target == ROOT.resolve() or ROOT.resolve() in target.parents:
        raise ValueError("Clean package target must be outside the source tree")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for source in ROOT.rglob("*"):
        rel = source.relative_to(ROOT)
        if should_skip(rel) or source == target or target in source.parents:
            continue
        destination = target / rel
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a clean AegisQA source package.")
    parser.add_argument("target", nargs="?", type=Path, default=default_target())
    args = parser.parse_args()
    copy_clean(args.target)
    print(f"Clean package written to {args.target.resolve()}")
