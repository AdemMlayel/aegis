"""Coverage-plan adjudication (Layer 3 reasoning).

The coverage stage produces two independent signals about a ticket:

* a **deterministic derivation** — a ticket-specific requirement list, mandated
  test types, episodic-memory-evidenced regression tests, and a propagated
  confidence, all computed in :mod:`backend.intelligence.coverage_derivation`
  from the adjudicated requirement analysis, and
* an **LLM reading** — free-text ``risk_notes``, ``suggested_regressions`` ids,
  and a self-reported confidence.

Previously these were *stapled together*, not reconciled:
``risk_notes`` were blind-``extend``ed onto the rationale (no grounding check, no
provenance — an ungrounded model's prose sat indistinguishably beside concrete
derivation lines); ``suggested_regressions`` were blind-appended straight into
the regression set that feeds ``prioritization_order`` (so a hallucinated id
became a *planned execution target* with no evidence behind it); and the LLM's
coverage ``confidence`` was silently dropped with no recorded reason.

This module reconciles the two with **explicit, recorded rules**, the same way
:mod:`backend.intelligence.requirement_adjudication` reconciles Layer 2 and the
investigation stage scores evidence — every override is traceable.

Reconciliation rules
--------------------
1. **Risk notes (labelled union, loose grounding).** Risk notes are advisory
   text. When the LLM is *loosely* grounded (retrieved evidence OR produced
   concrete content) its notes are folded into the rationale, each explicitly
   tagged ``LLM risk note:`` and deduped against the deterministic lines. An
   ungrounded model's notes are withheld with a recorded reason.
2. **Suggested regressions (evidence gate + provenance).** A suggested
   regression becomes a real execution target, so it requires the *stricter*
   retrieval gate — knowledge or episodic-memory refs must be present, not just
   the model's say-so. Malformed ids are dropped. Every admission and every
   drop is recorded; deterministic (memory-evidenced) regressions always win and
   are never displaced.
3. **Confidence (grounded blend).** Start from the deterministic derivation
   confidence (itself an adjudicated, propagated figure). Move toward the LLM's
   confidence only to the extent the LLM is grounded, with a modest weight so a
   confident-but-ungrounded model cannot dominate. The arithmetic is recorded;
   an ungrounded model's confidence is discarded with a note instead of silently.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from backend.intelligence.structured_outputs import CoverageLLMOutput

# A suggested regression id flows into the execution order, so it must look like
# a real identifier — not a sentence, not empty, not unbounded.
_MAX_REGRESSION_ID_LEN = 64
# Weight applied to the LLM confidence when it is grounded. Lower than the
# requirement adjudicator's 0.35 because the derivation confidence is already a
# blended/propagated figure (requirement_confidence × 0.6 + completeness × 0.4),
# so we rotate onto the model more conservatively here.
_LLM_CONFIDENCE_WEIGHT = 0.30


@dataclass
class CoverageAdjudication:
    confidence: float
    # LLM-sourced rationale lines to append, already labelled with provenance.
    risk_rationale_additions: list[str] = field(default_factory=list)
    # Final reconciled regression list (deterministic + admitted LLM ones).
    regressions: list[str] = field(default_factory=list)
    # Adjudication trace — every fold/drop/blend decision, for auditability.
    notes: list[str] = field(default_factory=list)


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _is_duplicate(candidate: str, existing: list[str], threshold: float = 0.86) -> bool:
    return any(_similar(candidate, other) >= threshold for other in existing)


def _notes_grounded(llm: CoverageLLMOutput | None, *, knowledge_refs: int, memory_refs: int) -> bool:
    """Loose gate for advisory risk notes: retrieval OR concrete content."""
    if llm is None:
        return False
    return bool(knowledge_refs or memory_refs or llm.risk_notes or llm.suggested_regressions)


def _regressions_grounded(llm: CoverageLLMOutput | None, *, knowledge_refs: int, memory_refs: int) -> bool:
    """Strict gate for regressions: retrieved evidence must back the suggestion."""
    if llm is None:
        return False
    return bool(knowledge_refs or memory_refs)


def _valid_regression_id(candidate: str) -> bool:
    cand = candidate.strip()
    if not cand:
        return False
    if len(cand) > _MAX_REGRESSION_ID_LEN:
        return False
    if any(ch in cand for ch in "\n\r\t"):
        return False
    return True


def adjudicate_coverage_plan(
    *,
    derivation_confidence: float,
    deterministic_regressions: list[str],
    deterministic_rationale: list[str],
    llm: CoverageLLMOutput | None,
    knowledge_refs: int = 0,
    memory_refs: int = 0,
    llm_unparsed_text: str | None = None,
    llm_provider: str | None = None,
) -> CoverageAdjudication:
    """Reconcile deterministic coverage derivation with the LLM reading."""
    notes: list[str] = []
    additions: list[str] = []

    # --- Rule 1: risk notes — labelled union under loose grounding ----------
    notes_ok = _notes_grounded(llm, knowledge_refs=knowledge_refs, memory_refs=memory_refs)
    if llm is not None and notes_ok:
        folded = 0
        for note in llm.risk_notes:
            text = note.strip()
            if not text:
                continue
            if _is_duplicate(text, [*deterministic_rationale, *additions]):
                continue
            additions.append(f"LLM risk note: {text}")
            folded += 1
        if folded:
            notes.append(
                f"risk notes: folded {folded} grounded LLM risk note(s) into the "
                f"rationale, each labelled and deduped against deterministic lines."
            )
    elif llm is not None and not notes_ok:
        notes.append(
            "risk notes: LLM risk notes withheld — output was not grounded "
            "(no retrieved knowledge/memory and no concrete content)."
        )
    elif llm is None and llm_unparsed_text and llm_provider and llm_provider != "mock_llm":
        # Structured parse failed but a real provider returned prose: keep it as
        # explicitly-labelled, clearly-unstructured guidance (not silent).
        additions.append(f"LLM guidance (unstructured): {llm_unparsed_text[:1200]}")
        notes.append(
            "risk notes: structured parse failed; retained raw provider prose as "
            "labelled unstructured guidance."
        )

    # --- Rule 2: suggested regressions — evidence gate + provenance ---------
    regressions = list(deterministic_regressions)
    if llm is not None and llm.suggested_regressions:
        reg_ok = _regressions_grounded(
            llm, knowledge_refs=knowledge_refs, memory_refs=memory_refs
        )
        if reg_ok:
            admitted: list[str] = []
            dropped_malformed: list[str] = []
            for reg in llm.suggested_regressions:
                cand = reg.strip()
                if not _valid_regression_id(cand):
                    dropped_malformed.append(reg)
                    continue
                if cand in regressions:
                    continue
                regressions.append(cand)
                admitted.append(cand)
            if admitted:
                notes.append(
                    "regressions admitted (LLM-suggested, retrieval-grounded): "
                    f"{', '.join(admitted)}."
                )
            if dropped_malformed:
                notes.append(
                    "regressions dropped (malformed id): "
                    f"{', '.join(repr(r) for r in dropped_malformed)}."
                )
        else:
            notes.append(
                "regressions: "
                f"{len(llm.suggested_regressions)} LLM-suggested regression(s) "
                "withheld from the execution order — not retrieval-grounded "
                "(no knowledge/memory evidence backs them)."
            )

    # --- Rule 3: confidence — grounded blend, never silent ------------------
    base = round(derivation_confidence, 4)
    if llm is not None and notes_ok:
        weight = _LLM_CONFIDENCE_WEIGHT
        confidence = round(base * (1 - weight) + llm.confidence * weight, 4)
        notes.append(
            f"confidence: {confidence} = derivation({base})×{1 - weight:g} "
            f"+ llm({llm.confidence})×{weight:g} (LLM grounded)."
        )
    else:
        confidence = base
        if llm is not None:
            notes.append(
                f"confidence: {confidence} = derivation only "
                f"(LLM ungrounded, its confidence {llm.confidence} discarded)."
            )
        else:
            notes.append(
                f"confidence: {confidence} = derivation only (no parsed LLM signal)."
            )

    return CoverageAdjudication(
        confidence=confidence,
        risk_rationale_additions=additions,
        regressions=regressions,
        notes=notes,
    )
