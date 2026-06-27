from __future__ import annotations

import argparse
import ast
import json
import re
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "custom_libs"
DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT / "generated" / "robot_capabilities" / "extracted_capabilities.json"
)

CapabilityFileType = Literal["python", "robot"]
CapabilityStatus = Literal["ok", "parse_error"]
REDACTED = "[REDACTED]"
SENSITIVE_NAME_RE = re.compile(
    r"(password|passwd|pwd|secret|token|api[_-]?key|credential|authorization|bearer)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_RE = re.compile(
    r"("
    r"\b\d{1,3}(?:\.\d{1,3}){3}\b"
    r"|https?://\S+"
    r"|github_pat_[A-Za-z0-9_]+"
    r"|ghp_[A-Za-z0-9_]+"
    r"|sk-[A-Za-z0-9_-]+"
    r"|sk-proj-[A-Za-z0-9_-]+"
    r"|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    r")",
    re.IGNORECASE,
)


def extract_capability_report(source_root: Path) -> dict[str, Any]:
    root = source_root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Capability source root does not exist: {source_root}")

    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _should_skip(path):
            continue
        if path.suffix.lower() == ".py":
            files.append(_extract_python_file(path, root))
        elif path.suffix.lower() == ".robot":
            files.append(_extract_robot_file(path, root))

    summary = _summarize(files)
    return {
        "schema_version": "robot-capability-extraction.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_root": _safe_path(root),
        "safety": {
            "mode": "static_parse_only",
            "imports_executed": False,
            "runtime_code_executed": False,
            "raw_files_committed": False,
            "redaction": "docstrings_and_default_values",
        },
        "summary": summary,
        "files": files,
    }


def write_capability_report(
    report: dict[str, Any],
    output_path: Path,
    *,
    enforce_generated_output: bool = True,
) -> Path:
    resolved_output = output_path.resolve()
    if enforce_generated_output:
        generated_root = (PROJECT_ROOT / "generated").resolve()
        try:
            resolved_output.relative_to(generated_root)
        except ValueError as exc:
            raise ValueError("Capability report output must be under generated/") from exc

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return resolved_output


def _extract_python_file(path: Path, root: Path) -> dict[str, Any]:
    relative_path = path.relative_to(root).as_posix()
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            module = ast.parse(source, filename=relative_path)
    except SyntaxError as exc:
        return {
            "path": relative_path,
            "type": "python",
            "status": "parse_error",
            "error": _redact_text(str(exc)),
            "classes": [],
            "functions": [],
        }

    classes: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    for node in module.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            classes.append(_extract_class(node))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if not node.name.startswith("_"):
                functions.append(_extract_function(node))

    return {
        "path": relative_path,
        "type": "python",
        "status": "ok",
        "module_docstring": _redact_text(ast.get_docstring(module) or ""),
        "classes": classes,
        "functions": functions,
    }


def _extract_class(node: ast.ClassDef) -> dict[str, Any]:
    methods = [
        _extract_function(child)
        for child in node.body
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
        and not child.name.startswith("_")
    ]
    return {
        "name": node.name,
        "docstring": _redact_text(ast.get_docstring(node) or ""),
        "methods": methods,
    }


def _extract_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    return {
        "name": node.name,
        "async": isinstance(node, ast.AsyncFunctionDef),
        "docstring": _redact_text(ast.get_docstring(node) or ""),
        "args": _extract_python_args(node.args),
    }


def _extract_python_args(arguments: ast.arguments) -> list[dict[str, str | None]]:
    args: list[dict[str, str | None]] = []
    positional_args = [*arguments.posonlyargs, *arguments.args]
    positional_defaults = _defaults_by_arg(positional_args, arguments.defaults)
    for index, arg in enumerate(positional_args):
        if index == 0 and arg.arg in {"self", "cls"}:
            continue
        args.append(
            {
                "name": arg.arg,
                "kind": "positional",
                "default": _default_value(arg.arg, positional_defaults.get(arg.arg)),
            }
        )

    if arguments.vararg is not None:
        args.append(
            {
                "name": arguments.vararg.arg,
                "kind": "vararg",
                "default": None,
            }
        )

    for arg, default in zip(
        arguments.kwonlyargs,
        arguments.kw_defaults,
        strict=False,
    ):
        args.append(
            {
                "name": arg.arg,
                "kind": "keyword_only",
                "default": _default_value(arg.arg, default),
            }
        )

    if arguments.kwarg is not None:
        args.append(
            {
                "name": arguments.kwarg.arg,
                "kind": "kwarg",
                "default": None,
            }
        )

    return args


