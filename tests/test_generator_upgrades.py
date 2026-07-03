"""Tests for generator upgrades:
1. one covering test case per derived requirement (beyond the 3 base archetypes),
2. generic robot files emit REAL BuiltIn assertions over resolved data (not Log-only).
"""
from __future__ import annotations

from backend.graph.state import (
    CompletenessChecklist,
    CoveragePlan,
    RequirementAnalysis,
    RequirementCoverageItem,
    ReviewFeedback,
    TestCase,
    TestDataBlock,
)
from backend.tools.test_case_heuristics import generate_test_cases
from backend.tools.automation_heuristics import _builtin_data_assertions, _render_robot_file


def _analysis() -> RequirementAnalysis:
    return RequirementAnalysis(
        business_action="Reset Password",
        domain="security",
        actor="customer",
        preconditions=["User exists"],
        expected_results=["Reset completes"],
        completeness_checklist=CompletenessChecklist(
            error_scenarios_mentioned=True, data_constraints_defined=True
        ),
        confidence=0.8,
    )


def _plan_with_requirements(n_extra: int) -> CoveragePlan:
    reqs = [
        RequirementCoverageItem(
            requirement_id=f"REQ-{i:03d}",
            description=f"Requirement {i}",
            origin="acceptance_criteria" if i <= 3 else "checklist",
            test_types=["negative"] if i > 3 else ["functional"],
        )
        for i in range(1, 4 + n_extra)
    ]
    matrix = {
        f"{r.requirement_id} {r.description}": [f"TC{i:03d}"]
        for i, r in enumerate(reqs, start=1)
    }
    return CoveragePlan(
        risk_level="high",
        test_types_required=["functional", "negative", "boundary"],
        coverage_matrix=matrix,
        requirement_items=reqs,
    )


# --- Task 1: one case per derived requirement -------------------------------

def test_three_requirements_yields_three_base_cases() -> None:
    cases = generate_test_cases(analysis=_analysis(), coverage_plan=_plan_with_requirements(0))
    assert [c.id for c in cases] == ["TC001", "TC002", "TC003"]


def test_extra_requirements_get_covering_cases() -> None:
    # 5 derived requirements ⇒ 3 base + 2 extra covering cases.
    cases = generate_test_cases(analysis=_analysis(), coverage_plan=_plan_with_requirements(2))
    assert [c.id for c in cases] == ["TC001", "TC002", "TC003", "TC004", "TC005"]
    # The extra cases tag to the real derived requirements, not hardcoded refs.
    tc004 = next(c for c in cases if c.id == "TC004")
    assert tc004.requirement_refs == ["REQ-004"]
    assert any("Derived from coverage requirement REQ-004" in n for n in tc004.generation_notes)


def test_extra_requirement_case_type_follows_requirement() -> None:
    cases = generate_test_cases(analysis=_analysis(), coverage_plan=_plan_with_requirements(1))
    tc004 = next(c for c in cases if c.id == "TC004")
    # REQ-004 declares test_types=["negative"].
    assert tc004.type == "negative"


# --- Task 2: real BuiltIn assertions ----------------------------------------

def test_builtin_assertions_use_resolved_data() -> None:
    tc = TestCase(
        id="TC001", title="t", type="functional", expected_outcome="Login succeeds",
    )
    td = TestDataBlock(
        test_case_id="TC001", strategy="factory",
        resolved_data={"users": ["alice", "bob"], "records": ["r1"]},
    )
    lines = _builtin_data_assertions(tc, td)
    body = "\n".join(lines)
    assert "Create List    alice    bob" in body
    assert "Should Not Be Empty    ${USERS}" in body
    assert "Should Contain    ${USERS}    alice" in body
    assert "Should Be Equal As Strings" in body
    # No bare Log-only — these are real assertions.
    assert "Create List" in body


def test_builtin_assertions_fallback_when_no_data() -> None:
    tc = TestCase(id="TC001", title="t", type="functional", expected_outcome="")
    lines = _builtin_data_assertions(tc, None)
    # Still emits one real executable assertion, not nothing.
    assert lines == ["    Should Be True    ${True}"]


def test_generic_robot_file_contains_real_assertions_not_only_logs() -> None:
    tc = TestCase(
        id="TC001", title="Happy Path", type="functional",
        expected_outcome="Works", preconditions=["env"], steps=["do a thing"],
    )
    td = TestDataBlock(
        test_case_id="TC001", strategy="factory", resolved_data={"users": ["u1"]},
    )
    content = _render_robot_file(tc, "TICKET-1", 1, [], ticket=None, test_data=td)
    assert "Library           BuiltIn" in content
    assert "Create List    u1" in content
    assert "Should Contain" in content
    # Steps are still logged for traceability, but assertions are present too.
    assert "Log    Step 1: do a thing" in content


def test_review_feedback_still_rendered() -> None:
    tc = TestCase(id="TC001", title="t", type="functional", expected_outcome="ok")
    fb = [ReviewFeedback(requested_by="qa", comment="tighten assertion", stage="automation")]
    content = _render_robot_file(tc, "TICKET-1", 1, fb, ticket=None, test_data=None)
    assert "Reviewer feedback applied: tighten assertion" in content
