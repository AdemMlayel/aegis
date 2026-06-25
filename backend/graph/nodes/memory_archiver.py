from __future__ import annotations

import json

from backend.graph.artifacts import memory_output_dir, relative_to_project, slug
from backend.graph.state import MemoryArchiveBlock, TestContext, utc_now
from backend.memory import get_local_memory_store


def memory_archiver(context: TestContext) -> TestContext:
    ticket_id = context.ticket.id if context.ticket else context.context_id
    output_dir = memory_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    outcome = "unknown"
    if context.execution is not None:
        outcome = context.execution.status if context.execution.status in {"passed", "failed", "skipped"} else "unknown"

    tags = [
        context.coverage_plan.risk_level if context.coverage_plan else "unknown-risk",
        context.ticket.priority if context.ticket else "unknown-priority",
        context.requirement_analysis.domain if context.requirement_analysis else "unknown-domain",
        "workflow-archive",
    ]
    if context.ticket:
        tags.extend(context.ticket.labels)

    summary = (
        f"Archived workflow memory for {ticket_id}: "
        f"{len(context.test_cases)} tests, approval "
        f"{context.approval.status if context.approval else 'n/a'}, "
        f"execution {context.execution.status if context.execution else 'n/a'}, "
        f"knowledge refs {len(context.intelligence_trace.knowledge_refs)}, "
        f"memory refs {len(context.intelligence_trace.memory_refs)}."
    )

    memory_entry = get_local_memory_store().archive(
        title=f"Workflow memory for {ticket_id}",
        summary=summary,
        tags=tags,
        source_refs=[f"local://workflow/{context.context_id}"],
        outcome=outcome,  # type: ignore[arg-type]
    )

    memory_file = output_dir / f"{slug(ticket_id)}_{memory_entry.memory_id}.json"
    payload = {
        "memory_id": memory_entry.memory_id,
        "title": memory_entry.title,
        "summary": memory_entry.summary,
        "tags": list(memory_entry.tags),
        "source_refs": list(memory_entry.source_refs),
        "outcome": memory_entry.outcome,
        "context_id": context.context_id,
        "ticket_id": ticket_id,
        "ticket_title": context.ticket.title if context.ticket else None,
        "risk_level": context.coverage_plan.risk_level if context.coverage_plan else None,
        "test_case_count": len(context.test_cases),
        "automation_revision": context.automation_revision,
        "approval_status": context.approval.status if context.approval else None,
        "execution_status": context.execution.status if context.execution else None,
        "investigation_status": context.investigation.status if context.investigation else None,
        "knowledge_refs": [ref.ref_id for ref in context.intelligence_trace.knowledge_refs],
        "memory_refs": [ref.ref_id for ref in context.intelligence_trace.memory_refs],
        "prompt_versions": [f"{ref.name}@{ref.version}" for ref in context.intelligence_trace.prompt_versions],
        "llm_provider": context.intelligence_trace.llm_provider,
        "archived_at": utc_now().isoformat(),
    }
    memory_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    context.memory_archive = MemoryArchiveBlock(
        status="archived",
        archived_at=utc_now(),
        memory_id=memory_entry.memory_id,
        summary=summary,
        tags=tags,
        source_refs=[relative_to_project(memory_file)],
        indexed_refs=[memory_entry.memory_id],
    )
    context.record_event(
        actor="system",
        event_type="memory_archived",
        summary="Workflow memory snapshot archived locally and indexed in episodic memory store.",
        metadata={
            "context_id": context.context_id,
            "memory_id": memory_entry.memory_id,
            "path": relative_to_project(memory_file),
            "knowledge_ref_count": len(context.intelligence_trace.knowledge_refs),
            "memory_ref_count": len(context.intelligence_trace.memory_refs),
        },
    )
    context.mark("memory_archived")
    return context
