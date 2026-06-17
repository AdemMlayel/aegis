export type Priority = "low" | "medium" | "high" | "critical";
export type TicketStatus = "backlog" | "ready" | "in_progress" | "blocked" | "done";
export type ApprovalStatus = "not_ready" | "pending_review" | "approved" | "changes_requested";
export type ExecutionStatus = "passed" | "failed" | "skipped";
export type ExecutionResultStatus = "passed" | "failed" | "skipped";
export type ExecutionRunStatus = ExecutionStatus | "queued" | "running" | "blocked";
export type ProviderKind =
  | "ticket_connector"
  | "execution_adapter"
  | "artifact_store"
  | "secret_provider"
  | "git_handoff"
  | "llm_provider"
  | "knowledge_store"
  | "memory_store"
  | "embedding_model"
  | "vector_store"
  | "reranker";
export type ProviderMode = "mock" | "local" | "external";

export type MockTicketComment = {
  author: string;
  body: string;
  created_at: string;
};

export type MockLinkedRequirement = {
  id: string;
  title: string;
  status: "draft" | "approved" | "needs_clarification";
  source: string;
};

export type TicketData = {
  id: string;
  title: string;
  description: string;
  acceptance_criteria: string[];
  priority: Priority;
  labels: string[];
  assignee?: string | null;
  source?: string;
  raw_url?: string | null;
  status?: TicketStatus;
  created_at?: string;
  updated_at?: string;
  comments?: MockTicketComment[];
  linked_requirements?: MockLinkedRequirement[];
};

export type TestCase = {
  id: string;
  title: string;
  type: string;
  priority: Priority;
  requirement_refs: string[];
  preconditions: string[];
  steps: string[];
  expected_outcome: string;
  test_data_requirements: Record<string, string[]>;
};

export type AutomationBlock = {
  test_case_id: string;
  robot_file: string;
  revision: number;
  data_reference_check_passed: boolean;
  validation: {
    artifact_exists: boolean;
    dry_run_passed: boolean | null;
    dry_run_skipped_reason: string | null;
    validation_attempts: number;
    errors: string[];
  };
};

export type ExecutionArtifact = {
  kind: "log" | "junit" | "html" | "robot-output" | "screenshot" | "trace" | "summary";
  path: string | null;
  content_type: string;
  description: string;
};

export type InvestigationBlock = {
  status: "not_started" | "completed" | "skipped";
  generated_at: string | null;
  findings: Array<{
    test_case_id: string | null;
    severity: "info" | "warning" | "high" | "critical";
    category: "test" | "application" | "environment" | "data" | "unknown";
    summary: string;
    evidence_refs: string[];
    confidence: number;
  }>;
  root_cause_summary: string | null;
  confidence: number;
};

export type MemoryArchiveBlock = {
  status: "not_started" | "archived" | "skipped";
  archived_at: string | null;
  memory_id: string | null;
  summary: string | null;
  tags: string[];
  source_refs: string[];
};

export type ExecutionBlock = {
  status: ExecutionStatus;
  run_by: string;
  started_at: string;
  finished_at: string;
  adapter: string;
  env: string;
  summary: {
    total: number;
    passed: number;
    failed: number;
    skipped: number;
    duration_ms: number;
  };
  results: Array<{
    test_case_id: string;
    title: string;
    status: ExecutionResultStatus;
    duration_ms: number;
    robot_file: string | null;
    message: string;
    logs: string[];
  }>;
  artifacts: ExecutionArtifact[];
};

export type ExecutionRunRequest = {
  suite: string;
  adapter: string;
  branch?: string | null;
  env: string;
  tags: string[];
  actor: string;
};

export type ExecutionRunRecord = {
  run_id: string;
  context_id: string;
  request: ExecutionRunRequest;
  status: ExecutionRunStatus;
  execution: ExecutionBlock | null;
  junit_xml: string | null;
  created_at: string;
  updated_at: string;
};

