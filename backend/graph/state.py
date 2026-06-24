from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from backend.config.settings import settings


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


class IntelligenceEvidenceRef(StrictModel):
    ref_id: str
    source: str
    title: str
    score: float = Field(default=0.0, ge=0, le=1)
    excerpt: str = ""


class PromptUsageRef(StrictModel):
    name: str
    version: str


class LLMUsageRef(StrictModel):
    provider: str
    model: str
    prompt_name: str
    prompt_version: str
    deterministic: bool = True
    agent_name: str | None = None
    model_role: str | None = None
    requested_model: str | None = None
    summary: str


class AgentModelRouteBlock(StrictModel):
    provider: str = Field(min_length=1)
    model: str | None = None


class IntelligenceTraceBlock(StrictModel):
    llm_provider: str = "mock_llm"
    configured_llm_provider: str = Field(default_factory=lambda: settings.default_llm_provider)
    configured_embedding_provider: str = Field(default_factory=lambda: settings.default_embedding_provider)
    configured_llm_model: str | None = None
    configured_embedding_model: str | None = None
    configured_agent_routes: dict[str, AgentModelRouteBlock] = Field(default_factory=dict)
    knowledge_refs: list[IntelligenceEvidenceRef] = Field(default_factory=list)
    memory_refs: list[IntelligenceEvidenceRef] = Field(default_factory=list)
    prompt_versions: list[PromptUsageRef] = Field(default_factory=list)
    llm_calls: list[LLMUsageRef] = Field(default_factory=list)


class IntelligenceConfigBlock(StrictModel):
    llm_provider: str = Field(default_factory=lambda: settings.default_llm_provider)
    embedding_provider: str = Field(default_factory=lambda: settings.default_embedding_provider)
    llm_model: str | None = None
    embedding_model: str | None = None
    agent_routes: dict[str, AgentModelRouteBlock] = Field(default_factory=dict)


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
    knowledge_refs_used: list[str] = Field(default_factory=list)
    prompt_versions_used: list[str] = Field(default_factory=list)
    llm_summary: str | None = None
    confidence: float = Field(default=0.7, ge=0, le=1)


class CoveragePlan(StrictModel):
    risk_level: Literal["low", "medium", "high", "critical"] = "medium"
    business_criticality: int = Field(default=5, ge=1, le=10)
    test_types_required: list[str] = Field(default_factory=list)
    coverage_matrix: dict[str, list[str]] = Field(default_factory=dict)
    regression_tests_to_rerun: list[str] = Field(default_factory=list)
    estimated_automation_effort: Literal["low", "medium", "high"] = "medium"
    prioritization_order: list[str] = Field(default_factory=list)
    memory_refs_used: list[str] = Field(default_factory=list)
    knowledge_refs_used: list[str] = Field(default_factory=list)
    risk_rationale: list[str] = Field(default_factory=list)


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
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    generation_notes: list[str] = Field(default_factory=list)


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


class ValidationSummary(StrictModel):
    generated_at: datetime = Field(default_factory=utc_now)
    status: Literal["passed", "warning", "failed"] = "failed"
    total_artifacts: int = Field(default=0, ge=0)
    passed_artifacts: int = Field(default=0, ge=0)
    failed_artifacts: int = Field(default=0, ge=0)
    requirement_coverage_percent: int = Field(default=0, ge=0, le=100)
    artifact_pass_percent: int = Field(default=0, ge=0, le=100)
    data_reference_percent: int = Field(default=0, ge=0, le=100)
    requirement_completeness_percent: int = Field(default=0, ge=0, le=100)
    quality_score: int = Field(default=0, ge=0, le=100)
    missing_requirements: list[str] = Field(default_factory=list)
    risk_areas: list[str] = Field(default_factory=list)
    validator_mode: Literal[
        "robot_dry_run",
        "local_structural",
        "mixed",
        "not_run",
    ] = "not_run"
    total_attempts: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=0, ge=0)


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


