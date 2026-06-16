from __future__ import annotations

from backend.graph.state import (
    InvestigationBlock,
    InvestigationFinding,
    TestContext,
    utc_now,
)


def investigation_coordinator(context: TestContext) -> TestContext:
    if context.execution is None or context.execution.status == "skipped":
        context.investigation = InvestigationBlock(
            status="skipped",
            generated_at=utc_now(),
            root_cause_summary="Investigation skipped because no real execution evidence is available yet.",
            confidence=0.0,
        )
        context.mark("investigation_skipped")
        return context

    findings: list[InvestigationFinding] = []
    for result in context.execution.results:
        if result.status == "failed":
            findings.append(
                InvestigationFinding(
                    test_case_id=result.test_case_id,
                    severity="high",
                    category="test",
                    summary=result.message,
                    evidence_refs=[ref for ref in [result.robot_file] if ref],
                    confidence=0.65,
                )
            )

    if findings:
        summary = f"Detected {len(findings)} failed generated test case(s)."
        confidence = max(finding.confidence for finding in findings)
    else:
        summary = "No failed generated test cases were observed."
        confidence = 0.85

    context.investigation = InvestigationBlock(
        status="completed",
        generated_at=utc_now(),
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
            "confidence": confidence,
        },
    )
    context.mark("investigation_completed")
    return context