export type ExecutionEvent = {
  id: string;
  run_id: string;
  context_id: string;
  level: "debug" | "info" | "warning" | "error";
  phase:
    | "queued"
    | "running"
    | "case_started"
    | "case_finished"
    | "artifact"
    | "completed"
    | "blocked";
  status: string | null;
  test_case_id: string | null;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ExecuteRunResponse = {
  run_id: string;
  context_id: string;
  status: ExecutionRunStatus;
  status_url: string;
  summary_url: string;
  junit_url: string;
  report_url: string;
  logs_url: string;
  websocket_url: string | null;
};

export type ProviderCatalogEntry = {
  kind: ProviderKind;
  name: string;
  mode: ProviderMode;
  description: string;
  version: string;
  requires_external_api: boolean;
  enabled: boolean;
  selected: boolean;
  config_key: string | null;
  configuration_status?: string;
  configuration_keys?: string[];
};

export type ProviderSelection = {
  kind: ProviderKind;
  selected: string;
  requires_external_api: boolean;
  status: string;
};

export type ProviderCatalog = {
  environment: string;
  external_connectors_enabled: boolean;
  selected: ProviderSelection[];
  providers: ProviderCatalogEntry[];
};

export type IntegrationProviderRef = {
  kind: ProviderKind;
  name: string;
  mode: ProviderMode;
  requires_external_api: boolean;
  status: "ready" | "disabled" | "placeholder";
  notes: string[];
};

export type IntegrationProfile = {
  ticket_connector: IntegrationProviderRef | null;
  execution_adapter: IntegrationProviderRef | null;
  artifact_store: IntegrationProviderRef | null;
  secret_provider: IntegrationProviderRef | null;
  git_handoff: IntegrationProviderRef | null;
  llm_provider: IntegrationProviderRef | null;
  knowledge_store: IntegrationProviderRef | null;
  memory_store: IntegrationProviderRef | null;
  policy: "mock_only" | "local_only" | "external_allowed";
  external_connectors_enabled: boolean;
};

export type PromptTemplate = {
  name: string;
  version: string;
  description: string;
};

export type LLMProvider = {
  name: string;
  mode: ProviderMode;
  model: string;
  requires_external_api: boolean;
  description: string;
  configuration_status?: string;
  configuration_keys?: string[];
};

export type KnowledgeSearchItem = {
  ref_id: string;
  title: string;
  source: string;
  score: number;
  vector_score: number;
  rerank_score: number;
  retention_status: string;
  excerpt: string;
  matched_terms: string[];
};

export type MemorySearchItem = {
  ref_id: string;
  title: string;
  score: number;
  vector_score: number;
  rerank_score: number;
  retention_status: string;
  summary: string;
  tags: string[];
  source_refs: string[];
  matched_terms: string[];
};

export type IntelligenceTrace = {
  llm_provider: string;
  knowledge_refs: Array<{
    ref_id: string;
    source: string;
    title: string;
    score: number;
    excerpt: string;
  }>;
  memory_refs: Array<{
    ref_id: string;
    source: string;
    title: string;
    score: number;
    excerpt: string;
  }>;
  prompt_versions: Array<{
    name: string;
    version: string;
  }>;
  llm_calls: Array<{
    provider: string;
    model: string;
    prompt_name: string;
    prompt_version: string;
    deterministic: boolean;
    summary: string;
  }>;
};

export type ApprovalBlock = {
  status: ApprovalStatus;
  requested_at: string | null;
  requested_by: string | null;
  decided_at: string | null;
  decided_by: string | null;
  review_items: string[];
  git_branch: string | null;
  git_pr_url: string | null;
  git_commit_sha: string | null;
  git_status: "not_started" | "completed" | "blocked";
  git_error: string | null;
  git_handoff_path: string | null;
  comments: string[];
  notes: string[];
};

export type WorkflowSummary = {
  context_id: string;
  ticket_id: string | null;
  ticket_title: string | null;
  workflow_status: string;
  approval_status: ApprovalStatus | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  test_count: number;
  automation_revision: number;
  highest_risk: string | null;
  git_status: "not_started" | "completed" | "blocked" | null;
  execution_status: ExecutionStatus | null;
  execution_passed: number;
  execution_failed: number;
  execution_skipped: number;
  executed_at: string | null;
};

export type AuditEvent = {
  id: string;
  created_at: string;
  actor: string;
  event_type: string;
  summary: string;
  metadata: Record<string, unknown>;
};

export type TestContext = {
  context_id: string;
  schema_version: string;
  created_by: string;
  workflow_status: string;
  ticket: TicketData | null;
  test_cases: TestCase[];
  automation_revision: number;
  automation: Record<string, AutomationBlock>;
  integration_profile: IntegrationProfile | null;
  intelligence_trace: IntelligenceTrace;
  execution_request: {
    requested_by: string;
    requested_at: string;
    adapter: string;
    env: string;
    branch: string | null;
    tags: string[];
    status: "pending" | "deferred" | "running" | "completed" | "blocked";
    blocked_reason: string | null;
  } | null;
  execution: ExecutionBlock | null;
  investigation: InvestigationBlock | null;
  memory_archive: MemoryArchiveBlock | null;
  approval: ApprovalBlock | null;
  review_feedback: Array<{
    requested_at: string;
    requested_by: string;
    comment: string;
    status: "open" | "applied";
  }>;
  audit_log: AuditEvent[];
  reports: {
    summary: string;
    total_test_cases: number;
    highest_risk: string;
    next_actions: string[];
  } | null;
};
