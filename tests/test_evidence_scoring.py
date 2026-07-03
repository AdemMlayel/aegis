"""Tests for the evidence-weighted investigation scoring model (Layer 7).

Covers the pure scorer (signal detection, traceable Σ math, normalization,
aggregation) and its integration into the investigation coordinator (derived
confidence replacing the old hardcoded literals, matched-signal breakdown,
severity bands, signal-driven recommended actions).
"""
from __future__ import annotations

from backend.graph.nodes.investigation_coordinator import (
    _extract_referenced_keywords,
    _recommended_actions,
    _registry_keyword_names,
    _severity_for_score,
    investigation_coordinator,
)
from backend.graph.state import (
    ExecutionBlock,
    ExecutionCaseResult,
    ExecutionSummary,
    TestContext,
    utc_now,
)
from backend.intelligence.evidence_scoring import (
    NORMALIZATION_WEIGHT,
    SIGNALS,
    TOTAL_WEIGHT,
    EvidenceProbe,
    aggregate,
    score_probe,
)


# --- Pure scorer -------------------------------------------------------------

def test_signal_table_has_spec_and_domain_signals() -> None:
    names = {s.name for s in SIGNALS}
    # The twelve canonical blueprint spec signals are all present verbatim.
    spec = {
        "http_5xx", "http_4xx", "contract_breach", "timeout",
        "timestamp_correlation", "auth_failure", "network_anomaly",
        "historical_match", "resource_exhaustion", "config_error",
        "log_pattern_match", "db_error",
    }
    assert spec <= names
    # Domain-native signals exist too (Option B).
    assert {"keyword_resolution_failure", "robot_import_error"} <= names
    # Canonical spec weights preserved exactly.
    by_name = {s.name: s.weight for s in SIGNALS}
    assert by_name["http_5xx"] == 35
    assert by_name["http_4xx"] == 30
    assert by_name["contract_breach"] == 30
    assert by_name["timeout"] == 25
    assert by_name["db_error"] == 15


def test_clean_pass_scores_zero() -> None:
    result = score_probe(EvidenceProbe(status="passed", message="", logs=["PASS"]))
    assert result.score == 0.0
    assert result.hits == []
    assert result.confidence == 0.0


def test_http_5xx_failure_scores_high_and_is_traceable() -> None:
    probe = EvidenceProbe(
        status="failed",
        message="HTTP 503 Service Unavailable",
        logs=["Traceback (most recent call last):", "read timed out"],
        duration_ms=45_000,
    )
    result = score_probe(probe)
    fired = {h.signal for h in result.hits}
    assert "http_5xx" in fired
    assert "timeout" in fired
    # Severe multi-signal failure must read as high confidence, not ~25.
    assert result.score >= 70
    # The basis string is the literal traceable arithmetic.
    matched = sum(h.weight for h in result.hits)
    assert f"/ {NORMALIZATION_WEIGHT} × 100" in result.basis
    assert str(matched) in result.basis


def test_503_does_not_double_count_as_environment_unavailable() -> None:
    # "503 Service Unavailable" must not also fire environment_unavailable —
    # that phrase belongs to the HTTP signal, not an infra signal.
    result = score_probe(
        EvidenceProbe(status="failed", message="HTTP 503 Service Unavailable")
    )
    assert {h.signal for h in result.hits} == {"http_5xx"}


def test_keyword_resolution_signal_fires_on_registry_diff() -> None:
    probe = EvidenceProbe(
        status="failed",
        message="No keyword with name 'Do Geet' found",
        referenced_keywords=("Do Geet",),
        known_keywords=frozenset({"Do Get", "Log"}),
    )
    result = score_probe(probe)
    fired = {h.signal for h in result.hits}
    assert "keyword_resolution_failure" in fired
    assert result.dominant_category == "test"


def test_score_never_exceeds_100() -> None:
    # Pile on many signals; score is clamped at 100 and basis notes the cap.
    probe = EvidenceProbe(
        status="failed",
        message="HTTP 500 401 Unauthorized schema mismatch connection refused",
        logs=["Traceback", "out of memory", "sql deadlock", "missing env var",
              "AssertionError expected but got", "docker container could not start"],
        duration_ms=60_000,
    )
    result = score_probe(probe)
    assert result.score <= 100.0


