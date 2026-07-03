from __future__ import annotations

from pathlib import Path

from scripts.intake_reference_corpus import (
    inventory_quarantined_source,
    run_reference_corpus_intake,
    scan_sanitized_tree,
)


def test_reference_corpus_intake_sanitizes_and_generates_profiles(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "aegis-sensitive-data"
    corpus_root = tmp_path / "fixtures" / "reference_corpus"
    (source_root / "custom_libs").mkdir(parents=True)
    (source_root / "robot_suites").mkdir(parents=True)
    (source_root / "old_test_tickets").mkdir(parents=True)
    (source_root / "success").mkdir(parents=True)

    (source_root / "custom_libs" / "UnsafeLibrary.py").write_text(
        """
class UnsafeLibrary:
    def validate_event(self, endpoint="http://internal.example.test"):
        return endpoint
""",
        encoding="utf-8",
    )
    (source_root / "robot_suites" / "Unsafe.robot").write_text(
        """
*** Settings ***
Library    UnsafeLibrary.py

*** Test Cases ***
Validate Placeholder Flow
    [Tags]    smoke
    Validate Event    10.20.30.40
""",
        encoding="utf-8",
    )
    (source_root / "old_test_tickets" / "ticket.txt").write_text(
        """
Ticket ID: DEMO-1
Business objective: validate a safe demo workflow.
Test objective: generate Robot automation from a ticket.
Environment: http://ticket.example.test
Expected outputs: pass/fail report.
Validation rules: status must be passed.
Required tools: Robot Framework and Wireshark.
""",
        encoding="utf-8",
    )
    (source_root / "success" / "output.xml").write_text(
        '<robot><suite><test><status status="PASS"/></test></suite></robot>',
        encoding="utf-8",
    )

    summary = run_reference_corpus_intake(
        source_root=source_root,
        corpus_root=corpus_root,
    )

    assert summary["steps"]["sanitization"]["files"] == 4
    assert summary["steps"]["safety_scan"]["passed"] is True
    assert summary["steps"]["normalization"]["robot_keywords"] >= 1
    assert summary["steps"]["normalization"]["robot_style_files"] == 1
    assert summary["steps"]["normalization"]["ticket_files"] == 1
    assert (corpus_root / "INTAKE_SUMMARY.json").exists()
    assert (corpus_root / "normalized" / "ticket_profile" / "profile.json").exists()

    combined_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (corpus_root / "raw_sanitized").rglob("*")
        if path.is_file() and path.suffix.lower() != ".xlsx"
    )
    assert "http://internal.example.test" not in combined_text
    assert "10.20.30.40" not in combined_text
    assert "http://ticket.example.test" not in combined_text


def test_inventory_does_not_preserve_source_paths(tmp_path: Path) -> None:
    source_root = tmp_path / "aegis-sensitive-data"
    (source_root / "secret_named_bucket").mkdir(parents=True)
    (source_root / "secret_named_bucket" / "private_ticket.txt").write_text(
        "Ticket ID: DEMO-1",
        encoding="utf-8",
    )

    inventory = inventory_quarantined_source(source_root)

    assert inventory["raw_paths_preserved"] is False
    rendered = str(inventory)
    assert "secret_named_bucket" not in rendered
    assert "private_ticket" not in rendered
    assert inventory["files"] == 1
    assert inventory["buckets"][0]["bucket"] == "bucket_001"


def test_sanitized_tree_scan_detects_unsafe_output(tmp_path: Path) -> None:
    root = tmp_path / "raw_sanitized"
    root.mkdir()
    (root / "unsafe.robot").write_text(
        "Log    http://still-sensitive.example.test",
        encoding="utf-8",
    )

    scan = scan_sanitized_tree(root)

    assert scan["passed"] is False
    assert scan["findings"]["url"] == 1


def test_sanitized_tree_scan_allows_placeholder_tokens(tmp_path: Path) -> None:
    root = tmp_path / "raw_sanitized"
    root.mkdir()
    (root / "safe.robot").write_text(
        "Authorization: Bearer TOKEN_PLACEHOLDER\nURL_PLACEHOLDER",
        encoding="utf-8",
    )

    scan = scan_sanitized_tree(root)

    assert scan["passed"] is True
    assert scan["findings"] == {}
