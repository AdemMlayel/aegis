from importlib.util import find_spec
from pathlib import Path

from backend.graph.state import TestContext as WorkflowContext
from backend.graph.state import TicketData
from backend.graph.workflow import run_workflow


def test_workflow_runs_ticket_to_report() -> None:
    context = WorkflowContext(
        created_by="pytest",
        ticket=TicketData(
            id="FAKE-123",
            title="Money Transfer Feature",
            description="As an authenticated customer, I want to transfer money.",
            acceptance_criteria=[
                "Transfer completes within 3 seconds",
                "Balance updates immediately",
            ],
            priority="high",
            labels=["banking", "payments"],
        ),
    )

    result = run_workflow(context)

    assert result.workflow_status == "report_generated"
    assert result.schema_version == "0.15.0"
    assert result.ticket is not None
    assert result.requirement_analysis is not None
    assert result.requirement_analysis.domain == "banking"
    assert result.coverage_plan is not None
    assert result.coverage_plan.risk_level == "high"
    assert [test_case.id for test_case in result.test_cases] == [
        "TC001",
        "TC002",
        "TC003",
    ]
    assert set(result.test_data) == {"TC001", "TC002", "TC003"}
    assert result.test_data["TC001"].strategy == "factory"
    assert result.test_data["TC002"].strategy == "fixture"
    assert set(result.automation) == {"TC001", "TC002", "TC003"}
    assert result.automation_revision == 1
    assert result.automation["TC001"].revision == 1
    assert all(block.data_reference_check_passed for block in result.automation.values())
    assert Path(result.automation["TC001"].robot_file).is_file()
    assert all(block.validation.artifact_exists for block in result.automation.values())
    assert result.reports is not None
    assert result.reports.total_test_cases == 3
    assert "Robot automation files" in result.reports.summary

    validation = result.automation["TC001"].validation
    assert validation.dry_run_passed is True
    assert validation.validation_attempts == 1
    if find_spec("robot") is None:
        assert validation.dry_run_skipped_reason is not None
    assert result.approval is not None
    assert result.approval.status == "pending_review"
    assert result.approval.git_branch == "aegis/fake_123"
    assert result.approval.git_pr_url is None
    assert result.approval.review_items == [
        block.robot_file for block in result.automation.values()
    ]
    assert result.execution is not None
    assert result.execution.status == "skipped"
    assert result.investigation is not None
    assert result.investigation.status == "skipped"
    assert result.memory_archive is not None
    assert result.memory_archive.status == "archived"
    assert result.validation_retry_count == 0
    assert result.max_validation_retries == 2
    assert result.workflow_trace
    assert {trace.node_name for trace in result.workflow_trace} >= {
        "load_ticket",
        "automation_generator",
        "validator",
        "validation_retry_gate",
        "execution_dispatcher",
        "investigation_coordinator",
        "memory_archiver",
    }


def test_context_defaults_do_not_share_mutable_state() -> None:
    first = WorkflowContext(created_by="first")
    second = WorkflowContext(created_by="second")

    completed = run_workflow(WorkflowContext(created_by="pytest"))
    first.test_cases.append(completed.test_cases[0])
    first.test_data["TC001"] = completed.test_data["TC001"]
    first.automation["TC001"] = completed.automation["TC001"]
    first.approval = completed.approval

    assert second.test_cases == []
    assert second.test_data == {}
    assert second.automation == {}
    assert second.approval is None



def test_validation_retry_loop_regenerates_once(monkeypatch) -> None:
    from backend.graph.state import AutomationValidation
    from backend.tools import robot_validation

    original_structural_check = robot_validation._run_local_robot_syntax_check
    calls = {"count": 0}

    def flaky_structural_check(robot_file):
        calls["count"] += 1
        if calls["count"] <= 3:
            return AutomationValidation(
                artifact_exists=True,
                dry_run_passed=False,
                dry_run_skipped_reason="forced first-pass validation failure",
                validation_attempts=1,
                errors=["Forced validation failure for retry routing test"],
            )
        return original_structural_check(robot_file)

    monkeypatch.setattr(robot_validation, "_robot_command", lambda: None)
    monkeypatch.setattr(
        robot_validation,
        "_run_local_robot_syntax_check",
        flaky_structural_check,
    )

    result = run_workflow(
        WorkflowContext(
            created_by="pytest",
            ticket=TicketData(
                id="RETRY-001",
                title="Validation Retry Feature",
                description="As a QA engineer, I want invalid generated automation to be regenerated.",
                acceptance_criteria=["Validation retry is attempted before approval"],
                priority="medium",
                labels=["validation", "workflow"],
            ),
        )
    )

    assert result.workflow_status == "report_generated"
    assert result.validation_retry_count == 1
    assert result.automation_revision == 2
    assert result.approval is not None
    assert result.approval.status == "pending_review"
    assert all(
        block.validation.dry_run_passed is True
        for block in result.automation.values()
    )
    assert any(
        event.event_type == "automation_validation_retry"
        for event in result.audit_log
    )
    assert any(
        trace.status == "routed" and trace.node_name == "validation_retry_gate"
        for trace in result.workflow_trace
    )


