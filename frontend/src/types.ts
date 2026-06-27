export type Priority = "low" | "medium" | "high" | "critical";
export type TicketStatus = "backlog" | "ready" | "in_progress" | "blocked" | "done";
export type ApprovalStatus = "not_ready" | "pending_review" | "approved" | "changes_requested";
export type ExecutionStatus = "passed" | "failed" | "skipped" | "blocked";
export type ExecutionResultStatus = "passed" | "failed" | "skipped";
export type ExecutionRunStatus = ExecutionStatus | "queued" | "running";
export type WorkflowStageName =
  | "ticket"
  | "requirements"
  | "coverage"
  | "tests"
  | "automation"
  | "validation"
  | "approval"
  | "report";
export type WorkflowMode = "autonomous" | "approval_required" | "step_by_step";
export type WorkflowControlState =
  | "initialized"
  | "running"
  | "paused"
  | "waiting_review"
  | "completed"
  | "failed";

export type TicketInputDatum = {
  name: string;
  value: string;
  description: string;
};

export type TicketValidationRule = {
  id: string;
  description: string;
  applies_to: string;
  severity: "info" | "warning" | "high" | "critical";
};

export type TicketTestStep = {
  order: number;
  action: string;
  expected_result: string;
  validation_refs: string[];
};

export type TicketServiceInteraction = {
  name: string;
  source: string;
  target: string;
  protocol: string;
  operation: string;
  expected_result: string;
  validation_refs: string[];
};

export type TicketTechnicalDetails = {
  architecture_summary: string;
  components_involved: string[];
  data_flow: string[];
  api_or_service_interactions: TicketServiceInteraction[];
  configuration_requirements: string[];
  security_constraints: string[];
  logging_requirements: string[];
  monitoring_requirements: string[];
  error_handling_expectations: string[];
  test_data_requirements: string[];
};

