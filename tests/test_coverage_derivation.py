"""Tests for coverage derivation — coverage now CONSUMES the adjudicated
requirement analysis (checklist-driven types, real requirement matrix, propagated
confidence) instead of ignoring it, and test cases tag to the derived matrix.
"""
from __future__ import annotations

from backend.graph.state import (
    CompletenessChecklist,
    CoveragePlan,
    RequirementAnalysis,
)
from backend.intelligence.coverage_derivation import (
    build_coverage_matrix,
    derive_coverage,
    derive_requirements,
)
from backend.tools.test_case_heuristics import _refs_for, generate_test_cases


def _analysis(**checklist_flags: bool) -> RequirementAnalysis:
    return RequirementAnalysis(
        business_action="Money Transfer",
        domain="banking",
        actor="customer",
        expected_results=["Transfer completes within 3 seconds", "Balance updates"],
        completeness_checklist=CompletenessChecklist(**checklist_flags),
        confidence=0.8,
    )


# --- requirement derivation -------------------------------------------------

def test_requirements_derived_from_acceptance_criteria_not_hardcoded() -> None:
    reqs = derive_requirements(_analysis(expected_outcome_specified=True))
    descriptions = [r.description for r in reqs]
    assert any("primary success path" in d for d in descriptions)
    assert "Transfer completes within 3 seconds" in descriptions
    assert "Balance updates" in descriptions
    # ids are sequential and unique
    ids = [r.requirement_id for r in reqs]
    assert ids == sorted(set(ids), key=ids.index)
    assert ids[0] == "REQ-001"


def test_checklist_adds_error_and_boundary_requirements() -> None:
    reqs = derive_requirements(
        _analysis(error_scenarios_mentioned=True, data_constraints_defined=True)
    )
    origins = {r.origin for r in reqs}
    assert "checklist" in origins
    descriptions = " ".join(r.description for r in reqs).lower()
    assert "invalid" in descriptions or "rejected" in descriptions
    assert "boundary" in descriptions


# --- coverage type derivation (the consumption fix) -------------------------

def test_error_scenarios_mandate_negative_and_boundary() -> None:
    d = derive_coverage(_analysis(error_scenarios_mentioned=True), risk_level="medium")
    assert "negative" in d.test_types_required
    assert "boundary" in d.test_types_required
    assert any("error scenarios affirmed" in r for r in d.rationale)


def test_checklist_ignored_before_was_now_consumed() -> None:
    # Regression guard for the audit finding: previously coverage only reacted to
    # performance_expectations_set. Now error/data checklist items change types.
    without = derive_coverage(_analysis(), risk_level="low")
    with_errors = derive_coverage(
        _analysis(error_scenarios_mentioned=True), risk_level="low"
    )
    assert "boundary" not in without.test_types_required
    assert "boundary" in with_errors.test_types_required


def test_performance_flag_mandates_performance_type() -> None:
    d = derive_coverage(_analysis(performance_expectations_set=True), risk_level="low")
    assert "performance" in d.test_types_required


# --- confidence propagation -------------------------------------------------

def test_confidence_propagates_from_requirement_analysis() -> None:
    high = derive_coverage(
        _analysis(
            actor_identified=True, preconditions_defined=True,
            expected_outcome_specified=True, error_scenarios_mentioned=True,
            data_constraints_defined=True, performance_expectations_set=True,
        ),
        risk_level="high",
    )
    low = derive_coverage(_analysis(), risk_level="low")
    # More satisfied checklist items ⇒ higher propagated confidence.
    assert high.confidence > low.confidence
    assert any("requirement_confidence" in r for r in high.rationale)


# --- matrix + test-case tagging ---------------------------------------------

def test_matrix_tags_requirements_to_planned_test_slots() -> None:
    reqs = derive_requirements(_analysis(expected_outcome_specified=True))
    assignment = {r.requirement_id: [f"TC{i:03d}"] for i, r in enumerate(reqs, start=1)}
    matrix = build_coverage_matrix(reqs, assignment)
    assert all(" " in key for key in matrix)  # "REQ-00N description"
    assert matrix[f"{reqs[0].requirement_id} {reqs[0].description}"] == ["TC001"]


def test_refs_for_inverts_matrix() -> None:
    plan = CoveragePlan(
        coverage_matrix={
            "REQ-001 primary success path": ["TC001"],
            "REQ-002 Balance updates": ["TC002"],
        }
    )
    assert _refs_for(plan, "TC001", "REQ-FALLBACK") == ["REQ-001"]
    assert _refs_for(plan, "TC002", "REQ-FALLBACK") == ["REQ-002"]
    # Unmapped slot uses fallback.
    assert _refs_for(plan, "TC999", "REQ-FALLBACK") == ["REQ-FALLBACK"]


def test_generated_test_cases_tag_to_derived_requirements() -> None:
    analysis = _analysis(expected_outcome_specified=True)
    # Build a coverage plan the way plan_coverage now does.
    reqs = derive_requirements(analysis)
    assignment = {r.requirement_id: [f"TC{i:03d}"] for i, r in enumerate(reqs, start=1)}
    plan = CoveragePlan(
        risk_level="high",
        test_types_required=["functional", "negative", "boundary"],
        coverage_matrix=build_coverage_matrix(reqs, assignment),
    )
    cases = generate_test_cases(analysis=analysis, coverage_plan=plan)
    # TC001 should tag to REQ-001 (the derived primary), not a hardcoded constant
    # disconnected from the matrix.
    tc001 = next(c for c in cases if c.id == "TC001")
    assert tc001.requirement_refs == ["REQ-001"]
