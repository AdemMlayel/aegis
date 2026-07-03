"""Requirement-analysis adjudication (Layer 2 reasoning).

The requirement stage produces two independent signals about a ticket:

* a **deterministic heuristic** — a six-item completeness checklist computed by
  keyword-spotting (``"auth" in description`` etc.) plus the clarification
  questions implied by any unmet items, and
* an **LLM reading** — a free-text summary, a list of ambiguities, a self-reported
  confidence, and (when the model cooperates) an independent tri-state assessment
  of the same six checklist items.

Previously these were *stapled together*, not reconciled: clarification questions
were concatenated (duplicates, contradictions), confidence blindly took the LLM's
number whenever present (a confident-but-ungrounded model won), and the checklist
booleans never got a second opinion — so a brittle keyword miss produced a bogus
"please clarify" question even when the LLM clearly identified the information.

This module reconciles the two with **explicit, recorded rules**. Every override
is appended to ``adjudication_notes`` so the final analysis is auditable, the same
way investigation confidence is traceable to its weighted signals.

Reconciliation rules
---------------------
1. **Checklist (union with provenance).** An item is satisfied if the heuristic
   OR a confident LLM affirms it. The LLM can only *raise* an item the heuristic
   missed (recall fix); it never silently clears an item the heuristic set, and a
   model "no opinion" (None) leaves the heuristic untouched. Every flip is noted.
2. **Confidence (grounded reconciliation).** Start from a heuristic-grounded base
   driven by how many checklist items are satisfied. Move toward the LLM's
   confidence only to the extent the LLM is *grounded* (parsed, non-empty summary,
   used real knowledge/memory). An ungrounded-but-confident LLM is discounted.
3. **Clarification questions (dedup + conflict resolution).** Union heuristic
   questions with LLM ambiguities, drop any heuristic question whose checklist
   item was just satisfied by adjudication, and dedup near-duplicates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from backend.graph.state import CompletenessChecklist
from backend.intelligence.structured_outputs import RequirementLLMOutput

# Maps a checklist field to the heuristic clarification question it triggers, so
# adjudication can retract a question once the item is satisfied.
_ITEM_TO_QUESTION: dict[str, str] = {
    "preconditions_defined": "What setup or authentication state is required?",
    "error_scenarios_mentioned": "Which error states should be tested?",
    "data_constraints_defined": "What input limits, formats, or currencies apply?",
}

_CHECKLIST_FIELDS = (
    "actor_identified",
    "preconditions_defined",
    "expected_outcome_specified",
    "error_scenarios_mentioned",
    "data_constraints_defined",
    "performance_expectations_set",
)


@dataclass
class AdjudicationResult:
    checklist: CompletenessChecklist
    confidence: float
    clarification_questions: list[str]
    notes: list[str] = field(default_factory=list)


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _dedup_questions(questions: list[str], threshold: float = 0.86) -> list[str]:
    """Drop empty and near-duplicate questions, preserving first-seen order."""
    kept: list[str] = []
    for q in questions:
        q = q.strip()
        if not q:
            continue
        if any(_similar(q, existing) >= threshold for existing in kept):
            continue
        kept.append(q)
    return kept


def _llm_is_grounded(llm: RequirementLLMOutput | None, *, knowledge_refs: int, memory_refs: int) -> bool:
    """The LLM signal is trustworthy only if it parsed and is evidence-grounded."""
    if llm is None:
        return False
    if not llm.summary or not llm.summary.strip():
        return False
    # A real reading either retrieved supporting context or surfaced ambiguities.
    return bool(knowledge_refs or memory_refs or llm.ambiguities)


def adjudicate_requirement_analysis(
    *,
    heuristic_checklist: CompletenessChecklist,
    heuristic_questions: list[str],
    llm: RequirementLLMOutput | None,
    heuristic_confidence: float,
    knowledge_refs: int = 0,
    memory_refs: int = 0,
) -> AdjudicationResult:
    """Reconcile heuristic and LLM requirement signals with traceable rules."""
    notes: list[str] = []
    grounded = _llm_is_grounded(llm, knowledge_refs=knowledge_refs, memory_refs=memory_refs)

    # --- Rule 1: checklist union with provenance ----------------------------
    reconciled = heuristic_checklist.model_copy(deep=True)
    satisfied_by_llm: set[str] = set()
    assessment = llm.checklist_assessment if (llm and grounded) else None
    if assessment is not None:
        for item_field in _CHECKLIST_FIELDS:
            heuristic_val = getattr(reconciled, item_field)
            llm_val = getattr(assessment, item_field)
            if llm_val is True and heuristic_val is False:
                setattr(reconciled, item_field, True)
                satisfied_by_llm.add(item_field)
                notes.append(
                    f"checklist: '{item_field}' raised False→True — heuristic keyword "
                    f"match missed it but the grounded LLM affirmed it."
                )
            elif llm_val is False and heuristic_val is True:
                # The LLM disagrees downward. We do NOT clear a heuristic-confirmed
                # item (keyword evidence is concrete), but we record the dissent.
                notes.append(
                    f"checklist: '{item_field}' kept True despite LLM dissent — "
                    f"deterministic keyword evidence is authoritative for clears."
                )
    elif llm is not None and not grounded:
        notes.append(
            "checklist: LLM assessment ignored — model output was not grounded "
            "(no retrieved knowledge/memory and no ambiguities surfaced)."
        )

    # --- Rule 2: grounded confidence reconciliation -------------------------
    satisfied_count = sum(1 for f in _CHECKLIST_FIELDS if getattr(reconciled, f))
    # Heuristic-grounded base: 0.5 floor, +~0.083 per satisfied item → 0.5..1.0.
    heuristic_base = round(0.5 + (satisfied_count / len(_CHECKLIST_FIELDS)) * 0.5, 4)
    if llm is not None and grounded:
        # Blend toward the LLM only as far as it is grounded. Weight is modest
        # (0.35) so a confident hallucination cannot dominate concrete checklist
        # evidence.
        llm_weight = 0.35
        reconciled_confidence = round(
            heuristic_base * (1 - llm_weight) + llm.confidence * llm_weight, 4
        )
        notes.append(
            f"confidence: {reconciled_confidence} = heuristic_base({heuristic_base}) "
            f"×{1 - llm_weight:g} + llm({llm.confidence})×{llm_weight:g} "
            f"[{satisfied_count}/{len(_CHECKLIST_FIELDS)} items satisfied]."
        )
    else:
        reconciled_confidence = heuristic_base
        if llm is not None:
            notes.append(
                f"confidence: {reconciled_confidence} = heuristic_base only "
                f"(LLM ungrounded, its confidence discarded)."
            )
        else:
            notes.append(
                f"confidence: {reconciled_confidence} = heuristic_base only "
                f"(no LLM signal available)."
            )

    # --- Rule 3: clarification dedup + conflict resolution ------------------
    retracted = {
        _ITEM_TO_QUESTION[item]
        for item in satisfied_by_llm
        if item in _ITEM_TO_QUESTION
    }
    surviving_heuristic = [q for q in heuristic_questions if q.strip() not in retracted]
    for dropped in retracted:
        notes.append(
            f"question retracted: '{dropped}' — the related checklist item was "
            f"satisfied during adjudication."
        )
    llm_ambiguities = list(llm.ambiguities) if (llm and grounded) else []
    questions = _dedup_questions([*surviving_heuristic, *llm_ambiguities])

    return AdjudicationResult(
        checklist=reconciled,
        confidence=reconciled_confidence,
        clarification_questions=questions,
        notes=notes,
    )
