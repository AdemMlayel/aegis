"""Self-Healing / Locator Repair engine.

Implements the blueprint's Module 10 (Self-Healing Agent) grounded in the real
shape of this codebase. Two real broken-reference classes are detected and
repaired — never silently, always human-gated:

1. **Web-style locator failures.** When execution output contains an
   ``ElementNotFound`` / ``ElementNotInteractable`` class error, the failed
   locator (``id=`` / ``css=`` / ``xpath=`` / ``name=``) is extracted and
   candidate replacements are proposed from the page/DOM hints available.

2. **Unknown keyword references.** This corpus is keyword-driven telco/IMS
   automation, not web UI. The dominant real failure mode is a generated or
   edited ``.robot`` step that references a Robot keyword which does not exist
   in the sanitized keyword registry (a renamed / invented keyword). The healer
   matches the unknown keyword against the 238-keyword registry and proposes the
   closest valid keyword.

Scoring is deterministic and explainable (blueprint principle: every locator
suggestion traceable to evidence). A candidate's score is::

    score = similarity * stability_weight

where ``similarity`` is a normalized string similarity to the broken reference
and ``stability_weight`` encodes the blueprint's stability heuristics
(data-testid / id high, class medium, xpath-with-text low; for keywords,
registry membership + argument-count agreement + domain agreement).

Nothing in this module writes to disk or mutates an artifact. It only produces
ranked *suggestions*. Applying a fix is a separate, explicitly confirmed action.
"""
from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from typing import Any, Literal

from backend.graph.state import HealingCandidate, HealingSuggestion, utc_now


def _stable_suggestion_id(prefix: str, *parts: object) -> str:
    """Process-stable suggestion id.

    N2: builtin ``hash()`` is salted per-process (PYTHONHASHSEED), so the same
    break produced a different id on every restart, breaking idempotent
    approve/apply round-trips and audit correlation. A blake2b digest of the
    identifying parts is deterministic across processes.
    """
    payload = "|".join("" if part is None else str(part) for part in parts)
    digest = hashlib.blake2b(payload.encode("utf-8"), digest_size=4).hexdigest()
    return f"{prefix}-{digest}"


# --- Locator stability heuristics (blueprint Module 10) ------------------- #

# Higher = more stable across releases, so a more trustworthy repair target.
_LOCATOR_STABILITY: dict[str, float] = {
    "data-testid": 1.0,   # set by developers explicitly for testing
    "id": 0.9,            # usually stable across releases
    "name": 0.75,         # fairly stable form field identifier
    "css": 0.6,           # medium — often changed in redesigns
    "class": 0.5,         # medium — frequently churned
    "xpath": 0.35,        # low — brittle, especially with text content
    "link": 0.4,
    "tag": 0.3,
    "unknown": 0.4,
}

# Robot Framework exceptions that indicate a broken element reference.
_LOCATOR_ERROR_PATTERNS = (
    "elementnotfound",
    "elementnotinteractable",
    "nosuchelement",
    "element not found",
    "element is not interactable",
    "stale element",
    "unable to locate element",
)

_LOCATOR_RE = re.compile(
    r"\b(data-testid|id|name|css|xpath|class|link|tag)\s*=\s*([^\s'\"]+)",
    re.IGNORECASE,
)


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _stability_label(weight: float) -> Literal["high", "medium", "low"]:
    if weight >= 0.75:
        return "high"
    if weight >= 0.5:
        return "medium"
    return "low"


def is_locator_failure(message: str) -> bool:
    """True when an execution message looks like a broken-element failure."""
    lowered = (message or "").lower()
    return any(pattern in lowered for pattern in _LOCATOR_ERROR_PATTERNS)


def extract_locator(text: str) -> tuple[str, str] | None:
    """Pull the first ``strategy=value`` locator out of a failure message.

    Returns ``(strategy, value)`` lowercased strategy, or ``None``.
    """
    match = _LOCATOR_RE.search(text or "")
    if not match:
        return None
    return match.group(1).lower(), match.group(2)