export type TicketData = {
  id: string;
  title: string;
  description: string;
  business_objective: string;
  test_objective: string;
  system_under_test: string;
  feature_or_service_name: string;
  test_scope: string[];
  out_of_scope: string[];
  preconditions: string[];
  assumptions: string[];
  environment: string;
  interfaces_involved: string[];
  input_data: TicketInputDatum[];
  expected_outputs: string[];
  validation_rules: TicketValidationRule[];
  test_steps: TicketTestStep[];
  acceptance_criteria: string[];
  risks_or_constraints: string[];
  dependencies: string[];
  required_tools: string[];
  priority: Priority;
  labels: string[];
  assignee?: string | null;
  source?: string;
  raw_url?: string | null;
  status: TicketStatus;
  created_date: string;
  last_updated_date: string;
  created_at?: string;
  updated_at?: string;
  technical: TicketTechnicalDetails;
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

export type ValidationSummary = {
  generated_at: string;
  status: "passed" | "warning" | "failed";
  total_artifacts: number;
  passed_artifacts: number;
  failed_artifacts: number;
  requirement_coverage_percent: number;
  artifact_pass_percent: number;
  data_reference_percent: number;
  requirement_completeness_percent: number;
  quality_score: number;
  missing_requirements: string[];
  risk_areas: string[];
  validator_mode: "robot_dry_run" | "local_structural" | "mixed" | "not_run";
  total_attempts: number;
  retry_count: number;
  max_retries: number;
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

export type InvestigationEvidenceItem = {
  evidence_id: string;
  kind: "robot_result" | "robot_log" | "artifact" | "model_trace" | "knowledge_ref" | "memory_ref" | "workflow_event";
  source: string;
  summary: string;
  test_case_id: string | null;
  severity_hint: "info" | "warning" | "high" | "critical";
  content_excerpt: string;
};

export type InvestigationBlock = {
  status: "not_started" | "completed" | "skipped";
  generated_at: string | null;
  evidence_items: InvestigationEvidenceItem[];
  findings: Array<{
    test_case_id: string | null;
    severity: "info" | "warning" | "high" | "critical";
    category: "test" | "application" | "environment" | "data" | "unknown";
    summary: string;
    evidence_refs: string[];
    confidence: number;
    recommended_actions: string[];
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
  configured_agent_routes: Record<string, AgentModelRoute>;
  knowledge_refs: Array<{ ref_id: string; title: string; source: string; score: number; excerpt: string }>;
  memory_refs: Array<{ ref_id: string; title: string; source: string; score: number; excerpt: string }>;
  prompt_versions: Array<{ name: string; version: string }>;
  llm_calls: Array<{
    provider: string;
    model: string;
    prompt_name: string;
    prompt_version: string;
    deterministic: boolean;
    agent_name: string | null;
    model_role: string | null;
    requested_model: string | null;
    summary: string;
  }>;
  structured_parses: Array<{
    prompt_name: string;
    prompt_version: string;
    provider: string;
    model: string;
    schema: string;
    status: string;
    error: string | null;
  }>;
};

export type AgentModelRoute = {
  provider: string;
  model: string | null;
};

export type IntelligenceConfig = {
  llm_provider: string;
  embedding_provider: string;
  llm_model: string | null;
  embedding_model: string | null;
  agent_routes: Record<string, AgentModelRoute>;
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

export type StageReview = {
  stage: WorkflowStageName;
  revision: number;
  status: "not_requested" | "pending" | "approved" | "changes_requested";
  requested_at: string | null;
  requested_by: string | null;
  decided_at: string | null;
  decided_by: string | null;
  comments: string[];
};

export type WorkflowControl = {
  mode: WorkflowMode;
  state: WorkflowControlState;
  current_stage: WorkflowStageName | null;
  next_stage: WorkflowStageName | null;
  pause_requested: boolean;
  completed_stages: WorkflowStageName[];
  stage_revisions: Record<string, number>;
  stage_reviews: Record<string, StageReview>;
  last_error: string | null;
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
  created_at: string;
  updated_at: string;
  workflow_status: string;
  current_node: string | null;
  validation_retry_count: number;
  max_validation_retries: number;
  workflow_trace: Array<{
    node_name: string;
    status: "started" | "completed" | "failed" | "routed";
    timestamp: string;
    iteration: number;
    summary: string | null;
    metadata: Record<string, unknown>;
  }>;
  workflow_control: WorkflowControl;
  integration_profile: IntegrationProfile | null;
  intelligence_config: IntelligenceConfig;
  intelligence_trace: IntelligenceTrace;
  ticket: TicketData | null;
  requirement_analysis: RequirementAnalysis | null;
  coverage_plan: CoveragePlan | null;
  test_cases: TestCase[];
  automation_revision: number;
  automation: Record<string, AutomationBlock>;
  validation_summary: ValidationSummary | null;
  execution: ExecutionBlock | null;
  investigation: InvestigationBlock | null;
  memory_archive: MemoryArchiveBlock | null;
  approval: ApprovalBlock | null;
  audit_log: AuditEvent[];
  review_feedback: Array<{
    requested_at: string;
    requested_by: string;
    comment: string;
    stage: WorkflowStageName | null;
    status: "open" | "applied";
  }>;
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

export type WorkflowEvent = {
  sequence: number;
  id: string;
  context_id: string;
  kind: "session" | "control" | "stage" | "review" | "artifact" | "message" | "error";
  stage: WorkflowStageName | null;
  status: string | null;
  actor: string;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ArtifactRevision = {
  id: string;
  context_id: string;
  test_case_id: string;
  artifact_path: string;
  version: number;
  source: "generated" | "manual";
  actor: string;
  comment: string | null;
  content: string;
  created_at: string;
};

export type ReportPackageFile = {
  path: string;
  kind: string;
  content_type: string;
  description: string;
  size_bytes: number;
  sha256: string;
};

export type ReportPackageManifest = {
  context_id: string;
  ticket_id: string | null;
  ticket_title: string | null;
  generated_at: string;
  package_name: string;
  package_status: "draft" | "ready_for_approval" | "approved" | "executed";
  approval_status: string;
  execution_status: string;
  validation_status: string;
  quality_score: number | null;
  files: ReportPackageFile[];
  warnings: string[];
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
  configuration_status: "ready" | "disabled" | "unconfigured";
  configuration_keys: string[];
  selectable: boolean;
};

export type EmbeddingProvider = {
  name: string;
  mode: string;
  model: string;
  dimensions: number;
  requires_external_api: boolean;
  description: string;
  configuration_status: "ready" | "disabled" | "unconfigured";
  configuration_keys: string[];
  selectable: boolean;
};

export type AgentModelProfile = {
  agent_name: string;
  label: string;
  purpose: string;
  uses_llm: boolean;
  prompt_names: string[];
  local_role: string | null;
  recommended_mode: "external" | "local" | "deterministic";
  rationale: string;
  local_provider: string | null;
  local_model: string | null;
  external_provider: string | null;
  external_model: string | null;
  recommended_provider: string | null;
  recommended_model: string | null;
};

export type EmbeddingRecommendation = {
  recommended_mode: "local";
  recommended_provider: string;
  recommended_model: string;
  fallback_provider: string;
  rationale: string;
};

export type AgentRoutingCatalog = {
  agents: AgentModelProfile[];
  embedding: EmbeddingRecommendation;
};

export type AgentGovernanceCatalog = {
  agents: Array<{
    identity: {
      agent_id: string;
      name: string;
      version: string;
      owner: string;
      service_account: string;
      trust_domain: string;
      risk_tier: string;
    };
    policy: {
      agent_id: string;
      allowed_skills: string[];
      allowed_providers: string[];
      max_model_calls_per_workflow: number;
      max_tokens_per_call: number;
      max_tokens_per_workflow: number;
      require_human_approval: boolean;
    };
  }>;
};

export type ObservabilitySummary = {
  date: string;
  requests: {
    total: number;
    server_errors: number;
    average_duration_ms: number;
    max_duration_ms: number;
  };
  models: {
    calls: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
  };
  agents: {
    total: number;
    failed: number;
    average_duration_ms: number;
  };
  provider_circuits: Array<{
    provider: string;
    state: string;
    failures: number;
    opened_at_epoch: number | null;
  }>;
};

export type TokenBudgetStatus = {
  organization_id: string;
  context_id: string | null;
  agent_name: string | null;
  used_tokens: number;
  reserved_tokens: number;
  limit_tokens: number;
  remaining_tokens: number;
  used_calls: number;
  reserved_calls: number;
  limit_calls: number | null;
};

export type OperationalHealth = {
  status: "healthy" | "degraded";
  request_error_rate: number;
  agent_failure_rate: number;
  open_provider_circuits: number;
  signals: Array<Record<string, unknown>>;
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

export type OllamaModelProfile = {
  role: string;
  model: string;
  kind: "chat" | "embedding";
  purpose: string;
  env_key: string;
  fallback_model: string | null;
  installed: boolean;
  fallback_installed: boolean;
  pull_command: string;
  fallback_pull_command: string | null;
};

export type OllamaModelProfiles = {
  base_url: string;
  service_available: boolean;
  service_error: string | null;
  installed_models: string[];
  profiles: OllamaModelProfile[];
  prompt_routes: OllamaPromptRoute[];
};

export type OllamaPromptRoute = {
  prompt_name: string;
  role: string;
  model: string;
};

export type OllamaSmokeTestResult = {
  role: string;
  model: string;
  kind: "chat" | "embedding";
  available: boolean;
  ok: boolean;
  response_excerpt: string;
  error: string | null;
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
  phase: string;
  status: string | null;
  test_case_id: string | null;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
};
