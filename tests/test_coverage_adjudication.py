"""Tests for coverage-plan adjudication (Layer 3 reconciliation).

Verifies the explicit, recorded reconciliation rules: labelled risk-note union
under loose grounding, the STRICT retrieval gate on suggested regressions (which
become execution targets), malformed-id dropping, grounded confidence blending,
and that deterministic memory-evidenced regressions always survive.
"""
from __future__ import annotations

from backend.intelligence.coverage_adjudication import adjudicate_coverage_plan
from backend.intelligence.structured_outputs import CoverageLLMOutput


# --- Rule 1: risk notes — labelled union under loose grounding --------------

def test_grounded_risk_notes_are_folded_and_labelled() -> None:
    llm = CoverageLLMOutput(
        risk_notes=["Concurrent transfers may double-spend."],
        suggested_regressions=[],
        confidence=0.8,
    )
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=[],
        deterministic_rationale=["Priority 'high' produces high risk."],
        llm=llm,
        knowledge_refs=2,
        memory_refs=0,
    )
    assert any(
        a == "LLM risk note: Concurrent transfers may double-spend."
        for a in res.risk_rationale_additions
    )
    assert any("folded 1 grounded LLM risk note" in n for n in res.notes)


def test_ungrounded_risk_notes_are_withheld() -> None:
    # No retrieval refs AND no concrete content ⇒ not grounded.
    llm = CoverageLLMOutput(risk_notes=[], suggested_regressions=[], confidence=0.95)
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=[],
        deterministic_rationale=["base"],
        llm=llm,
        knowledge_refs=0,
        memory_refs=0,
    )
    assert res.risk_rationale_additions == []
    assert any("risk notes withheld" in n for n in res.notes)


def test_duplicate_risk_note_is_deduped_against_deterministic() -> None:
    llm = CoverageLLMOutput(
        risk_notes=["Priority high produces high risk"],  # ~dup of deterministic
        suggested_regressions=[],
        confidence=0.7,
    )
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=[],
        deterministic_rationale=["Priority 'high' produces high risk."],
        llm=llm,
        knowledge_refs=1,
        memory_refs=0,
    )
    assert res.risk_rationale_additions == []


def test_unstructured_prose_retained_when_parse_failed_real_provider() -> None:
    # structured_output is None (parse failed) but a real provider gave prose.
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=[],
        deterministic_rationale=["base"],
        llm=None,
        knowledge_refs=0,
        memory_refs=0,
        llm_unparsed_text="Consider load spikes at month end.",
        llm_provider="openai_compatible",
    )
    assert any(
        a.startswith("LLM guidance (unstructured):") for a in res.risk_rationale_additions
    )


def test_mock_provider_prose_is_not_retained() -> None:
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=[],
        deterministic_rationale=["base"],
        llm=None,
        knowledge_refs=0,
        memory_refs=0,
        llm_unparsed_text="mock output",
        llm_provider="mock_llm",
    )
    assert res.risk_rationale_additions == []


# --- Rule 2: suggested regressions — evidence gate + provenance -------------

def test_regressions_admitted_only_when_retrieval_grounded() -> None:
    llm = CoverageLLMOutput(
        risk_notes=[],
        suggested_regressions=["REG-RACE-CONDITION"],
        confidence=0.8,
    )
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=["REG-BALANCE-CONSISTENCY"],
        deterministic_rationale=["base"],
        llm=llm,
        knowledge_refs=1,  # retrieval present ⇒ grounded
        memory_refs=0,
    )
    assert "REG-RACE-CONDITION" in res.regressions
    assert "REG-BALANCE-CONSISTENCY" in res.regressions
    assert any("regressions admitted" in n for n in res.notes)


def test_regressions_withheld_without_retrieval_evidence() -> None:
    # The dangerous case: a hallucinated regression must NOT enter the plan.
    llm = CoverageLLMOutput(
        risk_notes=["some note"],  # loosely grounded for NOTES
        suggested_regressions=["REG-HALLUCINATED"],
        confidence=0.9,
    )
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=["REG-BALANCE-CONSISTENCY"],
        deterministic_rationale=["base"],
        llm=llm,
        knowledge_refs=0,  # NO retrieval ⇒ strict gate fails
        memory_refs=0,
    )
    assert "REG-HALLUCINATED" not in res.regressions
    assert res.regressions == ["REG-BALANCE-CONSISTENCY"]
    assert any("withheld from the execution order" in n for n in res.notes)


def test_malformed_regression_ids_are_dropped() -> None:
    llm = CoverageLLMOutput(
        risk_notes=[],
        suggested_regressions=[
            "REG-OK",
            "   ",  # empty
            "a sentence that is clearly not an id and runs well beyond the cap length allowed here",
            "REG-WITH\nNEWLINE",
        ],
        confidence=0.8,
    )
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=[],
        deterministic_rationale=["base"],
        llm=llm,
        knowledge_refs=1,
        memory_refs=0,
    )
    assert "REG-OK" in res.regressions
    assert all("NEWLINE" not in r for r in res.regressions)
    assert all(len(r) <= 64 for r in res.regressions)
    assert any("dropped (malformed id)" in n for n in res.notes)


def test_deterministic_regressions_always_survive() -> None:
    # Even with no LLM, the memory-evidenced regressions pass straight through.
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=["REG-AUTH-NEGATIVE-PATHS"],
        deterministic_rationale=["base"],
        llm=None,
    )
    assert res.regressions == ["REG-AUTH-NEGATIVE-PATHS"]


def test_duplicate_suggested_regression_not_double_added() -> None:
    llm = CoverageLLMOutput(
        risk_notes=[],
        suggested_regressions=["REG-BALANCE-CONSISTENCY"],  # already deterministic
        confidence=0.8,
    )
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=["REG-BALANCE-CONSISTENCY"],
        deterministic_rationale=["base"],
        llm=llm,
        knowledge_refs=1,
        memory_refs=0,
    )
    assert res.regressions == ["REG-BALANCE-CONSISTENCY"]


# --- Rule 3: confidence — grounded blend, never silent ----------------------

def test_grounded_confidence_blended_and_recorded() -> None:
    llm = CoverageLLMOutput(
        risk_notes=["note"], suggested_regressions=[], confidence=0.9
    )
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=[],
        deterministic_rationale=["base"],
        llm=llm,
        knowledge_refs=2,
        memory_refs=0,
    )
    # 0.7*0.7 + 0.9*0.3 = 0.49 + 0.27 = 0.76
    assert res.confidence == 0.76
    assert any("×0.3" in n and "confidence:" in n for n in res.notes)


def test_ungrounded_confidence_discarded_not_silent() -> None:
    llm = CoverageLLMOutput(
        risk_notes=[], suggested_regressions=[], confidence=0.99
    )
    res = adjudicate_coverage_plan(
        derivation_confidence=0.7,
        deterministic_regressions=[],
        deterministic_rationale=["base"],
        llm=llm,
        knowledge_refs=0,
        memory_refs=0,
    )
    assert res.confidence == 0.7
    assert any("its confidence 0.99 discarded" in n for n in res.notes)


def test_no_llm_signal_uses_derivation_confidence() -> None:
    res = adjudicate_coverage_plan(
        derivation_confidence=0.83,
        deterministic_regressions=[],
        deterministic_rationale=["base"],
        llm=None,
    )
    assert res.confidence == 0.83
    assert any("no parsed LLM signal" in n for n in res.notes)
