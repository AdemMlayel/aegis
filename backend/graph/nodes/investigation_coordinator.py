from __future__ import annotations

import re
from typing import Literal

from backend.graph.state import (
    InvestigationBlock,
    InvestigationEvidenceItem,
    InvestigationFinding,
    TestContext,
    utc_now,
)
from backend.intelligence.evidence_scoring import (
    Category,
    EvidenceProbe,
    ScoreResult,
    aggregate,
    score_probe,
)
from backend.reference_corpus.profiles import (
    load_execution_evidence_profile,
    load_robot_keyword_registry,
)


def investigation_coordinator(context: TestContext) -> TestContext:
    if context.execution is None or context.execution.status == "skipped":
        evidence = [*_collect_execution_profile_evidence(), *_collect_non_execution_evidence(context)]
        context.investigation = InvestigationBlock(
            status="skipped",
            generated_at=utc_now(),
            evidence_items=evidence,
            root_cause_summary=(
                "Investigation skipped because no executable Robot evidence is available. "
                "RAG, model, and workflow evidence were retained for review."
            ),
            confidence=0.0,
        )
        context.mark("investigation_skipped")
        return context

    evidence_items = _collect_execution_evidence(context)
    known_keywords = _registry_keyword_names()
    findings: list[InvestigationFinding] = []
    scored: list[ScoreResult] = []
    for result in context.execution.results:
        related_evidence = [
            item.evidence_id
            for item in evidence_items
            if item.test_case_id == result.test_case_id
        ]
        if result.status == "failed":
            probe = EvidenceProbe(
                status="failed",
                message=result.message or "",
                logs=[log for log in result.logs if log],
                duration_ms=result.duration_ms or 0,
                known_keywords=known_keywords,
                referenced_keywords=_extract_referenced_keywords(result.message, result.logs),
            )
            score = score_probe(probe)
            scored.append(score)
            findings.append(
                InvestigationFinding(
                    test_case_id=result.test_case_id,
                    severity=_severity_for_score(score.score),
                    category=score.dominant_category
                    if score.hits
                    else _classify_failure(result.message, result.logs),
                    summary=result.message,
                    evidence_refs=related_evidence
                    or [ref for ref in [result.robot_file] if ref],
                    confidence=score.confidence,
                    evidence_score=score.score,
                    matched_signals=score.hits,
                    score_basis=score.basis,
                    recommended_actions=_recommended_actions(score),
                )
            )

    overall = aggregate(scored)
    if findings:
        signal_names = ", ".join(hit.signal for hit in overall.hits) or "no weighted signals"
        summary = (
            f"Detected {len(findings)} failed generated test case(s). "
            f"Weighted evidence score {overall.score}/100 "
            f"(signals: {signal_names})."
        )
        confidence = overall.confidence
    else:
        summary = "No failed generated test cases were observed; evidence indicates a clean local execution."
        confidence = 0.0
        overall = ScoreResult(score=0.0, hits=[], basis="clean execution; no failure evidence")

    context.investigation = InvestigationBlock(
        status="completed",
        generated_at=utc_now(),
        evidence_items=evidence_items,
        findings=findings,
        root_cause_summary=summary,
        confidence=confidence,
        evidence_score=overall.score,
        matched_signals=overall.hits,
    )
    context.record_event(
        actor="system",
        event_type="investigation_completed",
        summary=summary,
        metadata={
            "context_id": context.context_id,
            "finding_count": len(findings),
            "evidence_count": len(evidence_items),
            "confidence": confidence,
            "evidence_score": overall.score,
            "matched_signals": [hit.signal for hit in overall.hits],
        },
    )
    context.mark("investigation_completed")
    return context


def _collect_execution_evidence(context: TestContext) -> list[InvestigationEvidenceItem]:
    if context.execution is None:
        return _collect_non_execution_evidence(context)
    evidence: list[InvestigationEvidenceItem] = []
    for result in context.execution.results:
        evidence.append(
            InvestigationEvidenceItem(
                evidence_id=f"exec:{result.test_case_id}",
                kind="robot_result",
                source=result.robot_file or context.execution.adapter,
                summary=f"{result.title} finished with status {result.status} in {result.duration_ms} ms.",
                test_case_id=result.test_case_id,
                severity_hint="high" if result.status == "failed" else "info",
                content_excerpt="\n".join(log for log in result.logs if log)[:800],
            )
        )
    for index, artifact in enumerate(context.execution.artifacts, start=1):
        evidence.append(
            InvestigationEvidenceItem(
                evidence_id=f"artifact:{index}",
                kind="artifact",
                source=artifact.path or artifact.description or "execution artifact",
                summary=artifact.description or artifact.content_type,
                severity_hint="info",
            )
        )
    evidence.extend(_collect_execution_profile_evidence())
    evidence.extend(_collect_non_execution_evidence(context))
    return evidence


