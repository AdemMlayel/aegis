from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "aegis-sensitive-data"
DEFAULT_TARGET_ROOT = PROJECT_ROOT / "fixtures" / "reference_corpus" / "raw_sanitized"
TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".conf",
    ".csv",
    ".html",
    ".ini",
    ".json",
    ".md",
    ".properties",
    ".ps1",
    ".py",
    ".robot",
    ".sh",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
SPREADSHEET_SUFFIXES = {".xlsx"}
GENERIC_SOURCE_NAME_ALLOWLIST = {
    "failed",
    "failure",
    "generic",
    "log",
    "mobile",
    "output",
    "report",
    "robot",
    "success",
    "test",
    "tests",
    "utility",
    "validation",
}


@dataclass(frozen=True)
class CorpusCategory:
    target_folder: str
    source_aliases: tuple[str, ...]
    file_prefix: str
    auto_kind: str | None = None
    include_root_files: bool = False


CATEGORY_SOURCES = (
    CorpusCategory(
        target_folder="custom-libs",
        source_aliases=(
            "custom_libs",
            "custom-libs",
            "custom libs",
            "custom libraries",
            "custom_libraries",
            "libs",
            "libraries",
            "keywords",
        ),
        file_prefix="custom_lib",
        auto_kind="python",
    ),
    CorpusCategory(
        target_folder="robot-tests",
        source_aliases=(
            "robot",
            "robot-tests",
            "robot_tests",
            "robot suites",
            "robot_suites",
            "test suites",
            "test_suites",
            "tests",
        ),
        file_prefix="robot_test",
        auto_kind="robot",
    ),
    CorpusCategory(
        target_folder="report-example",
        source_aliases=(
            "output",
            "report",
            "reports",
            "report-example",
            "report_example",
            "report examples",
            "report_examples",
        ),
        file_prefix="report_example",
        auto_kind="report",
    ),
    CorpusCategory(
        target_folder="successful-execution",
        source_aliases=(
            "success",
            "successful",
            "successful-execution",
            "successful_execution",
            "passed",
            "pass",
        ),
        file_prefix="successful_execution",
        auto_kind="robot_execution",
    ),
    CorpusCategory(
        target_folder="failed-execution",
        source_aliases=(
            "fail",
            "failed",
            "failure",
            "failed-execution",
            "failed_execution",
        ),
        file_prefix="failed_execution",
    ),
    CorpusCategory(
        target_folder="ticket-examples",
        source_aliases=(
            "tickets",
            "ticket",
            "test tickets",
            "test_tickets",
            "old test tickets",
            "old_test_tickets",
        ),
        file_prefix="ticket_example",
        auto_kind="ticket",
        include_root_files=True,
    ),
    CorpusCategory(
        target_folder="lld-examples",
        source_aliases=(
            "LLD",
            "lld",
            "lld examples",
            "lld_examples",
            "lld-examples",
        ),
        file_prefix="lld_example",
        auto_kind="lld",
    ),
)


@dataclass
class RedactionStats:
    counts: dict[str, int] = field(default_factory=dict)

    def add(self, name: str, count: int) -> None:
        if count:
            self.counts[name] = self.counts.get(name, 0) + count

    def merge(self, other: "RedactionStats") -> None:
        for name, count in other.counts.items():
            self.add(name, count)

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def _generated_at() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), tz=UTC).isoformat()
    return datetime(1970, 1, 1, tzinfo=UTC).isoformat()