def _defaults_by_arg(
    args: list[ast.arg],
    defaults: list[ast.expr],
) -> dict[str, ast.expr]:
    default_args = args[-len(defaults) :] if defaults else []
    return {arg.arg: default for arg, default in zip(default_args, defaults, strict=True)}


def _default_value(name: str, value: ast.expr | None) -> str | None:
    if value is None:
        return None
    try:
        rendered = ast.unparse(value)
    except Exception:  # noqa: BLE001 - metadata extraction must be best effort.
        rendered = type(value).__name__
    if _is_sensitive_name(name) or _looks_sensitive(rendered):
        return REDACTED
    return _redact_text(rendered)


def _extract_robot_file(path: Path, root: Path) -> dict[str, Any]:
    relative_path = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    keywords: list[dict[str, Any]] = []
    current_keyword: dict[str, Any] | None = None
    in_keywords = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        section_name = _robot_section_name(stripped)
        if section_name is not None:
            in_keywords = section_name == "keywords"
            current_keyword = None
            continue
        if not in_keywords:
            continue

        if not raw_line.startswith((" ", "\t")):
            current_keyword = {
                "name": stripped,
                "docstring": "",
                "args": [],
            }
            keywords.append(current_keyword)
            continue

        if current_keyword is None:
            continue
        cells = _robot_cells(stripped)
        if not cells:
            continue
        setting = cells[0].strip().lower()
        if setting == "[arguments]":
            current_keyword["args"] = [_robot_arg(cell) for cell in cells[1:]]
        elif setting == "[documentation]":
            current_keyword["docstring"] = _redact_text(" ".join(cells[1:]))

    return {
        "path": relative_path,
        "type": "robot",
        "status": "ok",
        "keywords": keywords,
    }


def _robot_section_name(stripped_line: str) -> str | None:
    if not (stripped_line.startswith("***") and stripped_line.endswith("***")):
        return None
    return stripped_line.strip("* ").lower()


def _robot_cells(stripped_line: str) -> list[str]:
    if "    " in stripped_line:
        return [cell for cell in re.split(r" {2,}", stripped_line) if cell]
    return [cell for cell in stripped_line.split("\t") if cell]


def _robot_arg(cell: str) -> dict[str, str | None]:
    name, separator, default = cell.partition("=")
    normalized_name = name.strip()
    default_value = default.strip() if separator else None
    if default_value is not None and (
        _is_sensitive_name(normalized_name) or _looks_sensitive(default_value)
    ):
        default_value = REDACTED
    elif default_value is not None:
        default_value = _redact_text(default_value)
    return {
        "name": normalized_name,
        "kind": "robot_argument",
        "default": default_value,
    }


def _summarize(files: list[dict[str, Any]]) -> dict[str, int]:
    python_files = [file for file in files if file["type"] == "python"]
    robot_files = [file for file in files if file["type"] == "robot"]
    classes = sum(len(file.get("classes", [])) for file in python_files)
    methods = sum(
        len(class_info.get("methods", []))
        for file in python_files
        for class_info in file.get("classes", [])
    )
    functions = sum(len(file.get("functions", [])) for file in python_files)
    keywords = sum(len(file.get("keywords", [])) for file in robot_files)
    parse_errors = sum(1 for file in files if file["status"] == "parse_error")
    return {
        "python_files": len(python_files),
        "robot_files": len(robot_files),
        "classes": classes,
        "methods": methods,
        "functions": functions,
        "robot_keywords": keywords,
        "parse_errors": parse_errors,
    }


def _redact_text(value: str) -> str:
    if not value:
        return ""
    if _looks_sensitive(value):
        return REDACTED
    return value.strip()


def _looks_sensitive(value: str) -> bool:
    return bool(SENSITIVE_VALUE_RE.search(value) or SENSITIVE_NAME_RE.search(value))


def _is_sensitive_name(value: str) -> bool:
    return bool(SENSITIVE_NAME_RE.search(value))


def _should_skip(path: Path) -> bool:
    return any(part in {"__pycache__", ".git", ".venv"} for part in path.parts)


def _safe_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract review-only Robot/custom-library capability metadata "
            "without importing or executing source files."
        )
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
        help="Directory containing quarantined reference libraries.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Ignored generated JSON output path.",
    )
    args = parser.parse_args()

    report = extract_capability_report(args.source_root)
    output_path = write_capability_report(report, args.output)
    print(f"Capability metadata written to {output_path}")
    print(
        "Parsed "
        f"{report['summary']['python_files']} Python files and "
        f"{report['summary']['robot_files']} Robot files "
        "with static analysis only."
    )


if __name__ == "__main__":
    main()