def _collect_execution_profile_evidence() -> list[InvestigationEvidenceItem]:
    profile = load_execution_evidence_profile()
    summary = profile.get("summary", {}) if isinstance(profile, dict) else {}
    if not isinstance(summary, dict) or not summary.get("artifact_count"):
        return []

    guidance = profile.get("investigation_guidance", [])
    if not isinstance(guidance, list):
        guidance = []
    has_failed = bool(summary.get("has_failed_example"))
    has_successful = bool(summary.get("has_successful_example"))
    return [
        InvestigationEvidenceItem(
            evidence_id="reference-profile:execution-evidence",
            kind="artifact",
            source="fixtures/reference_corpus/normalized/execution_evidence_profile/profile.json",
            summary=(
                "Sanitized execution evidence profile available "
                f"(success={has_successful}, failed={has_failed})."
            ),
            severity_hint="info",
            content_excerpt="; ".join(str(item) for item in guidance[:4])[:800],
        )
    ]


def _collect_non_execution_evidence(context: TestContext) -> list[InvestigationEvidenceItem]:
    evidence: list[InvestigationEvidenceItem] = []
    for ref in context.intelligence_trace.knowledge_refs[:8]:
        evidence.append(
            InvestigationEvidenceItem(
                evidence_id=f"knowledge:{ref.ref_id}",
                kind="knowledge_ref",
                source=ref.source,
                summary=ref.title,
                content_excerpt=ref.excerpt[:800],
            )
        )
    for ref in context.intelligence_trace.memory_refs[:8]:
        evidence.append(
            InvestigationEvidenceItem(
                evidence_id=f"memory:{ref.ref_id}",
                kind="memory_ref",
                source=ref.source,
                summary=ref.title,
                content_excerpt=ref.excerpt[:800],
            )
        )
    for index, call in enumerate(context.intelligence_trace.llm_calls[-6:], start=1):
        evidence.append(
            InvestigationEvidenceItem(
                evidence_id=f"model:{index}",
                kind="model_trace",
                source=f"{call.provider}/{call.model}",
                summary=f"{call.prompt_name}@{call.prompt_version}",
                content_excerpt=call.summary[:800],
            )
        )
    return evidence


def _classify_failure(message: str, logs: list[str]) -> Category:
    text = " ".join([message, *logs]).lower()
    if any(term in text for term in ("timeout", "connection", "docker", "environment")):
        return "environment"
    if any(term in text for term in ("variable", "data", "fixture", "input")):
        return "data"
    if any(term in text for term in ("keyword", "import", "syntax", "robot")):
        return "test"
    if any(term in text for term in ("assert", "expected", "actual", "mismatch", "failed")):
        return "application"
    return "unknown"


def _severity_for_score(score: float) -> Literal["info", "warning", "high", "critical"]:
    """Map a 0-100 weighted-evidence score to a severity band.

    Thresholds are deterministic and align with the score's meaning: a high
    weighted score means multiple corroborating signals fired, which warrants a
    higher severity than a single weak signal.
    """
    if score >= 70:
        return "critical"
    if score >= 45:
        return "high"
    if score >= 20:
        return "warning"
    return "info"


def _recommended_actions(score: ScoreResult) -> list[str]:
    """Derive next actions from the signals that actually fired, not a fixed list."""
    actions: list[str] = []
    fired = {hit.signal for hit in score.hits}
    if "keyword_resolution_failure" in fired:
        actions.append(
            "Run self-healing: the failing step references a keyword absent from the "
            "registry — review the suggested replacement before re-running."
        )
    if "robot_import_error" in fired:
        actions.append("Verify library/resource imports resolve in the execution environment.")
    if fired & {"http_5xx", "http_4xx", "auth_failure", "contract_breach"}:
        actions.append(
            "Inspect the application response (status, body, auth) — evidence points at "
            "the system under test rather than the generated test."
        )
    if fired & {"timeout", "network_anomaly", "environment_unavailable", "resource_exhaustion"}:
        actions.append("Check environment health (connectivity, containers, resources) before retrying.")
    if fired & {"fixture_data_mismatch", "db_error"}:
        actions.append("Review resolved test data and fixtures for mismatches against expectations.")
    if not actions:
        actions.append("Inspect Robot output and stderr artifacts to localize the failure.")
    actions.append("Check generated keyword/data references before blaming the application.")
    return actions


def _registry_keyword_names() -> frozenset[str]:
    """Real keyword names from the sanitized registry, for keyword-resolution scoring."""
    registry = load_robot_keyword_registry()
    keywords = registry.get("keywords") if isinstance(registry, dict) else None
    names: set[str] = set()
    if isinstance(keywords, list):
        for entry in keywords:
            if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                names.add(entry["name"])
    return frozenset(names)


# Robot step lines reference a keyword as the first cell after indentation.
_KEYWORD_REF_RE = re.compile(r"no keyword with name ['\"]([^'\"]+)['\"]", re.IGNORECASE)


def _extract_referenced_keywords(message: str, logs: list[str]) -> tuple[str, ...]:
    """Pull keyword names that Robot reported as unresolved, from message + logs."""
    text = "\n".join([message, *logs])
    return tuple(dict.fromkeys(_KEYWORD_REF_RE.findall(text)))