def test_aggregate_is_max_driven_not_diluted() -> None:
    severe = score_probe(
        EvidenceProbe(status="failed", message="HTTP 500", logs=["timed out"], duration_ms=40_000)
    )
    weak = score_probe(EvidenceProbe(status="failed", message="AssertionError"))
    agg = aggregate([severe, weak])
    # Adding a weak finding must not lower the strong finding's score.
    assert agg.score == max(severe.score, weak.score)
    # Union of distinct signals across findings.
    assert {h.signal for h in agg.hits} >= {h.signal for h in severe.hits}


def test_total_weight_is_audit_ceiling_not_divisor() -> None:
    # TOTAL_WEIGHT (full budget) is larger than the normalization divisor;
    # the score uses the realistic co-firing divisor.
    assert TOTAL_WEIGHT > NORMALIZATION_WEIGHT


# --- Coordinator integration -------------------------------------------------

def _context_with_failure(message: str, logs: list[str], duration_ms: int = 0) -> TestContext:
    context = TestContext(context_id="ctx-evidence-test", created_by="evidence-test")
    context.execution = ExecutionBlock(
        status="failed",
        run_by="system",
        started_at=utc_now(),
        finished_at=utc_now(),
        summary=ExecutionSummary(total=1, passed=0, failed=1),
        adapter="local",
        results=[
            ExecutionCaseResult(
                test_case_id="TC001",
                title="Failing case",
                status="failed",
                message=message,
                logs=logs,
                duration_ms=duration_ms,
                robot_file="generated/tc001.robot",
            )
        ],
    )
    return context


def test_coordinator_uses_derived_confidence_not_hardcoded() -> None:
    context = _context_with_failure(
        "HTTP 503 Service Unavailable", ["Traceback", "read timed out"], duration_ms=45_000
    )
    result = investigation_coordinator(context)
    assert result.investigation is not None
    block = result.investigation
    assert block.status == "completed"
    assert block.findings
    finding = block.findings[0]
    # NOT the old hardcoded 0.72/0.6.
    assert finding.confidence not in {0.72, 0.6, 0.88}
    # Derived score is populated and traceable.
    assert finding.evidence_score >= 70
    assert finding.matched_signals
    assert "× 100" in finding.score_basis
    # Block-level rollup present.
    assert block.evidence_score == finding.evidence_score
    assert block.matched_signals


def test_coordinator_severity_scales_with_score() -> None:
    severe = investigation_coordinator(
        _context_with_failure("HTTP 500", ["timed out", "Traceback"], duration_ms=40_000)
    )
    weak = investigation_coordinator(
        _context_with_failure("AssertionError: values differ", [])
    )
    assert severe.investigation.findings[0].severity in {"high", "critical"}
    assert weak.investigation.findings[0].severity in {"info", "warning"}


def test_coordinator_recommends_self_healing_on_keyword_failure() -> None:
    context = _context_with_failure("No keyword with name 'Do Geet' found", [])
    result = investigation_coordinator(context)
    actions = result.investigation.findings[0].recommended_actions
    assert any("self-healing" in a.lower() for a in actions)


def test_clean_execution_has_zero_evidence_score() -> None:
    context = TestContext(context_id="ctx-clean", created_by="evidence-test")
    context.execution = ExecutionBlock(
        status="passed",
        run_by="system",
        started_at=utc_now(),
        finished_at=utc_now(),
        summary=ExecutionSummary(total=1, passed=1, failed=0),
        adapter="local",
        results=[
            ExecutionCaseResult(
                test_case_id="TC001", title="Passing", status="passed",
                message="", logs=["PASS"], duration_ms=10,
            )
        ],
    )
    result = investigation_coordinator(context)
    assert result.investigation.findings == []
    assert result.investigation.evidence_score == 0.0
    assert result.investigation.confidence == 0.0


# --- Helpers -----------------------------------------------------------------

def test_registry_keyword_names_loads_real_registry() -> None:
    names = _registry_keyword_names()
    assert len(names) > 100  # the sanitized corpus has 238


def test_extract_referenced_keywords_parses_robot_error() -> None:
    assert _extract_referenced_keywords("No keyword with name 'Do Get' found", []) == ("Do Get",)


def test_severity_bands() -> None:
    assert _severity_for_score(85) == "critical"
    assert _severity_for_score(55) == "high"
    assert _severity_for_score(30) == "warning"
    assert _severity_for_score(5) == "info"


def test_recommended_actions_always_nonempty() -> None:
    from backend.intelligence.evidence_scoring import ScoreResult
    assert _recommended_actions(ScoreResult(score=0.0, hits=[], basis="")) != []
