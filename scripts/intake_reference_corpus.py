#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.generate_reference_corpus_profiles import (
        DEFAULT_CORPUS_ROOT,
        NORMALIZED_DIR,
        RAW_DIR,
        generate_reference_profiles,
    )
    from scripts.sanitize_sensitive_data_repo import (
        DEFAULT_SOURCE_ROOT,
        sanitize_sensitive_repo,
    )
except ModuleNotFoundError:  # direct script execution
    from generate_reference_corpus_profiles import (  # type: ignore[no-redef]
        DEFAULT_CORPUS_ROOT,
        NORMALIZED_DIR,
        RAW_DIR,
        generate_reference_profiles,
    )
    from sanitize_sensitive_data_repo import (  # type: ignore[no-redef]
        DEFAULT_SOURCE_ROOT,
        sanitize_sensitive_repo,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = "INTAKE_SUMMARY.json"
TEXT_SUFFIXES = {
    ".cfg",
    ".conf",
    ".csv",
    ".html",
    ".ini",
    ".json",
    ".md",
    ".properties",
    ".py",
    ".robot",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
SAFETY_SCAN_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private_key_block",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
    ),
    ("url", re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE)),
    ("ipv4", re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),
    (
        "email",
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ),
    ("github_token", re.compile(r"\b(?:github_pat|ghp)_[A-Za-z0-9_]+\b", re.IGNORECASE)),
    ("api_key", re.compile(r"\bsk(?:-proj)?-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE)),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}\b")),
    ("windows_path", re.compile(r"\b[A-Za-z]:\\[^\s'\"<>]+")),
)