REDACTION_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "private_key_block",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        "PRIVATE_KEY_PLACEHOLDER",
    ),
    (
        "url",
        re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE),
        "URL_PLACEHOLDER",
    ),
    (
        "ipv4",
        re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
        "IP_ADDRESS_PLACEHOLDER",
    ),
    (
        "email",
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        "EMAIL_PLACEHOLDER",
    ),
    (
        "windows_path",
        re.compile(r"\b[A-Za-z]:\\[^\s'\"<>]+"),
        "LOCAL_PATH_PLACEHOLDER",
    ),
    (
        "unix_path",
        re.compile(r"(?<![:\w])/[\w.-]+(?:/[\w.-]+)+"),
        "LOCAL_PATH_PLACEHOLDER",
    ),
    (
        "github_token",
        re.compile(r"\b(?:github_pat|ghp)_[A-Za-z0-9_]+\b", re.IGNORECASE),
        "TOKEN_PLACEHOLDER",
    ),
    (
        "api_key",
        re.compile(r"\bsk(?:-proj)?-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE),
        "API_KEY_PLACEHOLDER",
    ),
    (
        "bearer_token",
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}\b"),
        "Bearer TOKEN_PLACEHOLDER",
    ),
    (
        "long_hex_identifier",
        re.compile(r"\b[0-9a-fA-F]{16,}\b"),
        "HEX_IDENTIFIER_PLACEHOLDER",
    ),
    (
        "long_numeric_identifier",
        re.compile(r"\b\d{7,}\b"),
        "NUMERIC_IDENTIFIER_PLACEHOLDER",
    ),
    (
        "hostname",
        re.compile(r"\b[A-Za-z0-9][A-Za-z0-9-]{2,}(?:\.[A-Za-z0-9-]{2,}){1,}\b"),
        "HOSTNAME_PLACEHOLDER",
    ),
)

SENSITIVE_ASSIGNMENT_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "quoted_sensitive_assignment",
        re.compile(
            r"(?i)\b([A-Za-z_][A-Za-z0-9_]*(?:password|passwd|pwd|secret|token|"
            r"api[_-]?key|apikey|credential|authorization|bearer)[A-Za-z0-9_]*"
            r"\s*[:=]\s*)(['\"])(.*?)(\2)"
        ),
        r"\1\2VALUE_PLACEHOLDER\4",
    ),
    (
        "unquoted_sensitive_assignment",
        re.compile(
            r"(?i)\b([A-Za-z_][A-Za-z0-9_]*(?:password|passwd|pwd|secret|token|"
            r"api[_-]?key|apikey|credential|authorization|bearer)[A-Za-z0-9_]*"
            r"\s*[:=]\s*)([^\s,#)]+)"
        ),
        r"\1VALUE_PLACEHOLDER",
    ),
    (
        "robot_sensitive_argument",
        re.compile(
            r"(?i)(\$\{[^}]*?(?:password|passwd|pwd|secret|token|api[_-]?key|"
            r"credential|authorization|bearer)[^}]*\}\s{2,})([^\s]+)"
        ),
        r"\1VALUE_PLACEHOLDER",
    ),
)


def sanitize_sensitive_repo(
    *,
    source_root: Path = DEFAULT_SOURCE_ROOT,
    target_root: Path = DEFAULT_TARGET_ROOT,
    clean: bool = False,
) -> dict[str, object]:
    source_root = source_root.resolve()
    target_root = target_root.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"Source folder does not exist: {source_root}")
    _assert_safe_target(target_root)

    if target_root.exists():
        if not clean:
            raise FileExistsError(
                f"Target already exists: {target_root}. Use --clean to recreate it."
            )
        shutil.rmtree(target_root)
    target_root.mkdir(parents=True)

    manifest_entries: list[dict[str, object]] = []
    category_summaries: dict[str, dict[str, int]] = {}
    total_stats = RedactionStats()
    forbidden_terms = _forbidden_source_terms(source_root)

    used_sources: set[Path] = set()
    for category in CATEGORY_SOURCES:
        source_dirs = _source_dirs_for_category(source_root, category, used_sources)
        used_sources.update(path.resolve() for path in source_dirs)
        target_dir = target_root / category.target_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        entries = _sanitize_category(
            source_dirs=source_dirs,
            source_root=source_root,
            target_dir=target_dir,
            file_prefix=category.file_prefix,
            forbidden_terms=forbidden_terms,
        )
        for entry in entries:
            total_stats.merge(_stats_from_mapping(entry["redactions"]))
        manifest_entries.extend(entries)
        category_summaries[category.target_folder] = {
            "files": len(entries),
            "redactions": sum(
                int(entry["redaction_total"]) for entry in entries
            ),
        }
        _write_category_readme(target_dir, category.target_folder, len(entries))

    manifest = {
        "schema_version": "aegis-sanitized-data.v1",
        "generated_at": _generated_at(),
        "source": "quarantined_sensitive_reference",
        "target_layout": [category.target_folder for category in CATEGORY_SOURCES],
        "safety": {
            "raw_files_committed": False,
            "raw_values_preserved": False,
            "filenames_generalized": True,
            "original_paths_hashed": True,
            "binary_media_copied": False,
        },
        "summary": {
            "files": len(manifest_entries),
            "redactions": total_stats.total,
            "categories": category_summaries,
            "redaction_types": total_stats.counts,
        },
        "files": manifest_entries,
    }

    _write_json(target_root / "SANITIZATION_MANIFEST.json", manifest)
    _write_root_readme(target_root, manifest)
    return manifest


