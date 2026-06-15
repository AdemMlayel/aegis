export type Priority = "low" | "medium" | "high" | "critical";

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

export type ApprovalBlock = {
  status: "not_ready" | "pending_review" | "approved" | "changes_requested";
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
