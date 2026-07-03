"""Tests for requirement-analysis adjudication (Layer 2 reconciliation).

Verifies the explicit, recorded reconciliation rules: checklist union with
provenance, grounded confidence blending, and clarification dedup/retraction —
plus that an ungrounded-but-confident LLM cannot dominate concrete heuristic
evidence, and that a missing LLM signal degrades cleanly to heuristic-only.
"""
from __future__ import annotations

from backend.graph.state import CompletenessChecklist
from backend.intelligence.requirement_adjudication import (
    adjudicate_requirement_analysis,
)
from backend.intelligence.structured_outputs import (
    RequirementChecklistAssessment,
    RequirementLLMOutput,
)


def _heuristic(**flags: bool) -> CompletenessChecklist:
    return CompletenessChecklist(**flags)


# --- Rule 1: checklist union with provenance --------------------------------

def test_grounded_llm_raises_item_heuristic_missed() -> None:
    heur = _heuristic(actor_identified=True, error_scenarios_mentioned=False)
    llm = RequirementLLMOutput(
        summary="Insufficient-funds transfer must return an error.",
        ambiguities=["Daily cap?"],
        confidence=0.9,
        checklist_assessment=RequirementChecklistAssessment(error_scenarios_mentioned=True),
    )
    res = adjudicate_requirement_analysis(
        heuristic_checklist=heur,
        heuristic_questions=["Which error states should be tested?"],
        llm=llm,
        heuristic_confidence=0.62,
        knowledge_refs=2,
        memory_refs=0,
    )
    assert res.checklist.error_scenarios_mentioned is True
    assert any("raised False→True" in n for n in res.notes)


def test_llm_cannot_clear_a_heuristic_confirmed_item() -> None:
    # Heuristic found error scenarios (concrete keyword evidence); LLM says no.
    heur = _heuristic(error_scenarios_mentioned=True)
    llm = RequirementLLMOutput(
        summary="No error handling discussed.",
        ambiguities=["unclear"],
        confidence=0.8,
        checklist_assessment=RequirementChecklistAssessment(error_scenarios_mentioned=False),
    )
    res = adjudicate_requirement_analysis(
        heuristic_checklist=heur,
        heuristic_questions=[],
        llm=llm,
        heuristic_confidence=0.62,
        knowledge_refs=1,
        memory_refs=0,
    )
    # Item stays True; dissent is recorded, not silently applied.
    assert res.checklist.error_scenarios_mentioned is True
    assert any("kept True despite LLM dissent" in n for n in res.notes)


def test_llm_none_opinion_leaves_heuristic_untouched() -> None:
    heur = _heuristic(data_constraints_defined=False)
    llm = RequirementLLMOutput(
        summary="A reading with no checklist opinion.",
        ambiguities=["something"],
        confidence=0.7,
        checklist_assessment=RequirementChecklistAssessment(),  # all None
    )
    res = adjudicate_requirement_analysis(
        heuristic_checklist=heur,
        heuristic_questions=["What input limits, formats, or currencies apply?"],
        llm=llm,
        heuristic_confidence=0.62,
        knowledge_refs=1,
        memory_refs=0,
    )
    assert res.checklist.data_constraints_defined is False


# --- Rule 2: grounded confidence reconciliation -----------------------------

def test_ungrounded_confident_llm_is_discounted() -> None:
    heur = _heuristic(actor_identified=True)
    llm = RequirementLLMOutput(
        summary="x",
        ambiguities=[],
        confidence=0.99,
        checklist_assessment=RequirementChecklistAssessment(error_scenarios_mentioned=True),
    )
    res = adjudicate_requirement_analysis(
        heuristic_checklist=heur,
        heuristic_questions=[],
        llm=llm,
        heuristic_confidence=0.62,
        knowledge_refs=0,
        memory_refs=0,
    )
    # No grounding ⇒ assessment ignored, confidence stays at heuristic base.
    assert res.checklist.error_scenarios_mentioned is False
    assert res.confidence < 0.9
    assert any("LLM ungrounded" in n for n in res.notes)


def test_grounded_confidence_is_blended_and_recorded() -> None:
    heur = _heuristic(actor_identified=True, expected_outcome_specified=True)
    llm = RequirementLLMOutput(
        summary="A grounded reading.",
        ambiguities=["edge?"],
        confidence=0.9,
        checklist_assessment=None,
    )
    res = adjudicate_requirement_analysis(
        heuristic_checklist=heur,
        heuristic_questions=[],
        llm=llm,
        heuristic_confidence=0.62,
        knowledge_refs=3,
        memory_refs=1,
    )
    # Blended value lies strictly between the heuristic base and the LLM number.
    assert 0.5 < res.confidence < 0.9
    assert any("confidence:" in n and "×0.35" in n for n in res.notes)