def _sanitize_category(
    *,
    source_dirs: Sequence[Path],
    source_root: Path,
    target_dir: Path,
    file_prefix: str,
    forbidden_terms: set[str],
) -> list[dict[str, object]]:
    if not source_dirs:
        return []

    entries: list[dict[str, object]] = []
    files = sorted(
        {
            path.resolve()
            for source_dir in source_dirs
            if source_dir.exists()
            for path in (
                source_dir.rglob("*") if source_dir.is_dir() else [source_dir]
            )
            if path.is_file()
        },
        key=lambda path: path.as_posix(),
    )
    for index, source_file in enumerate(files, start=1):
        suffix = source_file.suffix.lower() or ".txt"
        target_suffix = suffix if suffix in TEXT_SUFFIXES | SPREADSHEET_SUFFIXES else ".md"
        target_file = target_dir / f"{file_prefix}_{index:03d}{target_suffix}"
        redactions = RedactionStats()

        if suffix in TEXT_SUFFIXES:
            redactions = _sanitize_text_file(
                source_file,
                target_file,
                forbidden_terms=forbidden_terms,
            )
            output_type = "sanitized_text"
        elif suffix in SPREADSHEET_SUFFIXES:
            redactions = _sanitize_xlsx_file(
                source_file,
                target_file,
                forbidden_terms=forbidden_terms,
            )
            output_type = "sanitized_spreadsheet"
        else:
            redactions = RedactionStats({"binary_placeholder": 1})
            target_file.write_text(
                _binary_placeholder(source_file),
                encoding="utf-8",
            )
            output_type = "binary_placeholder"

        relative_source = source_file.relative_to(source_root).as_posix()
        entries.append(
            {
                "target_path": target_file.relative_to(target_dir.parents[0]).as_posix(),
                "source_path_hash": _hash_text(relative_source),
                "source_extension": suffix,
                "source_size_bytes": source_file.stat().st_size,
                "output_type": output_type,
                "redaction_total": redactions.total,
                "redactions": redactions.counts,
            }
        )

    return entries


def _source_dirs_for_category(
    source_root: Path,
    category: CorpusCategory,
    used_sources: set[Path],
) -> list[Path]:
    if not source_root.is_dir():
        return []

    normalized_aliases = {
        _normalize_source_name(alias) for alias in category.source_aliases
    }
    matches: list[Path] = []
    seen: set[Path] = set()
    for child in sorted(source_root.iterdir()):
        if not child.is_dir():
            continue
        normalized_name = _normalize_source_name(child.name)
        resolved = child.resolve()
        if resolved in used_sources:
            continue
        if normalized_name in normalized_aliases:
            if resolved not in seen:
                matches.append(child)
                seen.add(resolved)

    if category.auto_kind:
        for child in sorted(source_root.iterdir()):
            if not child.is_dir():
                continue
            resolved = child.resolve()
            if resolved in used_sources or resolved in seen:
                continue
            if _matches_auto_kind(child, category.auto_kind):
                matches.append(child)
                seen.add(resolved)

    if category.include_root_files:
        root_files = sorted(path for path in source_root.iterdir() if path.is_file())
        matches.extend(path for path in root_files if path.resolve() not in used_sources)
    return matches


def _normalize_source_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _matches_auto_kind(source_dir: Path, kind: str) -> bool:
    files = [path for path in source_dir.rglob("*") if path.is_file()]
    if not files:
        return False
    extensions = Counter(path.suffix.lower() or "[none]" for path in files)
    if kind == "python":
        return extensions[".py"] > 0
    if kind == "robot":
        return extensions[".robot"] > 0
    if kind == "robot_execution":
        return _looks_like_robot_execution_dir(source_dir)
    if kind == "report":
        report_extensions = {".html", ".htm", ".xml", ".xlsx", ".md", ".txt"}
        return (
            any(extension in report_extensions for extension in extensions)
            and not _looks_like_robot_execution_dir(source_dir)
            and not _looks_like_ticket_or_lld_dir(source_dir)
            and extensions[".py"] == 0
            and extensions[".robot"] == 0
        )
    if kind == "ticket":
        ticket_extensions = {".txt", ".md", ".xlsx", ".csv", "[none]"}
        return (
            any(extension in ticket_extensions for extension in extensions)
            and extensions[".py"] == 0
            and extensions[".robot"] == 0
            and not _looks_like_robot_execution_dir(source_dir)
        )
    if kind == "lld":
        return any(extension in {".md", ".txt", ".docx", ".pdf"} for extension in extensions)
    return False