class ExecutionArtifact(StrictModel):
    kind: Literal["log", "junit", "html", "robot-output", "screenshot", "trace", "summary"]
    path: str | None = None
    content_type: str = "text/plain"
    description: str = ""


class ExecutionRequestBlock(StrictModel):
    requested_by: str = "system"
    requested_at: datetime = Field(default_factory=utc_now)
    adapter: str = "mock"
    env: str = "local"
    branch: str | None = None
    tags: list[str] = Field(default_factory=list)
    status: Literal["pending", "deferred", "running", "completed", "blocked"] = "pending"
    blocked_reason: str | None = None


class ExecutionBlock(StrictModel):
    status: Literal["passed", "failed", "skipped", "blocked"] = "skipped"
    run_by: str
    started_at: datetime
    finished_at: datetime
    summary: ExecutionSummary
    results: list[ExecutionCaseResult] = Field(default_factory=list)
    adapter: str = "mock"
    env: str = "local"
    artifacts: list[ExecutionArtifact] = Field(default_factory=list)


class InvestigationFinding(StrictModel):
    test_case_id: str | None = None
    severity: Literal["info", "warning", "high", "critical"] = "info"
    category: Literal["test", "application", "environment", "data", "unknown"] = "unknown"
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)


class InvestigationBlock(StrictModel):
    status: Literal["not_started", "completed", "skipped"] = "not_started"
    generated_at: datetime | None = None
    findings: list[InvestigationFinding] = Field(default_factory=list)
    root_cause_summary: str | None = None
    confidence: float = Field(default=0.0, ge=0, le=1)


class MemoryArchiveBlock(StrictModel):
    status: Literal["not_started", "archived", "skipped"] = "not_started"
    archived_at: datetime | None = None
    memory_id: str | None = None
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    indexed_refs: list[str] = Field(default_factory=list)


WorkflowStageName = Literal[
    "ticket",
    "requirements",
    "coverage",
    "tests",
    "automation",
    "validation",
    "approval",
    "report",
]


class ReviewFeedback(StrictModel):
    requested_at: datetime = Field(default_factory=utc_now)
    requested_by: str
    comment: str
    stage: WorkflowStageName | None = None
    status: Literal["open", "applied"] = "open"


class StageReviewBlock(StrictModel):
    stage: WorkflowStageName
    revision: int = Field(default=1, ge=1)
    status: Literal[
        "not_requested",
        "pending",
        "approved",
        "changes_requested",
    ] = "not_requested"
    requested_at: datetime | None = None
    requested_by: str | None = None
    decided_at: datetime | None = None
    decided_by: str | None = None
    comments: list[str] = Field(default_factory=list)


class WorkflowControlBlock(StrictModel):
    mode: Literal["autonomous", "approval_required", "step_by_step"] = "autonomous"
    state: Literal[
        "initialized",
        "running",
        "paused",
        "waiting_review",
        "completed",
        "failed",
    ] = "initialized"
    current_stage: WorkflowStageName | None = None
    next_stage: WorkflowStageName | None = "ticket"
    pause_requested: bool = False
    completed_stages: list[WorkflowStageName] = Field(default_factory=list)
    stage_revisions: dict[str, int] = Field(default_factory=dict)
    stage_reviews: dict[str, StageReviewBlock] = Field(default_factory=dict)
    last_error: str | None = None


AuditEventType = Literal[
    "workflow_started",
    "automation_file_read",
    "approval_requested",
    "approval_decision",
    "git_execution",
    "automation_regenerated",
    "automation_validation_retry",
    "execution_completed",
    "investigation_completed",
    "memory_archived",
    "tool_invoked",
    "workflow_control",
    "stage_review",
    "artifact_revision",
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
    knowledge_refs_used: list[str] = Field(default_factory=list)
    memory_refs_used: list[str] = Field(default_factory=list)
    prompt_versions_used: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0, le=1)


