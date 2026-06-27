from __future__ import annotations

from backend.graph.state import (
    InvestigationBlock,
    InvestigationEvidenceItem,
    InvestigationFinding,
    TestContext,
    utc_now,
)


def investigation_coordinator(context: TestContext) -> TestContext:
    if context.execution is None or context.execution.status == "skipped":
        evidence = _collect_non_execution_evidence(context)
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
    findings: list[InvestigationFinding] = []
    for result in context.execution.results:
        related_evidence = [
            item.evidence_id
            for item in evidence_items
            if item.test_case_id == result.test_case_id
        ]
        if result.status == "failed":
            findings.append(
                InvestigationFinding(
                    test_case_id=result.test_case_id,
                    severity="high",
                    category=_classify_failure(result.message, result.logs),
                    summary=result.message,
                    evidence_refs=related_evidence or [ref for ref in [result.robot_file] if ref],
                    confidence=0.72 if related_evidence else 0.6,
                    recommended_actions=[
                        "Inspect Robot output and stderr artifacts.",
                        "Check generated keyword/data references before blaming the application.",
                    ],
                )
            )

    if findings:
        summary = f"Detected {len(findings)} failed generated test case(s) with linked execution evidence."
        confidence = max(finding.confidence for finding in findings)
    else:
        summary = "No failed generated test cases were observed; evidence indicates a clean local execution."
        confidence = 0.88 if evidence_items else 0.72

    context.investigation = InvestigationBlock(
        status="completed",
        generated_at=utc_now(),
        evidence_items=evidence_items,
        findings=findings,
        root_cause_summary=summary,
        confidence=confidence,
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
    evidence.extend(_collect_non_execution_evidence(context))
    return evidence


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


def _classify_failure(message: str, logs: list[str]) -> str:
    text = " ".join([message, *logs]).lower()
    if any(term in text for term in ("timeout", "connection", "docker", "environment")):
        return "environment"
    if any(term in text for term in ("variable", "data", "fixture", "input")):
        return "data"
    if any(term in text for term in ("keyword", "import", "syntax", "robot")):
        return "test"
    return "unknown"
