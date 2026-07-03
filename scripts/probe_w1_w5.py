"""Probe W1 (optimistic concurrency) + W5 (retry reset) empirically.

Uses an isolated temp SQLite DB so it never touches real data. Run from repo
root with the venv active:
    python scripts/probe_w1_w5.py
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from backend.graph.state import TestContext, TicketData


def _fresh_db(tmp_dir: Path) -> Path:
    """Point the storage layer at an isolated temp DB."""
    import backend.storage.adapters as adapters
    import backend.storage.database as database

    db_path = tmp_dir / "probe.sqlite3"
    adapters.SQLITE_DB_PATH = db_path  # type: ignore[attr-defined]
    database.SQLITE_DB_PATH = db_path
    # default_storage_adapter caches its own path; rebuild it.
    adapters.default_storage_adapter = adapters.SQLiteStorageAdapter(db_path=db_path)
    return db_path


def probe_w1_optimistic_concurrency() -> None:
    from backend.storage.contexts import (
        OptimisticConcurrencyError,
        load_context,
        save_context,
    )

    ctx = TestContext(
        created_by="probe",
        ticket=TicketData(
            id="W1-1",
            title="concurrency",
            description="As a QA lead, I want last-writer-wins prevented.",
            acceptance_criteria=["concurrent save raises"],
            priority="high",
            labels=["probe"],
        ),
    )
    save_context(ctx)  # first write -> row_version 1
    print("W1: after first save, row_version =", ctx.row_version)
    assert ctx.row_version == 1

    # Two independent loads of the same row -- simulating resume + approve.
    writer_a = load_context(ctx.context_id)
    writer_b = load_context(ctx.context_id)
    assert writer_a is not None and writer_b is not None
    print("W1: writer_a loaded at row_version =", writer_a.row_version)
    print("W1: writer_b loaded at row_version =", writer_b.row_version)

    # Writer A commits first -> row advances to 2.
    writer_a.mark("a_changed_status")
    save_context(writer_a)
    print("W1: writer_a committed, row_version =", writer_a.row_version)
    assert writer_a.row_version == 2

    # Writer B still believes it holds version 1 -> must be rejected, NOT
    # silently overwrite writer A's change (last-writer-wins).
    writer_b.mark("b_changed_status")
    try:
        save_context(writer_b)
    except OptimisticConcurrencyError as exc:
        print("W1: writer_b correctly REJECTED ->", exc)
    else:
        raise AssertionError("W1 FAILED: stale writer_b save was not rejected")

    # The persisted state reflects writer A, not the rejected writer B.
    final = load_context(ctx.context_id)
    assert final is not None
    print("W1: persisted workflow_status =", final.workflow_status)
    assert final.workflow_status == "a_changed_status", "W1 FAILED: B clobbered A"
    print("W1: PASS - concurrent stale write rejected, no data loss\n")


def probe_w1_insert_then_update_no_false_conflict() -> None:
    """A normal load -> mutate -> save sequence (the common single-writer path)
    must NOT raise: version advances cleanly each time."""
    from backend.storage.contexts import load_context, save_context

    ctx = TestContext(created_by="probe-serial")
    save_context(ctx)
    for expected in (2, 3, 4):
        reloaded = load_context(ctx.context_id)
        assert reloaded is not None
        reloaded.mark(f"step_{expected}")
        save_context(reloaded)
        assert reloaded.row_version == expected, (
            f"expected row_version {expected}, got {reloaded.row_version}"
        )
    print("W1: PASS - serial load/mutate/save advances 1->4 with no false conflict\n")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        _fresh_db(Path(tmp))
        probe_w1_optimistic_concurrency()
        probe_w1_insert_then_update_no_false_conflict()
        print("All W1 probes passed.")
