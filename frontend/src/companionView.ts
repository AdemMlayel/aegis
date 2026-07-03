import type { TestContext } from "./types";
import type { WorkspaceView } from "./components/ConversationWorkspace";
import { STAGES, pendingStageReview } from "./components/WorkspaceUtils";

/**
 * Adaptive companion (V2 design): the detail panel follows the orchestrator
 * instead of forcing the user to pick a tab. Given the current workflow
 * context, decide which detail view best reflects what the system is doing
 * *right now* — so a non-technical user can just watch, while a power user can
 * still override by clicking a tab (we only auto-derive until they do).
 *
 * Mapping rationale (each step shows the artifact it is producing/just produced):
 *   - waiting on a stage review            -> Activity (the approval lives there)
 *   - generating/validating automation     -> Artifacts / Validation
 *   - executing / investigating / reporting-> Evidence then Report
 *   - building coverage / test cases       -> Tests
 *   - otherwise (early stages, idle)        -> Activity
 *
 * Pure function: no side effects, fully unit-testable.
 */
export function deriveCompanionView(context: TestContext | null): WorkspaceView {
  if (!context) return "conversation";

  // An open approval gate is the most important thing to surface.
  if (pendingStageReview(context)) return "conversation";

  const control = context.workflow_control;
  const stage = control.current_stage ?? control.next_stage ?? null;

  // A finished/failed execution means the evidence + report are the payload.
  if (context.execution) {
    if (context.reports) return "report";
    return "evidence";
  }

  switch (stage) {
    case "tests":
    case "coverage":
      return "tests";
    case "automation":
      return "artifacts";
    case "validation":
      return "validation";
    case "approval":
      return "conversation";
    case "report":
      return context.reports ? "report" : "evidence";
    default:
      return "conversation";
  }
}

/**
 * Progress ratio (0..1) across the 8 canonical stages, for the companion's
 * mini stepper. Derived purely from completed_stages so it is traceable.
 */
export function workflowProgressRatio(context: TestContext | null): number {
  if (!context) return 0;
  const done = context.workflow_control.completed_stages.length;
  return Math.min(1, done / STAGES.length);
}
