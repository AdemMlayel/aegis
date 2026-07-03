from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, Field, ValidationError

from backend.graph.state import TestContext
from backend.llm import LLMResponse


class StructuredParseError(ValueError):
    pass


class RequirementChecklistAssessment(BaseModel):
    """The LLM's independent read on the six completeness items.

    Each field is a tri-state: True (ticket satisfies it), False (it does not),
    or None (the model is unsure / did not assess it). None means "no opinion" and
    the adjudicator falls back to the deterministic heuristic for that item — so a
    model that omits this block entirely degrades gracefully to heuristic-only.
    """

    actor_identified: bool | None = None
    preconditions_defined: bool | None = None
    expected_outcome_specified: bool | None = None
    error_scenarios_mentioned: bool | None = None
    data_constraints_defined: bool | None = None
    performance_expectations_set: bool | None = None


class RequirementLLMOutput(BaseModel):
    summary: str = Field(min_length=1)
    ambiguities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0, le=1)
    checklist_assessment: RequirementChecklistAssessment | None = None


class CoverageLLMOutput(BaseModel):
    risk_notes: list[str] = Field(default_factory=list)
    suggested_regressions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0, le=1)


class TestCaseLLMOutput(BaseModel):
    generation_notes: list[str] = Field(default_factory=list)
    suggested_test_titles: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0, le=1)


class ReportLLMOutput(BaseModel):
    executive_summary: str = Field(min_length=1)
    next_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0, le=1)


# Concrete worked examples per schema. These are the single source of truth for
# the JSON contract injected into prompts — derived from the SAME schemas the
# parser validates against, so the instruction and the parser cannot drift. Each
# example is a minimal, valid instance that demonstrates the exact shape wanted.
_CONTRACT_EXAMPLES: dict[str, dict[str, Any]] = {
    "RequirementLLMOutput": {
        "summary": "Customer transfers funds; insufficient balance must be rejected with no state change.",
        "ambiguities": ["What is the maximum transfer limit?"],
        "confidence": 0.82,
        "checklist_assessment": {
            "actor_identified": True,
            "preconditions_defined": True,
            "expected_outcome_specified": True,
            "error_scenarios_mentioned": True,
            "data_constraints_defined": False,
            "performance_expectations_set": None,
        },
    },
    "CoverageLLMOutput": {
        "risk_notes": ["Concurrent transfers risk double-spend on the same balance."],
        "suggested_regressions": ["REG-BALANCE-CONSISTENCY"],
        "confidence": 0.78,
    },
    "TestCaseLLMOutput": {
        "generation_notes": ["Cover the insufficient-funds rejection path explicitly."],
        "suggested_test_titles": ["Successful transfer", "Insufficient funds rejected", "Minimum boundary transfer"],
        "confidence": 0.76,
    },
    "ReportLLMOutput": {
        "executive_summary": "12 tests generated and validated; all dry-run passed; one negative gap closed.",
        "next_actions": ["Wire the suite to CI", "Review the boundary cases with product"],
        "confidence": 0.8,
    },
}

def _field_type_label(schema: type[BaseModel], field_name: str) -> str:
    field = schema.model_fields[field_name]
    annotation = field.annotation
    text = str(annotation)
    if "RequirementChecklistAssessment" in text:
        return (
            "object with true/false/null flags for actor_identified, "
            "preconditions_defined, expected_outcome_specified, "
            "error_scenarios_mentioned, data_constraints_defined, "
            "performance_expectations_set"
        )
    if "list[" in text:
        return "array of strings"
    if annotation is float or "float" in text:
        return "number between 0 and 1"
    if annotation is str or "'str'" in text:
        return "string (non-empty)"
    return "value"


def build_json_contract(schema: type[BaseModel]) -> str:
    """Build a strict, self-describing JSON contract block for a prompt.

    Emits the exact field list (with types) plus a concrete worked example, both
    derived from ``schema`` so the prompt and the parser share one source of
    truth. This is what turns a vague 'return coverage priorities' instruction
    into a parseable contract.
    """
    example = _CONTRACT_EXAMPLES.get(schema.__name__)
    if example is None:  # pragma: no cover - defensive; all schemas are mapped.
        raise KeyError(f"No JSON contract example registered for {schema.__name__}")
    field_lines = [
        f"  - {name}: {_field_type_label(schema, name)}"
        for name in schema.model_fields
    ]
    example_json = json.dumps(example, indent=2, sort_keys=True)
    return (
        "Respond with ONE JSON object and nothing else — no prose, no markdown, "
        "no code fences, no explanation before or after. The object MUST have "
        "exactly these fields:\n"
        + "\n".join(field_lines)
        + "\n\nExample of a valid response (match this shape exactly):\n"
        + example_json
    )



T = TypeVar("T", bound=BaseModel)


def parse_structured_llm_response(
    *,
    response: LLMResponse,
    schema: type[T],
    context: TestContext | None = None,
) -> T | None:
    """Strictly parse an LLM response into a Pydantic schema.

    This is intentionally non-fatal for local/demo operation: invalid model output
    is recorded and deterministic heuristics remain the source of truth. Once real
    providers are connected, callers can make parse failures blocking per agent.
    """
    status = "parsed"
    error: str | None = None
    parsed: T | None = None
    try:
        payload = _extract_json_object(response.text)
        parsed = schema.model_validate(payload)
    except (StructuredParseError, ValidationError, TypeError, ValueError) as exc:
        status = "fallback"
        error = f"{type(exc).__name__}: {exc}"

    if context is not None:
        context.intelligence_trace.structured_parses.append(
            {
                "prompt_name": response.prompt_name,
                "prompt_version": response.prompt_version,
                "provider": response.provider,
                "model": response.model,
                "schema": schema.__name__,
                "status": status,
                "error": error,
            }
        )
    return parsed


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise StructuredParseError("LLM response was empty")
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        loaded = json.loads(stripped)
    except json.JSONDecodeError as exc:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if match is None:
            raise StructuredParseError(
                "No JSON object found in LLM response"
            ) from exc
        try:
            loaded = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise StructuredParseError("Invalid JSON object in LLM response") from exc
    if not isinstance(loaded, dict):
        raise StructuredParseError("LLM response must be a JSON object")
    return loaded