def _looks_like_robot_execution_dir(source_dir: Path) -> bool:
    names = {path.name.lower() for path in source_dir.rglob("*") if path.is_file()}
    return "output.xml" in names and bool({"log.html", "report.html"} & names)


def _looks_like_ticket_or_lld_dir(source_dir: Path) -> bool:
    normalized_name = _normalize_source_name(source_dir.name)
    return any(term in normalized_name for term in ("ticket", "lld", "requirement"))


def _sanitize_text_file(
    source_file: Path,
    target_file: Path,
    *,
    forbidden_terms: set[str],
) -> RedactionStats:
    text = source_file.read_text(encoding="utf-8", errors="replace")
    sanitized, stats = sanitize_text(text, forbidden_terms=forbidden_terms)
    sanitized = _normalize_sanitized_text(sanitized)
    target_file.write_text(sanitized, encoding="utf-8")
    return stats


def _sanitize_xlsx_file(
    source_file: Path,
    target_file: Path,
    *,
    forbidden_terms: set[str],
) -> RedactionStats:
    stats = RedactionStats()
    if not zipfile.is_zipfile(source_file):
        target_file.with_suffix(".md").write_text(
            _binary_placeholder(source_file),
            encoding="utf-8",
        )
        stats.add("spreadsheet_placeholder", 1)
        return stats

    with zipfile.ZipFile(source_file, "r") as source_zip:
        with zipfile.ZipFile(target_file, "w", compression=zipfile.ZIP_DEFLATED) as target_zip:
            for item in source_zip.infolist():
                payload = source_zip.read(item.filename)
                if _xlsx_entry_is_text(item.filename):
                    text = payload.decode("utf-8", errors="replace")
                    sanitized, entry_stats = sanitize_text(
                        text,
                        forbidden_terms=forbidden_terms,
                    )
                    stats.merge(entry_stats)
                    target_zip.writestr(item, sanitized.encode("utf-8"))
                elif _xlsx_entry_is_media(item.filename):
                    stats.add("spreadsheet_media_removed", 1)
                    continue
                else:
                    target_zip.writestr(item, payload)
    return stats


def sanitize_text(
    value: str,
    *,
    forbidden_terms: set[str] | None = None,
) -> tuple[str, RedactionStats]:
    stats = RedactionStats()
    sanitized = value

    for name, pattern, replacement in SENSITIVE_ASSIGNMENT_RULES:
        sanitized, count = pattern.subn(replacement, sanitized)
        stats.add(name, count)

    for name, pattern, replacement in REDACTION_RULES:
        sanitized, count = pattern.subn(replacement, sanitized)
        stats.add(name, count)

    for term in sorted(forbidden_terms or set(), key=len, reverse=True):
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        sanitized, count = pattern.subn("SOURCE_NAME_PLACEHOLDER", sanitized)
        stats.add("source_name_reference", count)

    return sanitized, stats


