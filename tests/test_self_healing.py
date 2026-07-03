"""Tests for the self-healing / locator-repair engine (blueprint Module 10).

Covers the pure scoring engine, the registry-grounded keyword repair, and the
high-level TestContext detector. The engine must never mutate a file or
auto-apply a fix — every suggestion is awaiting_approval.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.reference_corpus.profiles import load_robot_keyword_registry
from backend.chat.intent_classifier import classify_chat_intent
from backend.tools.self_healing import (
    detect_self_healing,
    extract_locator,
    heal_keyword,
    heal_locator,
    is_locator_failure,
)


# --- Locator failure detection ------------------------------------------- #

def test_is_locator_failure_matches_element_not_found() -> None:
    assert is_locator_failure("ElementNotFound: Element with locator id=foo not found")
    assert is_locator_failure("ElementNotInteractableException raised")
    assert is_locator_failure("Unable to locate element: css=.btn")
    assert not is_locator_failure("AssertionError: balance mismatch")


def test_extract_locator_pulls_strategy_and_value() -> None:
    assert extract_locator("ElementNotFound id=submitBtn missing") == ("id", "submitBtn")
    assert extract_locator("css=button.primary not found") == ("css", "button.primary")
    assert extract_locator("no locator here") is None


# --- Locator healing (blueprint worked example) -------------------------- #

def test_heal_locator_recommends_most_similar_stable_candidate() -> None:
    suggestion = heal_locator(
        broken_strategy="id",
        broken_value="submitBtn",
        dom_candidates=[
            ("id", "submitButton"),
            ("css", "button[type=submit]"),
            ("xpath", "//button[text()='Submit']"),
            ("data-testid", "submit-transfer"),
        ],
        robot_file="tests/JIRA-123/TC001.robot",
        line=24,
    )
    # Never auto-applies.
    assert suggestion.status == "awaiting_approval"
    # id=submitButton is both highly similar and high-stability -> wins.
    assert suggestion.recommended is not None
    assert suggestion.recommended.value == "id=submitButton"
    assert suggestion.recommended.stability_label == "high"
    # Candidates are ranked by score descending.
    scores = [c.score for c in suggestion.candidates]
    assert scores == sorted(scores, reverse=True)
    # The brittle xpath candidate is ranked last and labelled low stability.
    assert suggestion.candidates[-1].strategy == "xpath"
    assert suggestion.candidates[-1].stability_label == "low"


def test_heal_locator_with_no_candidates_has_no_recommendation() -> None:
    suggestion = heal_locator(
        broken_strategy="id", broken_value="x", dom_candidates=[]
    )
    assert suggestion.recommended is None
    assert suggestion.confidence == 0.0


# --- Keyword healing against the REAL sanitized registry ----------------- #

def test_heal_keyword_recovers_typo_against_real_registry() -> None:
    registry = load_robot_keyword_registry()["keywords"]
    assert any(k["name"] == "Do Get" for k in registry), "fixture changed"

    suggestion = heal_keyword(
        unknown_keyword="Do Geet",  # typo of a real registry keyword
        registry_keywords=registry,
        used_arg_count=2,
        domain_hint="generic",
    )
    assert suggestion.kind == "keyword"
    assert suggestion.status == "awaiting_approval"
    assert suggestion.recommended is not None
    assert suggestion.recommended.value == "Do Get"
    assert suggestion.confidence > 0.8


def test_heal_keyword_returns_nothing_for_totally_unknown() -> None:
    registry = load_robot_keyword_registry()["keywords"]
    suggestion = heal_keyword(
        unknown_keyword="Zzqxwv Nonsense Keyword 9000",
        registry_keywords=registry,
    )
    # No registry name is similar enough -> no candidates.
    assert suggestion.recommended is None


# --- High-level detector over a TestContext ------------------------------ #

def _ctx_with_robot(robot_text: str, robot_file: str = "gen/TC001.robot"):
    automation = {"TC001": SimpleNamespace(robot_file=robot_file)}
    return SimpleNamespace(execution=None, automation=automation)


def test_detect_self_healing_flags_unknown_keyword() -> None:
    registry = load_robot_keyword_registry()
    robot = (
        "*** Test Cases ***\n"
        "Some Call Test\n"
        "    [Tags]    generated\n"
        "    Log    starting\n"
        "    ${out}    Do Geet    /api/v1/x    params\n"  # typo of 'Do Get'
        "    Should Be Equal    ${out}    ok\n"
    )
    ctx = _ctx_with_robot(robot)
    block = detect_self_healing(
        ctx, registry=registry, read_file=lambda _f: robot
    )
    assert block.status == "completed"
    kw = [s for s in block.suggestions if s.kind == "keyword"]
    assert len(kw) == 1
    assert kw[0].broken_reference == "Do Geet"
    assert kw[0].recommended is not None
    assert kw[0].recommended.value == "Do Get"


def test_detect_self_healing_ignores_valid_keywords() -> None:
    registry = load_robot_keyword_registry()
    robot = (
        "*** Test Cases ***\n"
        "Clean Test\n"
        "    [Documentation]    no broken refs\n"
        "    Log    step 1\n"
        "    Should Be Equal    1    1\n"
        "    Do Get    /api/v1/x    params\n"  # real registry keyword
    )
    ctx = _ctx_with_robot(robot)
    block = detect_self_healing(ctx, registry=registry, read_file=lambda _f: robot)
    assert block.suggestions == []
    assert "No broken" in (block.summary or "")


def test_detect_self_healing_finds_locator_failure_in_execution() -> None:
    registry = load_robot_keyword_registry()
    result = SimpleNamespace(
        test_case_id="TC001",
        status="failed",
        robot_file="gen/TC001.robot",
        message="ElementNotFound: locator id=submitBtn not found",
        logs=["tried id=submitButton", "also saw data-testid=submit-transfer"],
    )
    ctx = SimpleNamespace(
        execution=SimpleNamespace(results=[result]),
        automation={},
    )
    block = detect_self_healing(ctx, registry=registry, read_file=lambda _f: None)
    loc = [s for s in block.suggestions if s.kind == "locator"]
    assert len(loc) == 1
    assert loc[0].broken_reference == "id=submitBtn"
    # Candidate harvested from the logs, recommended is the stable id match.
    assert loc[0].recommended is not None
    assert loc[0].recommended.value == "id=submitButton"
    assert loc[0].status == "awaiting_approval"


def test_detector_never_reports_apply_status() -> None:
    """Defense-in-depth: the detector must never emit an applied/approved fix."""
    registry = load_robot_keyword_registry()
    robot = (
        "*** Test Cases ***\n"
        "T\n"
        "    Frobnicate Widget    a    b\n"
    )
    ctx = _ctx_with_robot(robot)
    block = detect_self_healing(ctx, registry=registry, read_file=lambda _f: robot)
    assert all(s.status == "awaiting_approval" for s in block.suggestions)


# --- Chat intent routing -------------------------------------------------- #


@pytest.mark.parametrize(
    "message",
    [
        "are there any broken locators",
        "what needs healing",
        "run self healing",
        "fix the locators",
        "suggest a fix for the broken keyword",
        "self repair the tests",
        "show me unknown keywords",
    ],
)
def test_self_healing_questions_route_correctly(message: str) -> None:
    assert classify_chat_intent(message).intent == "self_healing_question"


def test_self_healing_does_not_shadow_investigation_or_validation() -> None:
    # "why did it fail" is investigation, not healing.
    assert classify_chat_intent("why did it fail").intent == "investigation_question"
    assert classify_chat_intent("why did validation fail").intent == "validation_question"
    # Generic "fix" without a healing target should not over-trigger healing.
    assert classify_chat_intent("run next stage").intent == "workflow_step"
