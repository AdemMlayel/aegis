"""Phase 5 polish regressions.

Covers:
- N2: self-healing suggestion ids are process-stable (hashlib, not builtin hash()).
- N3: resolved test-data teardown is rendered into the generated .robot file
      as a real executable [Teardown] clause (not a dead model field).
- N4: registry lookup misses raise the typed *RegistrationError, not a bare KeyError.
- S6: the LLM grounding retrieval applies the knowledge relevance floor.
- S8: the provider circuit breaker uses a half-open single-probe and does not
      count an open-circuit rejection as a fresh failure.
"""
from __future__ import annotations

import pytest

from backend.agents import AgentRegistrationError, agent_registry
from backend.config.settings import settings
from backend.governance.gateway import CircuitBreakerRegistry, CircuitOpenError
from backend.graph.state import TestCase, TestDataBlock
from backend.skills import SkillRegistrationError, skill_registry
from backend.tools import ToolRegistrationError, tool_registry
from backend.tools.automation_heuristics import _render_robot_file
from backend.tools.self_healing import heal_keyword, heal_locator


# --- N2: stable suggestion ids -------------------------------------------- #
def test_locator_suggestion_id_is_stable_across_calls() -> None:
    first = heal_locator(
        broken_strategy="id",
        broken_value="login-btn",
        dom_candidates=[("css", ".login")],
        robot_file="tests/login.robot",
        line=12,
    )
    second = heal_locator(
        broken_strategy="id",
        broken_value="login-btn",
        dom_candidates=[("css", ".login")],
        robot_file="tests/login.robot",
        line=12,
    )
    assert first.suggestion_id == second.suggestion_id
    assert first.suggestion_id.startswith("heal-loc-")
    # Deterministic hex digest, not the old salted-hash zero-padded integer.
    digest = first.suggestion_id.removeprefix("heal-loc-")
    assert all(ch in "0123456789abcdef" for ch in digest)


def test_keyword_suggestion_id_is_stable_and_distinct() -> None:
    registry = [{"name": "Open Browser", "library": "SeleniumLibrary", "args": ["url"]}]
    a = heal_keyword(
        unknown_keyword="Open Brwoser",
        registry_keywords=registry,
        robot_file="tests/x.robot",
        line=3,
    )
    b = heal_keyword(
        unknown_keyword="Open Brwoser",
        registry_keywords=registry,
        robot_file="tests/x.robot",
        line=3,
    )
    c = heal_keyword(
        unknown_keyword="Open Brwoser",
        registry_keywords=registry,
        robot_file="tests/x.robot",
        line=99,
    )
    assert a.suggestion_id == b.suggestion_id
    assert a.suggestion_id != c.suggestion_id  # line is part of the identity


# --- N3: teardown is rendered into the generated suite -------------------- #
def _tc() -> TestCase:
    return TestCase(
        id="TC001",
        title="Valid transfer",
        type="functional",
        expected_outcome="Transfer succeeds",
        steps=["Submit transfer"],
        test_data_requirements={"users": ["valid_user"]},
    )


def test_generated_robot_file_renders_teardown_clause() -> None:
    test_data = TestDataBlock(
        test_case_id="TC001",
        strategy="factory",
        resolved_data={"users": ["tc001_valid_user"]},
        teardown=["cleanup_tc001_data"],
    )
    content = _render_robot_file(
        _tc(), "TD-1", 1, [], ticket=None, test_data=test_data
    )
    assert "[Teardown]" in content
    assert "cleanup_tc001_data" in content


def test_generated_robot_file_omits_teardown_when_none() -> None:
    test_data = TestDataBlock(test_case_id="TC001", resolved_data={}, teardown=[])
    content = _render_robot_file(
        _tc(), "TD-1", 1, [], ticket=None, test_data=test_data
    )
    assert "[Teardown]" not in content


# --- N4: typed registration errors on lookup miss ------------------------- #
def test_tool_registry_miss_raises_typed_error() -> None:
    with pytest.raises(ToolRegistrationError):
        tool_registry.get("NoSuchToolEver")


def test_agent_registry_miss_raises_typed_error() -> None:
    with pytest.raises(AgentRegistrationError):
        agent_registry.get("NoSuchAgentEver")


def test_skill_registry_miss_raises_typed_error() -> None:
    with pytest.raises(SkillRegistrationError):
        skill_registry.get("NoSuchSkillEver")


# --- S6: LLM grounding applies the relevance floor ------------------------ #
def test_llm_grounding_retrieval_applies_relevance_floor(monkeypatch) -> None:
    from backend.chat import llm_responder

    class _Chunk:
        chunk_id = "kb-1"
        title = "Irrelevant"

    class _Result:
        def __init__(self, score: float) -> None:
            self.score = score
            self.chunk = _Chunk()
            self.excerpt = "noise"

    class _Store:
        def search(self, *, query: str, limit: int):
            # Everything below the floor -> nothing should be grounded.
            return [_Result(0.05), _Result(0.10)]

    monkeypatch.setattr(
        "backend.knowledge.local.get_local_knowledge_store", lambda: _Store()
    )
    grounding, citations = llm_responder._retrieve_context("unrelated question")
    assert grounding == ""
    assert citations == []


# --- S8: half-open single-probe circuit breaker --------------------------- #
def test_circuit_breaker_half_open_admits_single_probe(monkeypatch) -> None:
    registry = CircuitBreakerRegistry()
    monkeypatch.setattr(settings, "provider_circuit_failure_threshold", 1)
    monkeypatch.setattr(settings, "provider_circuit_reset_seconds", 0)

    # Trip the breaker.
    registry.record_failure("p")
    # reset_seconds=0 -> the window has elapsed, so the next before_call enters
    # half-open and becomes the single probe.
    registry.before_call("p")
    status = registry.status()[0]
    assert status["state"] == "half_open"

    # A second concurrent caller is held back while the probe is in flight.
    with pytest.raises(CircuitOpenError):
        registry.before_call("p")

    # A successful probe fully closes the breaker.
    registry.record_success("p")
    assert registry.status()[0]["state"] == "closed"
    registry.before_call("p")  # closed: no raise


def test_circuit_breaker_failed_probe_reopens(monkeypatch) -> None:
    registry = CircuitBreakerRegistry()
    monkeypatch.setattr(settings, "provider_circuit_failure_threshold", 1)
    monkeypatch.setattr(settings, "provider_circuit_reset_seconds", 0)

    registry.record_failure("p")
    registry.before_call("p")  # enters half-open as the probe
    registry.record_failure("p")  # probe fails -> re-open
    # Immediately after re-open with a fresh (epoch) opened_at, callers are
    # rejected until the next window.
    monkeypatch.setattr(settings, "provider_circuit_reset_seconds", 60)
    with pytest.raises(CircuitOpenError):
        registry.before_call("p")