class WorkflowTraceEvent(StrictModel):
    node_name: str
    status: Literal["started", "completed", "failed", "routed"]
    timestamp: datetime = Field(default_factory=utc_now)
    iteration: int = Field(default=1, ge=1)
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntegrationProviderRef(StrictModel):
    kind: Literal["ticket_connector", "execution_adapter", "artifact_store", "secret_provider", "git_handoff", "llm_provider", "knowledge_store", "memory_store", "embedding_provider"]
    name: str
    mode: Literal["mock", "local", "external"] = "local"
    requires_external_api: bool = False
    status: Literal["ready", "disabled", "placeholder"] = "ready"
    notes: list[str] = Field(default_factory=list)


class IntegrationProfileBlock(StrictModel):
    ticket_connector: IntegrationProviderRef | None = None
    execution_adapter: IntegrationProviderRef | None = None
    artifact_store: IntegrationProviderRef | None = None
    secret_provider: IntegrationProviderRef | None = None
    git_handoff: IntegrationProviderRef | None = None
    llm_provider: IntegrationProviderRef | None = None
    knowledge_store: IntegrationProviderRef | None = None
    memory_store: IntegrationProviderRef | None = None
    embedding_provider: IntegrationProviderRef | None = None
    policy: Literal["mock_only", "local_only", "external_allowed"] = "mock_only"
    external_connectors_enabled: bool = False


class TestContext(StrictModel):
    context_id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: str = settings.workflow_schema_version
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by: str
    workflow_status: str = "initialized"
    current_node: str | None = None
    graph_iteration: int = Field(default=1, ge=1)
    validation_retry_count: int = Field(default=0, ge=0)
    max_validation_retries: int = Field(default=2, ge=0, le=5)
    workflow_trace: list[WorkflowTraceEvent] = Field(default_factory=list)
    workflow_control: WorkflowControlBlock = Field(default_factory=WorkflowControlBlock)

    integration_profile: IntegrationProfileBlock | None = None
    intelligence_config: IntelligenceConfigBlock = Field(default_factory=IntelligenceConfigBlock)
    intelligence_trace: IntelligenceTraceBlock = Field(default_factory=IntelligenceTraceBlock)

    ticket: TicketData | None = None
    requirement_analysis: RequirementAnalysis | None = None
    coverage_plan: CoveragePlan | None = None
    test_cases: list[TestCase] = Field(default_factory=list)
    test_data: dict[str, TestDataBlock] = Field(default_factory=dict)
    automation_revision: int = 0
    automation: dict[str, AutomationBlock] = Field(default_factory=dict)
    validation_summary: ValidationSummary | None = None
    execution_request: ExecutionRequestBlock | None = None
    execution: ExecutionBlock | None = None
    investigation: InvestigationBlock | None = None
    memory_archive: MemoryArchiveBlock | None = None
    approval: ApprovalBlock | None = None
    review_feedback: list[ReviewFeedback] = Field(default_factory=list)
    audit_log: list[AuditEvent] = Field(default_factory=list)
    reports: ReportBlock | None = None

    def sync_intelligence_trace_config(self) -> None:
        self.intelligence_trace.configured_llm_provider = self.intelligence_config.llm_provider
        self.intelligence_trace.configured_embedding_provider = self.intelligence_config.embedding_provider
        self.intelligence_trace.configured_llm_model = self.intelligence_config.llm_model
        self.intelligence_trace.configured_embedding_model = self.intelligence_config.embedding_model
        self.intelligence_trace.configured_agent_routes = {
            agent_name: route.model_copy(deep=True)
            for agent_name, route in self.intelligence_config.agent_routes.items()
        }

    def mark(self, status: str) -> None:
        self.workflow_status = status
        self.updated_at = utc_now()

    def trace_node(
        self,
        *,
        node_name: str,
        status: Literal["started", "completed", "failed", "routed"],
        summary: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowTraceEvent:
        self.current_node = node_name
        trace = WorkflowTraceEvent(
            node_name=node_name,
            status=status,
            iteration=self.graph_iteration,
            summary=summary,
            metadata=metadata or {},
        )
        self.workflow_trace.append(trace)
        self.updated_at = utc_now()
        return trace

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