def _normalize_sanitized_text(value: str) -> str:
    lines = [line.rstrip() for line in value.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + ("\n" if lines else "")


def _forbidden_source_terms(source_root: Path) -> set[str]:
    terms: set[str] = set()
    for source_file in source_root.rglob("*"):
        if not source_file.is_file() or ".git" in source_file.parts:
            continue
        stem = source_file.stem.strip()
        if (
            len(stem) >= 4
            and not stem.isdigit()
            and stem.lower() not in GENERIC_SOURCE_NAME_ALLOWLIST
        ):
            terms.update(_source_name_variants(stem))
    return terms


def _source_name_variants(stem: str) -> set[str]:
    variants = {stem}
    separators_normalized = re.sub(r"[_\-\s]+", " ", stem).strip()
    if separators_normalized:
        variants.add(separators_normalized)
        variants.add(separators_normalized.replace(" ", "_"))
        variants.add(separators_normalized.replace(" ", "-"))
        variants.add(separators_normalized.replace(" ", ""))
    return {variant for variant in variants if len(variant) >= 4}


def _xlsx_entry_is_text(name: str) -> bool:
    lowered = name.lower()
    return lowered.endswith((".xml", ".rels", ".txt", ".vml"))


def _xlsx_entry_is_media(name: str) -> bool:
    lowered = name.lower()
    return lowered.startswith("xl/media/")


def _binary_placeholder(source_file: Path) -> str:
    return (
        "# Sanitized Binary Placeholder\n\n"
        "The original binary file was not copied into this sanitized repo.\n"
        "Use this placeholder to preserve file inventory without exposing "
        "screenshots, captures, credentials, or customer data.\n\n"
        f"Source extension: `{source_file.suffix.lower() or '[none]'}`\n"
        f"Source size bytes: `{source_file.stat().st_size}`\n"
    )


def _write_root_readme(target_root: Path, manifest: dict[str, object]) -> None:
    summary = manifest["summary"]
    assert isinstance(summary, dict)
    target_root.joinpath("README.md").write_text(
        "\n".join(
            [
                "# Sanitized Aegis Data",
                "",
                "This repo contains sanitized reference material only.",
                "Raw sensitive files were not committed here.",
                "",
                "## Layout",
                "",
                "- `robot-tests/`: sanitized Robot test plans.",
                "- `custom-libs/`: sanitized custom library references.",
                "- `report-example/`: sanitized report artifact examples.",
                "- `successful-execution/`: sanitized successful execution artifacts.",
                "- `failed-execution/`: sanitized failed execution artifacts when available.",
                "- `ticket-examples/`: sanitized structured or semi-structured test tickets.",
                "- `lld-examples/`: sanitized low-level-design examples when available.",
                "",
                "## Safety",
                "",
                "- Original filenames are replaced with generic names.",
                "- Original paths are stored only as non-reversible hashes.",
                "- URLs, IP addresses, tokens, credential values, long identifiers, "
                "and local paths are replaced with placeholders.",
                "- Binary media from spreadsheets is not copied.",
                "",
                "## Manifest",
                "",
                "`SANITIZATION_MANIFEST.json` contains counts, target paths, "
                "source path hashes, and redaction totals.",
                "",
                "## Summary",
                "",
                f"- Files sanitized: `{summary['files']}`",
                f"- Redactions applied: `{summary['redactions']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_category_readme(target_dir: Path, folder_name: str, file_count: int) -> None:
    label = folder_name.replace("-", " ").title()
    target_dir.joinpath("README.md").write_text(
        "\n".join(
            [
                f"# {label}",
                "",
                "Sanitized files in this folder are safe reference material for AegisQA.",
                "Do not replace them with raw customer or infrastructure data.",
                "",
                f"Sanitized file count: `{file_count}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _stats_from_mapping(value: object) -> RedactionStats:
    stats = RedactionStats()
    if isinstance(value, dict):
        for name, count in value.items():
            if isinstance(name, str) and isinstance(count, int):
                stats.add(name, count)
    return stats


def _assert_safe_target(target_root: Path) -> None:
    project_root = PROJECT_ROOT.resolve()
    target_root.relative_to(project_root)
    forbidden = {
        project_root,
        DEFAULT_SOURCE_ROOT.resolve(),
        project_root / "backend",
        project_root / "frontend",
        project_root / "tests",
    }
    if target_root in forbidden:
        raise ValueError(f"Unsafe sanitization target: {target_root}")


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a sanitized, standalone data repo from quarantined inputs."
    )
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--target-root", type=Path, default=DEFAULT_TARGET_ROOT)
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove and recreate the target folder before sanitizing.",
    )
    args = parser.parse_args()

    manifest = sanitize_sensitive_repo(
        source_root=args.source_root,
        target_root=args.target_root,
        clean=args.clean,
    )
    summary = manifest["summary"]
    assert isinstance(summary, dict)
    print(f"Sanitized data repo written to {args.target_root.resolve()}")
    print(
        f"Sanitized {summary['files']} files with "
        f"{summary['redactions']} redactions."
    )


if __name__ == "__main__":
    main()
