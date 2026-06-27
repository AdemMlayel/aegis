import type { TestContext, WorkflowEvent, WorkflowStageName } from "../types";

export const STAGES: Array<{ name: WorkflowStageName; label: string }> = [
  { name: "ticket", label: "Ticket" },
  { name: "requirements", label: "Requirements" },
  { name: "coverage", label: "Coverage" },
  { name: "tests", label: "Tests" },
  { name: "automation", label: "Automation" },
  { name: "validation", label: "Validation" },
  { name: "approval", label: "Approval" },
  { name: "report", label: "Report" }
];

export function pendingStageReview(context: TestContext | null): WorkflowStageName | null {
  if (!context || context.workflow_control.state !== "waiting_review") return null;
  const review = Object.values(context.workflow_control.stage_reviews).find(
    (item) => item.status === "pending"
  );
  return review?.stage ?? null;
}

export function stageState(
  context: TestContext,
  stage: WorkflowStageName
): "completed" | "active" | "blocked" | "waiting" {
  if (context.workflow_control.last_error && context.workflow_control.current_stage === stage) return "blocked";
  if (context.workflow_control.current_stage === stage || context.workflow_control.next_stage === stage) return "active";
  if (context.workflow_control.completed_stages.includes(stage)) return "completed";
  return "waiting";
}

export function activityDetail(
  context: TestContext,
  stage: WorkflowStageName,
  event?: WorkflowEvent
): string {
  if (context.workflow_control.current_stage === stage) return "Running";
  const review = context.workflow_control.stage_reviews[stage];
  if (review?.status === "pending") return "Waiting review";
  if (review?.status === "changes_requested") return "Changes requested";
  if (context.workflow_control.completed_stages.includes(stage)) {
    const duration = event?.metadata.duration_ms;
    return duration ? `${String(duration)} ms` : `Revision ${context.workflow_control.stage_revisions[stage] ?? 1}`;
  }
  return "Pending";
}

export function summaryInputs(context: TestContext, stage: WorkflowStageName): string {
  if (stage === "requirements") return context.ticket?.id ?? "Ticket";
  if (stage === "coverage") return "Approved requirements and memory";
  if (stage === "tests") return "Coverage plan and evidence";
  if (stage === "automation") return `${context.test_cases.length} test scenarios`;
  if (stage === "validation") return `${Object.keys(context.automation).length} Robot artifacts`;
  if (stage === "approval") return "Validated automation package";
  if (stage === "report") return "Workflow evidence and execution state";
  return "Selected ticket";
}

export function eventsFromTrace(context: TestContext): WorkflowEvent[] {
  return context.workflow_trace
    .filter((trace) => trace.status === "completed" || trace.status === "failed")
    .map((trace, index) => ({
      sequence: index + 1,
      id: `${trace.node_name}-${index}`,
      context_id: context.context_id,
      kind: trace.status === "failed" ? "error" : "stage",
      stage: nodeStage(trace.node_name),
      status: trace.status,
      actor: "system",
      message: trace.summary ?? `${trace.node_name.replaceAll("_", " ")} ${trace.status}.`,
      metadata: trace.metadata,
      created_at: trace.timestamp
    }));
}

export function nodeStage(nodeName: string): WorkflowStageName | null {
  if (nodeName === "load_ticket") return "ticket";
  if (nodeName === "requirement_agent") return "requirements";
  if (nodeName === "coverage_planner") return "coverage";
  if (nodeName === "test_case_generator" || nodeName === "test_data_resolver") return "tests";
  if (nodeName === "automation_generator") return "automation";
  if (nodeName === "validator" || nodeName === "validation_retry_gate") return "validation";
  if (nodeName === "human_approval") return "approval";
  if (["execution_dispatcher", "investigation_coordinator", "memory_archiver", "report_generator"].includes(nodeName)) return "report";
  return null;
}

export function stageLabel(stage: WorkflowStageName): string {
  return STAGES.find((item) => item.name === stage)?.label ?? stage;
}

export function validationText(value: boolean | null): string {
  if (value === true) return "Passed";
  if (value === false) return "Failed";
  return "Needs validation";
}

export function validationHeadline(status: "passed" | "warning" | "failed"): string {
  if (status === "passed") return "Validation passed";
  if (status === "warning") return "Validation passed with review notes";
  return "Validation failed";
}

export function yesNo(value: boolean): string {
  return value ? "Passed" : "Failed";
}

export function formatTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function formatDuration(durationMs: number): string {
  if (durationMs < 1000) return `${durationMs} ms`;
  const seconds = durationMs / 1000;
  if (seconds < 60) return `${seconds.toFixed(seconds < 10 ? 1 : 0)} s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

export function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}