def test_no_llm_signal_uses_heuristic_base_only() -> None:
    heur = _heuristic(actor_identified=True, preconditions_defined=True, expected_outcome_specified=True)
    res = adjudicate_requirement_analysis(
        heuristic_checklist=heur,
        heuristic_questions=[],
        llm=None,
        heuristic_confidence=0.62,
    )
    # 3/6 satisfied ⇒ 0.5 + 0.5*0.5 = 0.75.
    assert res.confidence == 0.75
    assert any("no LLM signal available" in n for n in res.notes)


def test_confidence_scales_with_satisfied_items() -> None:
    empty = adjudicate_requirement_analysis(
        heuristic_checklist=_heuristic(), heuristic_questions=[], llm=None,
        heuristic_confidence=0.5,
    )
    full = adjudicate_requirement_analysis(
        heuristic_checklist=_heuristic(
            actor_identified=True, preconditions_defined=True,
            expected_outcome_specified=True, error_scenarios_mentioned=True,
            data_constraints_defined=True, performance_expectations_set=True,
        ),
        heuristic_questions=[], llm=None, heuristic_confidence=0.5,
    )
    assert empty.confidence == 0.5
    assert full.confidence == 1.0


# --- Rule 3: clarification dedup + conflict resolution ----------------------

def test_question_retracted_when_item_satisfied_by_llm() -> None:
    heur = _heuristic(error_scenarios_mentioned=False)
    llm = RequirementLLMOutput(
        summary="Errors are handled: returns 400 on bad input.",
        ambiguities=[],
        confidence=0.85,
        checklist_assessment=RequirementChecklistAssessment(error_scenarios_mentioned=True),
    )
    res = adjudicate_requirement_analysis(
        heuristic_checklist=heur,
        heuristic_questions=["Which error states should be tested?"],
        llm=llm,
        heuristic_confidence=0.62,
        knowledge_refs=2,
        memory_refs=0,
    )
    assert "Which error states should be tested?" not in res.clarification_questions
    assert any("question retracted" in n for n in res.notes)


def test_near_duplicate_questions_are_deduped() -> None:
    heur = _heuristic()
    llm = RequirementLLMOutput(
        summary="reading",
        ambiguities=["What input limits, formats, or currencies apply?"],  # dup of heuristic
        confidence=0.7,
    )
    res = adjudicate_requirement_analysis(
        heuristic_checklist=heur,
        heuristic_questions=["What input limits, formats, or currencies apply?"],
        llm=llm,
        heuristic_confidence=0.62,
        knowledge_refs=1,
        memory_refs=0,
    )
    occurrences = sum(
        1 for q in res.clarification_questions if "input limits" in q.lower()
    )
    assert occurrences == 1


def test_ungrounded_llm_ambiguities_not_added() -> None:
    heur = _heuristic()
    llm = RequirementLLMOutput(
        summary="x", ambiguities=[], confidence=0.7,
    )  # ungrounded: no refs, no ambiguities
    res = adjudicate_requirement_analysis(
        heuristic_checklist=heur,
        heuristic_questions=["Heuristic question?"],
        llm=llm,
        heuristic_confidence=0.62,
        knowledge_refs=0,
        memory_refs=0,
    )
    assert res.clarification_questions == ["Heuristic question?"]


# --- End-to-end through the heuristic tool ----------------------------------

def test_analyze_ticket_populates_adjudication_notes() -> None:
    from backend.graph.state import TicketData
    from backend.tools.requirement_heuristics import analyze_ticket

    ticket = TicketData(
        id="ADJ-001",
        title="Transfer funds with insufficient balance",
        description=(
            "As a customer I transfer funds. If balance is insufficient the system "
            "must return an error. Minimum transfer is 1 USD."
        ),
        acceptance_criteria=["Transfer completes within 2 seconds for valid input."],
        priority="high",
        labels=["banking", "transfer"],
    )
    analysis = analyze_ticket(ticket)
    # Adjudication ran and recorded its reasoning; confidence is in range.
    assert analysis.adjudication_notes
    assert 0.0 <= analysis.confidence <= 1.0
    assert any("confidence:" in n for n in analysis.adjudication_notes)