def test_autonomous_run_does_not_fake_approval_or_report_completion() -> None:
    """Layer 1 honesty: the autonomous run defers execution at the approval gate,
    so it must NOT report approval/report as completed stages, and must not stamp
    revisions for stages that never genuinely ran."""
    result = run_workflow(
        WorkflowContext(
            created_by="pytest",
            ticket=TicketData(
                id="HONEST-001",
                title="Completion honesty",
                description="As a QA lead, I want honest stage bookkeeping.",
                acceptance_criteria=["Deferred stages are not reported complete"],
                priority="medium",
                labels=["workflow", "honesty"],
            ),
        )
    )

    control = result.workflow_control
    # Execution is deferred autonomously -> approval was never granted.
    assert result.approval is not None
    assert result.approval.status == "pending_review"
    assert result.execution is not None
    assert result.execution.status == "skipped"

    # The six genuinely-completed generation stages are present...
    assert control.completed_stages == [
        "ticket",
        "requirements",
        "coverage",
        "tests",
        "automation",
        "validation",
    ]
    # ...and the deferred gates are NOT faked as completed.
    assert "approval" not in control.completed_stages
    assert "report" not in control.completed_stages
    # Revisions are only recorded for stages that actually completed.
    assert set(control.stage_revisions) == set(control.completed_stages)
    # Every completed stage is traceable to a real artifact.
    assert result.ticket is not None
    assert result.requirement_analysis is not None
    assert result.coverage_plan is not None
    assert result.test_cases and result.test_data
    assert result.automation


def test_autonomous_run_contains_node_failure_and_attributes_stage(monkeypatch) -> None:
    """Layer 1 failure containment: a node crash must leave the control block in
    'failed' state with last_error recorded and the failing stage attributed,
    while still propagating the exception to the caller."""
    from backend.graph import workflow as wf

    def _boom(_context):
        raise RuntimeError("simulated coverage_planner crash")

    # Replace the coverage_planner entry in the module-global sequence (keeping
    # the node name so the LangGraph edges still wire) -- monkeypatching
    # nodes.coverage_planner would miss the frozen reference the graph captured.
    patched_sequence = tuple(
        (name, _boom if name == "coverage_planner" else node)
        for name, node in wf.NODE_SEQUENCE
    )
    monkeypatch.setattr(wf, "NODE_SEQUENCE", patched_sequence)

    context = WorkflowContext(
        created_by="pytest",
        ticket=TicketData(
            id="FAIL-001",
            title="Failure containment",
            description="As a QA lead, I want crashes contained and attributed.",
            acceptance_criteria=["A node crash sets state=failed"],
            priority="high",
            labels=["workflow", "resilience"],
        ),
    )

    import pytest

    with pytest.raises(RuntimeError, match="simulated coverage_planner crash"):
        run_workflow(context)

    control = context.workflow_control
    assert control.state == "failed"
    assert control.last_error is not None
    assert "RuntimeError" in control.last_error
    assert control.current_stage == "coverage"
    assert control.next_stage is None
    assert context.workflow_status == "coverage_failed"


def test_crash_recovers_pre_crash_artifacts_onto_outer_context(monkeypatch) -> None:
    """W4: LangGraph copies state per super-step, so on a node crash the outer
    context reference never observes artifacts earlier nodes produced. The
    failure path must recover them from the carrier so the failed run persists
    the real work done before the crash instead of an empty context."""
    from backend.graph import workflow as wf

    def _boom(_context):
        raise RuntimeError("simulated automation_generator crash")

    # Crash at automation_generator (stage 6): ticket/requirements/coverage/tests
    # all genuinely ran before it.
    patched_sequence = tuple(
        (name, _boom if name == "automation_generator" else node)
        for name, node in wf.NODE_SEQUENCE
    )
    monkeypatch.setattr(wf, "NODE_SEQUENCE", patched_sequence)

    context = WorkflowContext(
        created_by="pytest",
        ticket=TicketData(
            id="RECOVER-001",
            title="Pre-crash artifact recovery",
            description="As a QA lead, I want pre-crash work preserved.",
            acceptance_criteria=["Artifacts produced before a crash survive"],
            priority="high",
            labels=["workflow", "resilience"],
        ),
    )

    import pytest

    with pytest.raises(RuntimeError, match="simulated automation_generator crash"):
        run_workflow(context)

    control = context.workflow_control
    assert control.state == "failed"
    assert control.current_stage == "automation"
    # The artifacts the earlier nodes produced are recovered onto the outer
    # context (the object run_and_persist_workflow_start persists on failure).
    assert context.requirement_analysis is not None
    assert context.coverage_plan is not None
    assert context.test_cases
    assert context.test_data


def test_recursion_limit_config_exceeds_langgraph_default() -> None:
    """W3: the worst-case validate->regenerate path is 13 nodes + retries*3,
    which exceeds LangGraph's default recursion_limit of 25. The invoke config
    must size the limit above that worst case so a legitimate retry sequence is
    not aborted with GraphRecursionError mid-loop."""
    from backend.graph import workflow as wf

    context = WorkflowContext(created_by="pytest", max_validation_retries=5)
    config = wf._graph_invoke_config(context)
    worst_case = (
        len(wf.NODE_SEQUENCE)
        + context.max_validation_retries * len(wf.VALIDATION_LOOP_NODE_SEQUENCE)
    )
    assert config["recursion_limit"] >= worst_case
    assert config["recursion_limit"] > 25
