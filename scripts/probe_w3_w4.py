"""Probe W3 (recursion limit) and W4 (pre-crash artifact recovery) empirically.

Run from repo root with the venv active:
    python scripts/probe_w3_w4.py
"""
from __future__ import annotations

from backend.graph import workflow as wf
from backend.graph.state import TestContext, TicketData


def _ticket() -> TicketData:
    return TicketData(
        id="PROBE-1",
        title="probe",
        description="As a QA lead, I want to verify crash recovery.",
        acceptance_criteria=["artifacts survive a mid-run crash"],
        priority="high",
        labels=["probe"],
    )


def probe_w4_recovers_pre_crash_artifacts() -> None:
    """Crash at automation_generator (stage 6); requirements/coverage/tests
    were produced by earlier nodes. Under LangGraph's per-super-step state copy,
    the OLD code persisted the unmutated outer context (all None). W4 should now
    recover them onto the outer context."""

    def _boom(_ctx):
        raise RuntimeError("simulated automation_generator crash")

    patched = tuple(
        (name, _boom if name == "automation_generator" else node)
        for name, node in wf.NODE_SEQUENCE
    )
    orig = wf.NODE_SEQUENCE
    wf.NODE_SEQUENCE = patched
    context = TestContext(created_by="probe", ticket=_ticket())
    try:
        try:
            wf.run_workflow(context)
        except RuntimeError as exc:
            assert "automation_generator crash" in str(exc)
        else:
            raise AssertionError("expected the crash to propagate")
    finally:
        wf.NODE_SEQUENCE = orig

    control = context.workflow_control
    print("W4: state           =", control.state)
    print("W4: current_stage   =", control.current_stage)
    print("W4: requirement_analysis recovered =", context.requirement_analysis is not None)
    print("W4: coverage_plan recovered        =", context.coverage_plan is not None)
    print("W4: test_cases recovered           =", bool(context.test_cases))
    print("W4: test_data recovered            =", bool(context.test_data))
    assert control.state == "failed"
    assert control.current_stage == "automation"
    assert context.requirement_analysis is not None, "W4 FAILED: requirements lost"
    assert context.coverage_plan is not None, "W4 FAILED: coverage lost"
    assert context.test_cases, "W4 FAILED: test cases lost"
    assert context.test_data, "W4 FAILED: test data lost"
    print("W4: PASS - pre-crash artifacts recovered onto outer context\n")


def probe_w3_recursion_config() -> None:
    """The invoke config must size recursion_limit above LangGraph's default 25
    for the worst-case retry path."""
    ctx = TestContext(created_by="probe", max_validation_retries=5)
    config = wf._graph_invoke_config(ctx)
    print("W3: NODE_SEQUENCE len           =", len(wf.NODE_SEQUENCE))
    print("W3: max_validation_retries      =", ctx.max_validation_retries)
    print("W3: computed recursion_limit    =", config["recursion_limit"])
    # 13 + 5*3 + 5 = 33, comfortably above the worst-case 28 and the default 25.
    assert config["recursion_limit"] >= len(wf.NODE_SEQUENCE) + 5 * 3
    assert config["recursion_limit"] > 25
    print("W3: PASS - recursion_limit covers worst-case retry path\n")


if __name__ == "__main__":
    probe_w4_recovers_pre_crash_artifacts()
    probe_w3_recursion_config()
    print("All W3/W4 probes passed.")
