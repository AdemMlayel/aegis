from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, Field, ValidationError

from backend.graph.state import TestContext
from backend.llm import LLMResponse


class StructuredParseError(ValueError):
    pass


class RequirementLLMOutput(BaseModel):
    summary: str = Field(min_length=1)
    ambiguities: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0, le=1)


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
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if match is None:
            raise StructuredParseError("No JSON object found in LLM response")
        try:
            loaded = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise StructuredParseError("Invalid JSON object in LLM response") from exc
    if not isinstance(loaded, dict):
        raise StructuredParseError("LLM response must be a JSON object")
    return loaded
