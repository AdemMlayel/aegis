export type Priority = "low" | "medium" | "high" | "critical";
export type TicketStatus = "backlog" | "ready" | "in_progress" | "blocked" | "done";
export type ApprovalStatus = "not_ready" | "pending_review" | "approved" | "changes_requested";
export type ExecutionStatus = "passed" | "failed" | "skipped" | "blocked";
export type ExecutionResultStatus = "passed" | "failed" | "skipped";
export type ExecutionRunStatus = ExecutionStatus | "queued" | "running";

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
};

export type RequirementAnalysis = {
  business_action: string;
  domain: string;
  actor: string;
  preconditions: string[];
  expected_results: string[];
  missing_fields: string[];
  clarification_questions: string[];
  memory_refs_used: string[];
  knowledge_refs_used: string[];
  prompt_versions_used: string[];
  llm_summary: string | null;
  confidence: number;
};

export type CoveragePlan = {
  risk_level: Priority;
  business_criticality: number;
  test_types_required: string[];
  coverage_matrix: Record<string, string[]>;
  regression_tests_to_rerun: string[];
  estimated_automation_effort: "low" | "medium" | "high";
  prioritization_order: string[];
  memory_refs_used: string[];
  knowledge_refs_used: string[];
  risk_rationale: string[];
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
  evidence_refs: string[];
  memory_refs: string[];
  generation_notes: string[];
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
  kind: string;
  path: string | null;
  content_type: string;
  description: string;
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
  indexed_refs: string[];
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

export type IntelligenceTrace = {
  llm_provider: string;
  configured_llm_provider: string;
  configured_embedding_provider: string;
  configured_llm_model: string | null;
  configured_embedding_model: string | null;
  knowledge_refs: Array<{ ref_id: string; title: string; source: string; score: number; excerpt: string }>;
  memory_refs: Array<{ ref_id: string; title: string; source: string; score: number; excerpt: string }>;
  prompt_versions: Array<{ name: string; version: string }>;
  llm_calls: Array<{
    provider: string;
    model: string;
    prompt_name: string;
    prompt_version: string;
    deterministic: boolean;
    summary: string;
  }>;
};

export type IntelligenceConfig = {
  llm_provider: string;
  embedding_provider: string;
  llm_model: string | null;
  embedding_model: string | null;
};

export type IntegrationProviderRef = {
  kind: string;
  name: string;
  mode: "mock" | "local" | "external";
  requires_external_api: boolean;
  status: "ready" | "disabled" | "placeholder";
  notes: string[];
};

export type IntegrationProfile = Record<string, IntegrationProviderRef | string | boolean | null>;

export type AuditEvent = {
  id: string;
  created_at: string;
  actor: string;
  event_type: string;
  summary: string;
  metadata: Record<string, unknown>;
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

export type TestContext = {
  context_id: string;
  schema_version: string;
  created_by: string;
  workflow_status: string;
  integration_profile: IntegrationProfile | null;
  intelligence_config: IntelligenceConfig;
  intelligence_trace: IntelligenceTrace;
  ticket: TicketData | null;
  requirement_analysis: RequirementAnalysis | null;
  coverage_plan: CoveragePlan | null;
  test_cases: TestCase[];
  automation_revision: number;
  automation: Record<string, AutomationBlock>;
  execution: ExecutionBlock | null;
  investigation: InvestigationBlock | null;
  memory_archive: MemoryArchiveBlock | null;
  approval: ApprovalBlock | null;
  audit_log: AuditEvent[];
  reports: {
    summary: string;
    total_test_cases: number;
    highest_risk: string;
    next_actions: string[];
    knowledge_refs_used: string[];
    memory_refs_used: string[];
    prompt_versions_used: string[];
    confidence: number;
  } | null;
};

export type ProviderCatalogEntry = {
  kind: string;
  name: string;
  mode: string;
  description: string;
  version: string;
  requires_external_api: boolean;
  enabled: boolean;
  selected: boolean;
  config_key: string | null;
};

export type ProviderCatalog = {
  environment: string;
  external_connectors_enabled: boolean;
  selected: Array<{ kind: string; selected: string; requires_external_api: boolean; status: string }>;
  providers: ProviderCatalogEntry[];
};

export type LLMProvider = {
  name: string;
  mode: string;
  model: string;
  requires_external_api: boolean;
  description: string;
};

export type EmbeddingProvider = {
  name: string;
  mode: string;
  model: string;
  dimensions: number;
  requires_external_api: boolean;
  description: string;
};

export type OllamaHealth = {
  available: boolean;
  base_url: string;
  chat_model: string;
  embedding_model: string;
  installed_models: string[];
  chat_model_ready: boolean;
  embedding_model_ready: boolean;
  message: string;
};

export type ExecutionRunRequest = {
  suite: string;
  adapter: string;
  branch?: string | null;
  env: string;
  tags: string[];
  actor: string;
};

export type ExecuteRunResponse = {
  run_id: string;
  context_id: string;
  status: ExecutionRunStatus;
  worker_backend: string;
  worker_durable: boolean;
  worker_task_id: string | null;
  worker_fallback_used: boolean;
  worker_message: string;
  status_url: string;
  summary_url: string;
  junit_url: string;
  report_url: string;
  logs_url: string;
  websocket_url: string | null;
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
  phase: string;
  status: string | null;
  test_case_id: string | null;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
};
