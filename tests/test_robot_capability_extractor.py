import json
import shutil
from pathlib import Path

import pytest

from scripts.extract_robot_capabilities import (
    PROJECT_ROOT,
    REDACTED,
    extract_capability_report,
    write_capability_report,
)


@pytest.fixture
def workspace_tmp(request: pytest.FixtureRequest) -> Path:
    root = (
        PROJECT_ROOT
        / "generated"
        / "test-runtime"
        / "robot-capability-extractor"
        / request.node.name
    )
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def test_extract_python_capabilities_without_importing_source(
    workspace_tmp: Path,
) -> None:
    source_root = workspace_tmp / "custom_libs"
    source_root.mkdir()
    (source_root / "TraceLibrary.py").write_text(
        '''
"""Module docstring with TOKEN_PLACEHOLDER."""

raise RuntimeError("this module must never be imported")


class TraceLibrary:
    """Safe telecom trace helper."""

    def validate_header(self, message, header="Call-ID", token="TOKEN_PLACEHOLDER"):
        """Validate a sanitized header."""
        return True

    def _private_helper(self):
        return False


def public_helper(path, password="PASSWORD_PLACEHOLDER"):
    """Helper with sensitive default metadata."""
    return path
''',
        encoding="utf-8",
    )

    report = extract_capability_report(source_root)

    python_file = report["files"][0]
    assert python_file["status"] == "ok"
    assert python_file["module_docstring"] == REDACTED
    assert python_file["classes"][0]["name"] == "TraceLibrary"
    assert python_file["classes"][0]["docstring"] == "Safe telecom trace helper."

    method = python_file["classes"][0]["methods"][0]
    assert method["name"] == "validate_header"
    assert [arg["name"] for arg in method["args"]] == [
        "message",
        "header",
        "token",
    ]
    assert method["args"][1]["default"] == "'Call-ID'"
    assert method["args"][2]["default"] == REDACTED
    assert all(
        method["name"] != "_private_helper"
        for method in python_file["classes"][0]["methods"]
    )

    function = python_file["functions"][0]
    assert function["name"] == "public_helper"
    assert function["args"][1]["default"] == REDACTED


def test_extract_robot_keyword_capabilities(workspace_tmp: Path) -> None:
    source_root = workspace_tmp / "custom_libs"
    source_root.mkdir()
    (source_root / "trace_keywords.robot").write_text(
        """*** Settings ***
Library    BuiltIn

*** Keywords ***
Validate SIP Header
    [Documentation]    Uses TOKEN_PLACEHOLDER only.
    [Arguments]    ${message}    ${header}=Call-ID    ${token}=TOKEN_PLACEHOLDER
    Log    ${message}

Validate Diameter Session
    [Arguments]    ${request}    ${answer}
    Log    ${request}
""",
        encoding="utf-8",
    )

    report = extract_capability_report(source_root)

    robot_file = report["files"][0]
    assert robot_file["type"] == "robot"
    assert robot_file["keywords"][0]["name"] == "Validate SIP Header"
    assert robot_file["keywords"][0]["docstring"] == REDACTED
    assert robot_file["keywords"][0]["args"] == [
        {"name": "${message}", "kind": "robot_argument", "default": None},
        {"name": "${header}", "kind": "robot_argument", "default": "Call-ID"},
        {"name": "${token}", "kind": "robot_argument", "default": REDACTED},
    ]
    assert robot_file["keywords"][1]["name"] == "Validate Diameter Session"


def test_extract_report_summarizes_parse_errors(workspace_tmp: Path) -> None:
    source_root = workspace_tmp / "custom_libs"
    source_root.mkdir()
    (source_root / "broken.py").write_text("def broken(:\n", encoding="utf-8")

    report = extract_capability_report(source_root)

    assert report["summary"]["parse_errors"] == 1
    assert report["files"][0]["status"] == "parse_error"
    assert report["files"][0]["classes"] == []


def test_write_capability_report_defaults_to_generated_only(
    workspace_tmp: Path,
) -> None:
    report = {"schema_version": "robot-capability-extraction.v1"}

    outside_generated = PROJECT_ROOT / "capabilities.json"
    with pytest.raises(ValueError, match="generated"):
        write_capability_report(report, outside_generated)

    output = workspace_tmp / "robot_capabilities" / "capabilities.json"
    written = write_capability_report(
        report,
        output,
        enforce_generated_output=False,
    )

    assert json.loads(written.read_text(encoding="utf-8")) == report