def run_reference_corpus_intake(
    *,
    source_root: Path = DEFAULT_SOURCE_ROOT,
    corpus_root: Path = DEFAULT_CORPUS_ROOT,
    clean: bool = False,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    corpus_root = corpus_root.resolve()
    raw_root = corpus_root / RAW_DIR

    inventory = inventory_quarantined_source(source_root)
    manifest = sanitize_sensitive_repo(
        source_root=source_root,
        target_root=raw_root,
        clean=clean,
    )
    safety_scan = scan_sanitized_tree(raw_root)

    if not safety_scan["passed"]:
        summary = _summary_payload(
            inventory=inventory,
            manifest=manifest,
            safety_scan=safety_scan,
            profiles_summary={},
            corpus_root=corpus_root,
        )
        _write_summary(corpus_root, summary)
        raise RuntimeError(
            "Sanitized corpus safety scan failed. See INTAKE_SUMMARY.json counts."
        )

    profiles_summary = generate_reference_profiles(corpus_root)
    summary = _summary_payload(
        inventory=inventory,
        manifest=manifest,
        safety_scan=safety_scan,
        profiles_summary=profiles_summary,
        corpus_root=corpus_root,
    )
    _write_summary(corpus_root, summary)
    return summary


def inventory_quarantined_source(source_root: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"Source folder does not exist: {source_root}")

    files = sorted(path for path in source_root.rglob("*") if path.is_file())
    dirs = sorted(path for path in source_root.rglob("*") if path.is_dir())
    extension_counts = Counter(_safe_extension(path) for path in files)
    top_level_dirs = sorted(path for path in source_root.iterdir() if path.is_dir())
    root_files = sorted(path for path in source_root.iterdir() if path.is_file())

    buckets: list[dict[str, Any]] = []
    for index, directory in enumerate(top_level_dirs, start=1):
        bucket_files = [path for path in directory.rglob("*") if path.is_file()]
        bucket_bytes = sum(path.stat().st_size for path in bucket_files)
        buckets.append(
            {
                "bucket": f"bucket_{index:03d}",
                "files": len(bucket_files),
                "dirs": sum(1 for path in directory.rglob("*") if path.is_dir()),
                "bytes": bucket_bytes,
                "extensions": dict(
                    sorted(
                        Counter(_safe_extension(path) for path in bucket_files).items()
                    )
                ),
            }
        )

    return {
        "schema_version": "aegis-quarantine-inventory.v1",
        "source": "quarantined_sensitive_reference",
        "raw_paths_preserved": False,
        "files": len(files),
        "dirs": len(dirs),
        "bytes": sum(path.stat().st_size for path in files),
        "extensions": dict(sorted(extension_counts.items())),
        "root_files": len(root_files),
        "buckets": buckets,
    }


def scan_sanitized_tree(root: Path) -> dict[str, Any]:
    root = root.resolve()
    findings: Counter[str] = Counter()
    files_scanned = 0
    if not root.is_dir():
        return {
            "schema_version": "aegis-sanitized-safety-scan.v1",
            "passed": False,
            "files_scanned": 0,
            "findings": {"missing_sanitized_root": 1},
        }

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        text = _read_scannable_text(path)
        if text is None:
            continue
        files_scanned += 1
        for name, pattern in SAFETY_SCAN_RULES:
            finding_count = _count_non_placeholder_matches(pattern, text)
            if finding_count:
                findings[name] += finding_count

    return {
        "schema_version": "aegis-sanitized-safety-scan.v1",
        "passed": not findings,
        "files_scanned": files_scanned,
        "findings": dict(sorted(findings.items())),
    }


def _summary_payload(
    *,
    inventory: dict[str, Any],
    manifest: dict[str, Any],
    safety_scan: dict[str, Any],
    profiles_summary: dict[str, Any],
    corpus_root: Path,
) -> dict[str, Any]:
    manifest_summary = manifest.get("summary", {})
    profile_summary = profiles_summary.get("summary", {})
    return {
        "schema_version": "aegis-reference-corpus-intake.v1",
        "generated_at": _generated_at(),
        "source": "quarantined_sensitive_reference",
        "corpus_root": _safe_repo_path(corpus_root),
        "raw_sensitive_inputs_committed": False,
        "runtime_agents_read_quarantine": False,
        "steps": {
            "inventory": inventory,
            "sanitization": manifest_summary,
            "safety_scan": safety_scan,
            "normalization": profile_summary,
        },
        "outputs": {
            "raw_sanitized": _safe_repo_path(corpus_root / RAW_DIR),
            "normalized": _safe_repo_path(corpus_root / NORMALIZED_DIR),
            "intake_summary": _safe_repo_path(corpus_root / SUMMARY_PATH),
        },
    }


def _read_scannable_text(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES or suffix == "":
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".xlsx" and zipfile.is_zipfile(path):
        chunks: list[str] = []
        with zipfile.ZipFile(path, "r") as workbook:
            for name in workbook.namelist():
                if name.endswith((".xml", ".rels", ".txt")):
                    chunks.append(
                        workbook.read(name).decode("utf-8", errors="replace")
                    )
        return "\n".join(chunks)
    return None


def _count_non_placeholder_matches(pattern: re.Pattern[str], text: str) -> int:
    count = 0
    for match in pattern.finditer(text):
        rendered = match.group(0)
        if "PLACEHOLDER" in rendered or "REDACTED" in rendered:
            continue
        count += 1
    return count


def _safe_extension(path: Path) -> str:
    return path.suffix.lower() or "[none]"


def _write_summary(corpus_root: Path, payload: dict[str, Any]) -> None:
    corpus_root.mkdir(parents=True, exist_ok=True)
    (corpus_root / SUMMARY_PATH).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _safe_repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name


def _generated_at() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), tz=UTC).isoformat()
    return datetime(1970, 1, 1, tzinfo=UTC).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest quarantined AegisQA reference material into the sanitized "
            "reference corpus without exposing raw paths or values."
        )
    )
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove and recreate the sanitized corpus before intake.",
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Print metadata-only inventory without reading file contents.",
    )
    args = parser.parse_args()

    if args.scan_only:
        inventory = inventory_quarantined_source(args.source_root)
        print(json.dumps(inventory, indent=2, sort_keys=True))
        return 0

    try:
        summary = run_reference_corpus_intake(
            source_root=args.source_root,
            corpus_root=args.corpus_root,
            clean=args.clean,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should provide a safe summary.
        print(str(exc), file=sys.stderr)
        return 1

    steps = summary["steps"]
    print(f"Intake summary written to {(args.corpus_root / SUMMARY_PATH).resolve()}")
    print(
        "Sanitized "
        f"{steps['sanitization']['files']} files with "
        f"{steps['sanitization']['redactions']} redactions."
    )
    print(
        "Normalized profiles: "
        + json.dumps(steps["normalization"], sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
