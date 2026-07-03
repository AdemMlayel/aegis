"""Coverage derivation from adjudicated requirement analysis (Layer 3 support).

Previously coverage planning ignored almost the entire requirement analysis: it
read only ``domain`` and one checklist boolean, drove risk off ticket priority,
and emitted a HARDCODED coverage matrix (``REQ-001/2/3 -> TC001/2/3``) regardless
of the actual ticket. The adjudication work in Layer 2 (reconciled checklist,
clarification questions, confidence) therefore dead-ended one stage downstream.

This module makes coverage actually *consume* that reasoning, deterministically
and traceably:

* **Requirement derivation** — turn acceptance criteria + satisfied checklist
  items into a concrete, ticket-specific requirement list (each with a stable id),
  instead of the fixed REQ-001/2/3 placeholders. This is what the coverage matrix
  and test-case ``requirement_refs`` get tagged against.
* **Checklist-driven coverage types** — the reconciled checklist now changes the
  required test types: error scenarios present ⇒ mandate negative + boundary; data
  constraints present ⇒ mandate boundary; performance set ⇒ mandate performance.
  Every decision is recorded as a rationale line.
* **Confidence propagation** — start from the requirement analysis confidence and
  adjust by how complete the requirements are (how much of the checklist the plan
  could act on), rather than reinventing a number from priority alone.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.graph.state import RequirementAnalysis, RequirementCoverageItem

_BASE_TYPES = ["functional", "negative"]


@dataclass
class CoverageDerivation:
    requirements: list[RequirementCoverageItem]
    test_types_required: list[str]
    confidence: float
    rationale: list[str] = field(default_factory=list)


def _slug(index: int) -> str:
    return f"REQ-{index:03d}"


def derive_requirements(analysis: RequirementAnalysis) -> list[RequirementCoverageItem]:
    """Build a concrete, ticket-specific requirement list from the analysis.

    Order: the primary success path first, then one requirement per acceptance
    criterion / expected result, then checklist-implied requirements (error
    handling, boundary/data) when the adjudicated checklist affirms them. Falls
    back to a single primary requirement when the ticket carries nothing else.
    """
    items: list[RequirementCoverageItem] = []
    index = 1

    # Primary success path is always present.
    primary_desc = analysis.business_action or "Primary business action succeeds"
    items.append(
        RequirementCoverageItem(
            requirement_id=_slug(index),
            description=f"{primary_desc} — primary success path",
            origin="default",
            test_types=["functional"],
        )
    )
    index += 1

    # One requirement per concrete expected result (deduped, capped to keep the
    # matrix readable). These are the real, ticket-specific acceptance points.
    seen: set[str] = set()
    for expected in analysis.expected_results:
        norm = expected.strip()
        if not norm or norm.lower() in seen:
            continue
        seen.add(norm.lower())
        items.append(
            RequirementCoverageItem(
                requirement_id=_slug(index),
                description=norm,
                origin="acceptance_criteria",
                test_types=["functional"],
            )
        )
        index += 1
        if index > 6:  # cap explicit acceptance-derived requirements
            break

    checklist = analysis.completeness_checklist
    if checklist.error_scenarios_mentioned:
        items.append(
            RequirementCoverageItem(
                requirement_id=_slug(index),
                description="Invalid / rejected input is handled without side effects",
                origin="checklist",
                test_types=["negative"],
            )
        )
        index += 1
    if checklist.data_constraints_defined:
        items.append(
            RequirementCoverageItem(
                requirement_id=_slug(index),
                description="Boundary and data-constraint values behave per spec",
                origin="checklist",
                test_types=["boundary"],
            )
        )
        index += 1
    return items


def derive_coverage(
    analysis: RequirementAnalysis,
    *,
    risk_level: str,
) -> CoverageDerivation:
    """Derive requirements, required test types, and confidence from the analysis."""
    rationale: list[str] = []
    requirements = derive_requirements(analysis)

    types = list(_BASE_TYPES)
    checklist = analysis.completeness_checklist

    if checklist.error_scenarios_mentioned:
        if "negative" not in types:
            types.append("negative")
        if "boundary" not in types:
            types.append("boundary")
        rationale.append(
            "coverage: error scenarios affirmed by adjudicated checklist ⇒ "
            "negative + boundary mandated."
        )
    if checklist.data_constraints_defined and "boundary" not in types:
        types.append("boundary")
        rationale.append(
            "coverage: data constraints defined ⇒ boundary coverage mandated."
        )
    if risk_level in {"high", "critical"} and "boundary" not in types:
        types.append("boundary")
        rationale.append(
            f"coverage: {risk_level} risk ⇒ boundary coverage mandated."
        )
    if checklist.performance_expectations_set:
        types.append("performance")
        rationale.append(
            "coverage: performance expectations set ⇒ performance coverage mandated."
        )

    # --- Confidence propagation --------------------------------------------
    satisfied = sum(
        1
        for f in (
            "actor_identified",
            "preconditions_defined",
            "expected_outcome_specified",
            "error_scenarios_mentioned",
            "data_constraints_defined",
            "performance_expectations_set",
        )
        if getattr(checklist, f)
    )
    completeness = satisfied / 6
    # Blend the upstream (adjudicated) requirement confidence with coverage
    # completeness so the number carries forward and reflects what coverage could
    # actually act on. Weighted toward the upstream signal (0.6) since it is the
    # adjudicated, evidence-grounded figure.
    propagated = round(analysis.confidence * 0.6 + completeness * 0.4, 4)
    rationale.append(
        f"confidence: {propagated} = requirement_confidence({analysis.confidence})×0.6 "
        f"+ checklist_completeness({round(completeness, 4)})×0.4 "
        f"[{satisfied}/6 items satisfied]."
    )

    return CoverageDerivation(
        requirements=requirements,
        test_types_required=types,
        confidence=propagated,
        rationale=rationale,
    )


def build_coverage_matrix(
    requirements: list[RequirementCoverageItem],
    test_case_ids_by_requirement: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Build the matrix keyed by real requirement id+description → covering tests."""
    matrix: dict[str, list[str]] = {}
    for req in requirements:
        key = f"{req.requirement_id} {req.description}"
        matrix[key] = test_case_ids_by_requirement.get(req.requirement_id, [])
    return matrix
