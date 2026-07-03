"""Probe Layer 1 (orchestrator) hardening — verify the fix, not just the gap.

Gap A: run_workflow failure containment. A node exception must leave
       workflow_control.state == 'failed', record last_error, tag the failing
       stage, and re-raise (the stage runner already does this; the autonomous
       runner now mirrors it).
Gap B: run_workflow completion honesty. Stages are marked completed only when
       their evidence predicate holds. On the autonomous deferral (execution
       skipped at the approval gate), 'approval' and 'report' must NOT appear in
       completed_stages, and approval.status stays pending_review.

NOTE on faithful injection: the node sequences capture function references at
import time, so monkeypatching ``nodes.coverage_planner`` does NOT reach the
graph (an earlier version of this probe fell for that and printed a false
"no exception raised"). ``build_langgraph_workflow`` reads the module-global
``NODE_SEQUENCE`` at call time, so replacing the entry there -- keeping the node
name so the hardcoded edges still wire -- is the reliable way to force a real
in-graph node failure.
"""
from __future__ import annotations

from backend.graph import workflow as wf
from backend.graph.workflow import create_initial_context, run_workflow
from backend.graph.state import TicketData

# --- Gap B: deferred stages are NOT reported as completed -----------------
ticket = TicketData(id="AI-L1", title="probe orchestrator", description="probe")
ctx = create_initial_context(created_by="probe", ticket=ticket)
done = run_workflow(ctx)
print("=== Gap B: completion honesty ===")
print("workflow_control.state      :", done.workflow_control.state)
print("completed_stages            :", done.workflow_control.completed_stages)
print("stage_revisions keys        :", sorted(done.workflow_control.stage_revisions))
print("approval block present?     :", done.approval is not None,
      "| status:", getattr(done.approval, "status", None))
print("execution status            :", getattr(done.execution, "status", None))
deferred_ok = (
    "approval" not in done.workflow_control.completed_stages
    and "report" not in done.workflow_control.completed_stages
    and getattr(done.approval, "status", None) == "pending_review"
)
print("-> approval/report correctly EXCLUDED while execution deferred:", deferred_ok)
print()

# --- Gap A: failure containment in run_workflow ---------------------------
print("=== Gap A: failure containment ===")


def _boom(context):
    raise RuntimeError("simulated coverage_planner crash")


# Replace the coverage_planner entry in the module-global sequence, keeping the
# name so build_langgraph_workflow's hardcoded edges still wire it in.
original_sequence = wf.NODE_SEQUENCE
wf.NODE_SEQUENCE = tuple(
    (name, _boom if name == "coverage_planner" else node)
    for name, node in original_sequence
)
ctx2 = create_initial_context(created_by="probe", ticket=ticket)
try:
    run_workflow(ctx2)
    print("no exception raised (UNEXPECTED -- containment test did not trigger)")
except Exception as exc:  # noqa: BLE001
    print("exception propagated to caller    :", type(exc).__name__, "-", exc)
    print("workflow_control.state after crash:", ctx2.workflow_control.state)
    print("last_error recorded               :", ctx2.workflow_control.last_error)
    print("failing stage tagged              :", ctx2.workflow_control.current_stage)
    contained_ok = (
        ctx2.workflow_control.state == "failed"
        and ctx2.workflow_control.last_error is not None
        and ctx2.workflow_control.current_stage == "coverage"
    )
    print("-> failure contained + attributed to 'coverage':", contained_ok)
finally:
    wf.NODE_SEQUENCE = original_sequence  # restore
