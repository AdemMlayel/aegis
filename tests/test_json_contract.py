"""Tests for the schema-derived JSON contract injected into LLM prompts.

The contract is built from the SAME Pydantic schemas the parser validates
against, so the prompt instruction and the parser target cannot drift. These
tests pin that invariant: every schema field appears in the contract, and the
worked example is itself a valid instance of the schema.
"""
from __future__ import annotations

import json

import pytest

from backend.intelligence.structured_outputs import (
    CoverageLLMOutput,
    ReportLLMOutput,
    RequirementLLMOutput,
    TestCaseLLMOutput,
    _CONTRACT_EXAMPLES,
    build_json_contract,
)

_SCHEMAS = [
    RequirementLLMOutput,
    CoverageLLMOutput,
    TestCaseLLMOutput,
    ReportLLMOutput,
]


@pytest.mark.parametrize("schema", _SCHEMAS)
def test_contract_lists_every_field(schema) -> None:
    contract = build_json_contract(schema)
    for field_name in schema.model_fields:
        assert field_name in contract, f"{field_name} missing from {schema.__name__} contract"


@pytest.mark.parametrize("schema", _SCHEMAS)
def test_contract_demands_single_json_object(schema) -> None:
    contract = build_json_contract(schema)
    assert "ONE JSON object" in contract
    assert "no markdown" in contract
    assert "no code fences" in contract


@pytest.mark.parametrize("schema", _SCHEMAS)
def test_worked_example_is_valid_instance(schema) -> None:
    # The embedded example must itself validate — otherwise we'd be teaching the
    # model a shape the parser rejects.
    example = _CONTRACT_EXAMPLES[schema.__name__]
    model = schema.model_validate(example)
    # And it must round-trip through the JSON that actually appears in the prompt.
    contract = build_json_contract(schema)
    _, _, json_part = contract.partition("match this shape exactly):\n")
    reparsed = schema.model_validate(json.loads(json_part))
    assert reparsed == model


def test_requirement_checklist_rendered_as_object_not_array() -> None:
    # Regression: 'ChecklistAssessment' contains the substring 'list', which a
    # naive matcher mislabels as an array. It must render as an object.
    contract = build_json_contract(RequirementLLMOutput)
    # find the checklist_assessment line
    line = next(
        ln for ln in contract.splitlines() if ln.strip().startswith("- checklist_assessment:")
    )
    assert "object" in line
    assert "array" not in line


def test_unmapped_schema_raises() -> None:
    from pydantic import BaseModel

    class Unmapped(BaseModel):
        x: int = 0

    with pytest.raises(KeyError):
        build_json_contract(Unmapped)
