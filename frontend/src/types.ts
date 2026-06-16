export type Priority = "low" | "medium" | "high" | "critical";
export type TicketStatus = "backlog" | "ready" | "in_progress" | "blocked" | "done";
export type ApprovalStatus = "not_ready" | "pending_review" | "approved" | "changes_requested";
export type ExecutionStatus = "passed" | "failed" | "skipped";
export type ExecutionResultStatus = "passed" | "failed" | "skipped";

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

export type ExecutionBlock = {
  status: ExecutionStatus;
  run_by: string;
  started_at: string;
  finished_at: string;
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
  execution: ExecutionBlock | null;
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