def heal_locator(
    *,
    broken_strategy: str,
    broken_value: str,
    dom_candidates: list[tuple[str, str]],
    test_case_id: str | None = None,
    robot_file: str | None = None,
    line: int | None = None,
    detected_from: str = "",
    memory_fixes: list[dict[str, str]] | None = None,
) -> HealingSuggestion:
    """Rank candidate web locators for a broken element reference.

    ``dom_candidates`` is a list of ``(strategy, value)`` locators available on
    the current page (in a real Selenium run these come from a DOM snapshot; in
    tests/demo they are provided explicitly). Each is scored by similarity to the
    broken value times the strategy's stability weight.
    """
    candidates: list[HealingCandidate] = []
    for strategy, value in dom_candidates:
        strategy_key = strategy.lower()
        stability = _LOCATOR_STABILITY.get(strategy_key, _LOCATOR_STABILITY["unknown"])
        similarity = _similarity(broken_value, value)
        score = round(similarity * stability, 4)
        candidates.append(
            HealingCandidate(
                value=f"{strategy_key}={value}",
                strategy=strategy_key,
                similarity=round(similarity, 4),
                stability=round(stability, 4),
                score=score,
                stability_label=_stability_label(stability),
                source="dom_snapshot",
                rationale=(
                    f"{strategy_key} locator, similarity {similarity:.2f} to "
                    f"broken value, {_stability_label(stability)} stability"
                ),
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    recommended = candidates[0] if candidates else None

    memory_match = _match_memory_fix(
        f"{broken_strategy}={broken_value}", memory_fixes or []
    )

    suggestion_id = _stable_suggestion_id("heal-loc", robot_file, line, broken_value)
    return HealingSuggestion(
        suggestion_id=suggestion_id,
        kind="locator",
        test_case_id=test_case_id,
        robot_file=robot_file,
        line=line,
        broken_reference=f"{broken_strategy}={broken_value}",
        broken_strategy=broken_strategy,
        detected_from=detected_from,
        candidates=candidates,
        recommended=recommended,
        memory_match=memory_match,
    )


def heal_keyword(
    *,
    unknown_keyword: str,
    registry_keywords: list[dict[str, Any]],
    used_arg_count: int | None = None,
    domain_hint: str | None = None,
    test_case_id: str | None = None,
    robot_file: str | None = None,
    line: int | None = None,
    detected_from: str = "",
    memory_fixes: list[dict[str, str]] | None = None,
    top_n: int = 3,
) -> HealingSuggestion:
    """Rank registry keywords as repairs for an unknown/renamed keyword.

    Stability weight here rewards argument-count agreement and domain agreement,
    because a keyword whose signature matches is a far safer drop-in than one
    that merely has a similar name.
    """
    candidates: list[HealingCandidate] = []
    for entry in registry_keywords:
        name = str(entry.get("name", "")).strip()
        if not name:
            continue
        similarity = _similarity(unknown_keyword, name)
        if similarity < 0.4:
            continue
        # Stability: base registry membership, plus arg-count and domain agreement.
        stability = 0.6
        reg_args = entry.get("args") or []
        if used_arg_count is not None and isinstance(reg_args, list):
            if len(reg_args) == used_arg_count:
                stability += 0.25
            elif abs(len(reg_args) - used_arg_count) == 1:
                stability += 0.1
        if domain_hint and str(entry.get("domain", "")).lower() == domain_hint.lower():
            stability += 0.15
        stability = min(stability, 1.0)
        score = round(similarity * stability, 4)
        candidates.append(
            HealingCandidate(
                value=name,
                strategy="keyword",
                similarity=round(similarity, 4),
                stability=round(stability, 4),
                score=score,
                stability_label=_stability_label(stability),
                source=str(entry.get("library", "registry")),
                rationale=(
                    f"registry keyword from `{entry.get('library', 'unknown')}`, "
                    f"name similarity {similarity:.2f}"
                    + (
                        f", arg-count match ({len(reg_args)})"
                        if used_arg_count is not None and isinstance(reg_args, list)
                        and len(reg_args) == used_arg_count
                        else ""
                    )
                ),
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    candidates = candidates[:top_n]
    recommended = candidates[0] if candidates else None

    memory_match = _match_memory_fix(unknown_keyword, memory_fixes or [])

    suggestion_id = _stable_suggestion_id("heal-kw", robot_file, line, unknown_keyword)
    return HealingSuggestion(
        suggestion_id=suggestion_id,
        kind="keyword",
        test_case_id=test_case_id,
        robot_file=robot_file,
        line=line,
        broken_reference=unknown_keyword,
        broken_strategy="keyword",
        detected_from=detected_from,
        candidates=candidates,
        recommended=recommended,
        memory_match=memory_match,
    )


def _match_memory_fix(broken: str, memory_fixes: list[dict[str, str]]) -> str | None:
    """Find a previously approved fix whose 'from' is similar to the break."""
    best: tuple[float, str] | None = None
    for fix in memory_fixes:
        old = str(fix.get("from", ""))
        if not old:
            continue
        similarity = _similarity(broken, old)
        if similarity >= 0.8 and (best is None or similarity > best[0]):
            label = f"{fix.get('from')} -> {fix.get('to')}"
            ref = fix.get("ref")
            if ref:
                label = f"{label} ({ref})"
            best = (similarity, label)
    return best[1] if best else None


# --- High-level detector: scan a TestContext and produce suggestions ------- #

# Robot keywords that are always valid (BuiltIn + common stdlib libraries),
# so they are never flagged as unknown.
_ALWAYS_VALID_KEYWORDS: frozenset[str] = frozenset(
    name.lower()
    for name in (
        "Log", "Log Many", "Log To Console", "Set Variable", "Should Be Equal",
        "Should Be Equal As Strings", "Should Be True", "Should Contain",
        "Should Not Be Empty", "Should Match", "Run Keyword", "Run Keyword If",
        "Run Keywords", "Sleep", "Wait Until Keyword Succeeds", "Create Dictionary",
        "Create List", "Call Method", "Create Object", "Get Length", "Evaluate",
        "Set Test Variable", "Set Suite Variable", "Set Global Variable",
        "Comment", "No Operation", "Catenate", "Convert To String",
    )
)

# A Robot test-case step line: indented, not a setting/section, first cell is
# the keyword. We only treat lines that look like keyword calls.
_SECTION_RE = re.compile(r"^\*\*\*")
_SETTING_RE = re.compile(r"^\s*\[")
_ASSIGN_RE = re.compile(r"^\s*[\$&@]\{")


def _registry_keyword_names(registry: dict[str, Any]) -> set[str]:
    return {
        str(entry.get("name", "")).strip().lower()
        for entry in registry.get("keywords", [])
        if entry.get("name")
    }


def _extract_keyword_calls(robot_text: str) -> list[tuple[int, str, int]]:
    """Return ``(line_no, keyword_name, arg_count)`` for keyword-call lines.

    Best-effort Robot parsing: a step is an indented line whose first non-empty
    cell (cells separated by 2+ spaces or tabs) is a keyword. Assignment lines
    (``${x}    Keyword``) use the cell after the assignment as the keyword.
    """
    calls: list[tuple[int, str, int]] = []
    in_test_cases = False
    for idx, raw in enumerate(robot_text.splitlines(), start=1):
        if _SECTION_RE.match(raw):
            in_test_cases = "test case" in raw.lower()
            continue
        if not in_test_cases:
            continue
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not (raw.startswith(" ") or raw.startswith("\t")):
            continue  # test-case title line, not a step
        if _SETTING_RE.match(raw):
            continue  # [Tags]/[Documentation]/...
        cells = [c for c in re.split(r"\t|\s{2,}", raw.strip()) if c]
        if not cells:
            continue
        # Skip leading assignment cells like ${x} or &{d}
        keyword_idx = 0
        while keyword_idx < len(cells) and _ASSIGN_RE.match(cells[keyword_idx]):
            keyword_idx += 1
        if keyword_idx >= len(cells):
            continue
        keyword = cells[keyword_idx]
        arg_count = len(cells) - keyword_idx - 1
        calls.append((idx, keyword, arg_count))
    return calls


def detect_self_healing(
    context: Any,
    *,
    registry: dict[str, Any] | None = None,
    memory_fixes: list[dict[str, str]] | None = None,
    read_file=None,
):
    """Scan a TestContext for broken references and build a SelfHealingBlock.

    Two real detection paths:

    1. **Locator failures** in execution results (``ElementNotFound`` class).
    2. **Unknown keyword references** in generated ``.robot`` files — any
       keyword call whose name is neither an always-valid BuiltIn keyword nor
       present in the sanitized keyword registry is flagged and a closest-match
       repair is proposed.

    Returns a populated ``SelfHealingBlock`` (imported lazily to avoid import
    cycles). Never modifies any file.
    """
    from backend.graph.state import SelfHealingBlock  # local import: avoid cycle

    if registry is None:
        from backend.reference_corpus.profiles import load_robot_keyword_registry

        registry = load_robot_keyword_registry()
    if read_file is None:
        read_file = _default_read_robot

    registry_names = _registry_keyword_names(registry)
    registry_keywords = list(registry.get("keywords", []))
    suggestions: list[HealingSuggestion] = []

    # Path 1 — locator failures from execution.
    execution = getattr(context, "execution", None)
    if execution is not None:
        for result in getattr(execution, "results", []):
            if result.status != "failed" or not is_locator_failure(result.message):
                continue
            extracted = extract_locator(result.message) or _extract_from_logs(result.logs)
            if extracted is None:
                continue
            strategy, value = extracted
            suggestions.append(
                heal_locator(
                    broken_strategy=strategy,
                    broken_value=value,
                    dom_candidates=_dom_hints_from_logs(result.logs),
                    test_case_id=result.test_case_id,
                    robot_file=result.robot_file,
                    detected_from=f"execution failure: {result.message[:120]}",
                    memory_fixes=memory_fixes,
                )
            )

    # Path 2 — unknown keyword references in generated automation files.
    automation = getattr(context, "automation", None) or {}
    for test_id, block in automation.items():
        robot_file = getattr(block, "robot_file", None)
        if not robot_file:
            continue
        text = read_file(robot_file)
        if not text:
            continue
        for line_no, keyword, arg_count in _extract_keyword_calls(text):
            kw_lower = keyword.lower()
            if kw_lower in _ALWAYS_VALID_KEYWORDS or kw_lower in registry_names:
                continue
            suggestion = heal_keyword(
                unknown_keyword=keyword,
                registry_keywords=registry_keywords,
                used_arg_count=arg_count,
                test_case_id=test_id,
                robot_file=robot_file,
                line=line_no,
                detected_from="keyword not found in registry or BuiltIn",
                memory_fixes=memory_fixes,
            )
            # Only surface a suggestion if we found a plausible repair.
            if suggestion.recommended is not None:
                suggestions.append(suggestion)

    locator_count = sum(1 for s in suggestions if s.kind == "locator")
    keyword_count = sum(1 for s in suggestions if s.kind == "keyword")
    if suggestions:
        summary = (
            f"Detected {len(suggestions)} broken reference(s): "
            f"{locator_count} locator, {keyword_count} keyword. "
            "All repairs are suggestions awaiting human approval — no file changed."
        )
    else:
        summary = "No broken locators or unknown keyword references detected."

    return SelfHealingBlock(
        status="completed",
        generated_at=utc_now(),
        suggestions=suggestions,
        summary=summary,
    )


def _extract_from_logs(logs: list[str]) -> tuple[str, str] | None:
    for line in logs or []:
        found = extract_locator(line)
        if found:
            return found
    return None

def _dom_hints_from_logs(logs: list[str]) -> list[tuple[str, str]]:
    """Pull candidate ``strategy=value`` locators mentioned in logs.

    In a real Selenium run these come from a DOM snapshot; here we harvest any
    locators present in the captured logs so the demo is grounded in real data
    rather than fabricated candidates.
    """
    hints: list[tuple[str, str]] = []
    for line in logs or []:
        for match in _LOCATOR_RE.finditer(line):
            hints.append((match.group(1).lower(), match.group(2)))
    return hints


def _default_read_robot(robot_file: str) -> str | None:
    from backend.graph.artifacts import GENERATED_ROOT, PROJECT_ROOT

    for base in (GENERATED_ROOT.parent, PROJECT_ROOT):
        candidate = (base / robot_file).resolve()
        try:
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8")
        except OSError:
            continue
    return None
