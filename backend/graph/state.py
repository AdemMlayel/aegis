from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TicketSource(StrEnum):
    FAKE = "fake"
    JIRA = "jira"
    AZURE_DEVOPS = "azure_devops"
    GITLAB = "gitlab"


class TicketData(StrictModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    labels: list[str] = Field(default_factory=list)
    assignee: str | None = None
    source: TicketSource = TicketSource.FAKE
    raw_url: str | None = None


class CompletenessChecklist(StrictModel):
    actor_identified: bool = False
    preconditions_defined: bool = False
    expected_outcome_specified: bool = False
    error_scenarios_mentioned: bool = False
    data_constraints_defined: bool = False
    performance_expectations_set: bool = False


class RequirementAnalysis(StrictModel):
    business_action: str
    domain: str = "unknown"
    actor: str = "user"
    preconditions: list[str] = Field(default_factory=list)
    expected_results: list[str] = Field(default_factory=list)
    completeness_checklist: CompletenessChecklist = Field(
        default_factory=CompletenessChecklist
    )
    missing_fields: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    memory_refs_used: list[str] = Field(default_factory=list)


class CoveragePlan(StrictModel):
    risk_level: Literal["low", "medium", "high", "critical"] = "medium"
    business_criticality: int = Field(default=5, ge=1, le=10)
    test_types_required: list[str] = Field(default_factory=list)
    coverage_matrix: dict[str, list[str]] = Field(default_factory=dict)
    regression_tests_to_rerun: list[str] = Field(default_factory=list)
    estimated_automation_effort: Literal["low", "medium", "high"] = "medium"
    prioritization_order: list[str] = Field(default_factory=list)


class TestCase(StrictModel):
    id: str
    title: str
    type: Literal["functional", "negative", "boundary", "regression", "edge"]
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    requirement_refs: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    expected_outcome: str
    test_data_requirements: dict[str, list[str]] = Field(default_factory=dict)


class TestDataBlock(StrictModel):
    test_case_id: str
    strategy: Literal["factory", "fixture"] = "factory"
    resolved_data: dict[str, list[str]] = Field(default_factory=dict)
    teardown: list[str] = Field(default_factory=list)


class AutomationValidation(StrictModel):
    artifact_exists: bool = False
    dry_run_passed: bool | None = None
    dry_run_skipped_reason: str | None = None
    validation_attempts: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)


class AutomationBlock(StrictModel):
    test_case_id: str
    robot_file: str
    revision: int = Field(default=1, ge=1)
    resource_files: list[str] = Field(default_factory=list)
    data_reference_check_passed: bool = False
    validation: AutomationValidation = Field(default_factory=AutomationValidation)
    generated_at: datetime = Field(default_factory=utc_now)


class ExecutionCaseResult(StrictModel):
    test_case_id: str
    title: str
    status: Literal["passed", "failed", "skipped"]
    duration_ms: int = Field(default=0, ge=0)
    robot_file: str | None = None
    message: str
    logs: list[str] = Field(default_factory=list)


class ExecutionSummary(StrictModel):
    total: int = Field(default=0, ge=0)
    passed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    skipped: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=0, ge=0)


class ExecutionBlock(StrictModel):
    status: Literal["passed", "failed", "skipped"] = "skipped"
    run_by: str
    started_at: datetime
    finished_at: datetime
    summary: ExecutionSummary
    results: list[ExecutionCaseResult] = Field(default_factory=list)


class ReviewFeedback(StrictModel):
    requested_at: datetime = Field(default_factory=utc_now)
    requested_by: str
    comment: str
    status: Literal["open", "applied"] = "open"


AuditEventType = Literal[
    "workflow_started",
    "automation_file_read",
    "approval_requested",
    "approval_decision",
    "git_execution",
    "automation_regenerated",
    "execution_completed",
]


class ApprovalBlock(StrictModel):
    status: Literal["not_ready", "pending_review", "approved", "changes_requested"] = (
        "not_ready"
    )
    requested_at: datetime | None = None
    requested_by: str | None = None
    decided_at: datetime | None = None
    decided_by: str | None = None
    review_items: list[str] = Field(default_factory=list)
    git_branch: str | None = None
    git_pr_url: str | None = None
    git_commit_sha: str | None = None
    git_status: Literal["not_started", "completed", "blocked"] = "not_started"
    git_error: str | None = None
    git_handoff_path: str | None = None
    comments: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AuditEvent(StrictModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=utc_now)
    actor: str
    event_type: AuditEventType
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportBlock(StrictModel):
    generated_at: datetime = Field(default_factory=utc_now)
    summary: str
    total_test_cases: int
    highest_risk: str
    next_actions: list[str] = Field(default_factory=list)


class TestContext(StrictModel):
    context_id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: str = "0.7.0"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by: str
    workflow_status: str = "initialized"

    ticket: TicketData | None = None
    requirement_analysis: RequirementAnalysis | None = None
    coverage_plan: CoveragePlan | None = None
    test_cases: list[TestCase] = Field(default_factory=list)
    test_data: dict[str, TestDataBlock] = Field(default_factory=dict)
    automation_revision: int = 0
    automation: dict[str, AutomationBlock] = Field(default_factory=dict)
    execution: ExecutionBlock | None = None
    approval: ApprovalBlock | None = None
    review_feedback: list[ReviewFeedback] = Field(default_factory=list)
    audit_log: list[AuditEvent] = Field(default_factory=list)
    reports: ReportBlock | None = None

    def mark(self, status: str) -> None:
        self.workflow_status = status
        self.updated_at = utc_now()

    def record_event(
        self,
        *,
        actor: str,
        event_type: AuditEventType,
        summary: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor=actor,
            event_type=event_type,
            summary=summary,
            metadata=metadata or {},
        )
        self.audit_log.append(event)
        self.updated_at = utc_now()
        return event
