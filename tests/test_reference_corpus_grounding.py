from __future__ import annotations

import json
from pathlib import Path

from backend.reference_corpus.profiles import (
    load_execution_evidence_profile,
    load_report_profile,
    load_robot_keyword_registry,
    load_robot_style_profile,
    load_ticket_profile,
)
from backend.robot_libraries.registry import list_robot_keyword_capabilities
from backend.tools import tool_registry
from scripts.generate_reference_corpus_profiles import generate_reference_profiles
from scripts.package_clean import should_skip
from scripts.sanitize_sensitive_data_repo import sanitize_sensitive_repo


def test_clean_package_excludes_quarantined_sensitive_inputs() -> None:
    assert should_skip(Path("aegis-sensitive-data/custom_libs/raw.py")) is True
    assert should_skip(Path("data/SANITIZATION_MANIFEST.json")) is True
    assert should_skip(Path("fixtures/reference_corpus/raw_sanitized/robot-tests/demo.robot")) is False
    assert should_skip(Path("fixtures/reference_corpus/normalized/robot_keywords/keyword_registry.json")) is False


def test_reference_profiles_are_generated_from_sanitized_corpus() -> None:
    summary = generate_reference_profiles()

    assert summary["summary"]["robot_keywords"] > 0
    assert summary["summary"]["robot_style_files"] >= 5
    assert "report_files" in summary["summary"]
    assert "execution_artifacts" in summary["summary"]
    assert "ticket_files" in summary["summary"]

    registry_path = Path("fixtures/reference_corpus/normalized/robot_keywords/keyword_registry.json")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry["safety"]["imports_executed"] is False
    assert registry["summary"]["keyword_count"] == summary["summary"]["robot_keywords"]
    ticket_path = Path("fixtures/reference_corpus/normalized/ticket_profile/profile.json")
    ticket_profile = json.loads(ticket_path.read_text(encoding="utf-8"))
    assert ticket_profile["schema_version"] == "aegis-ticket-profile.v1"


def test_reference_profile_loaders_expose_normalized_metadata() -> None:
    keyword_registry = load_robot_keyword_registry()
    style_profile = load_robot_style_profile()
    report_profile = load_report_profile()
    execution_profile = load_execution_evidence_profile()
    ticket_profile = load_ticket_profile()

    assert keyword_registry["summary"]["keyword_count"] > 0
    assert style_profile["summary"]["robot_files"] >= 5
    assert "report_files" in report_profile["summary"]
    assert "has_successful_example" in execution_profile["summary"]
    assert "ticket_files" in ticket_profile["summary"]


def test_robot_keyword_tool_can_expose_sanitized_corpus_keywords() -> None:
    approved_only = list_robot_keyword_capabilities(domain="telecom_trace")
    with_corpus = list_robot_keyword_capabilities(
        domain="telecom_trace",
        include_corpus=True,
    )
    assert len(with_corpus) >= len(approved_only)

    tool = tool_registry.create("RobotKeywordCapabilityTool")
    capabilities = tool.invoke(domain="telecom_trace")
    assert len(capabilities) >= len(approved_only)


def test_sanitizer_default_target_is_reference_corpus(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    for folder in ("custom_libs", "robot", "output", "success", "fail", "LLD"):
        (source_root / folder).mkdir(parents=True)
    (source_root / "robot" / "Sensitive.robot").write_text(
        "*** Test Cases ***\nSensitive\n    Log    http://internal.example.test\n",
        encoding="utf-8",
    )
    target_root = tmp_path / "fixtures" / "reference_corpus" / "raw_sanitized"

    manifest = sanitize_sensitive_repo(source_root=source_root, target_root=target_root)

    assert target_root.name == "raw_sanitized"
    assert (target_root / "robot-tests" / "robot_test_001.robot").exists()
    assert (target_root / "ticket-examples").is_dir()
    assert manifest["summary"]["files"] == 1
    sanitized = (target_root / "robot-tests" / "robot_test_001.robot").read_text(
        encoding="utf-8"
    )
    assert "http://internal.example.test" not in sanitized
    assert "URL_PLACEHOLDER" in sanitized
