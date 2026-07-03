"""Live end-to-end verification of the self-healing path.

Runs a real workflow, injects a deliberately-broken keyword into one generated
.robot file, then runs the detector exactly as the chat copilot does and asserts
it surfaces a human-gated repair from the real keyword registry.
"""
from __future__ import annotations

from pathlib import Path

from backend.graph.artifacts import GENERATED_ROOT, PROJECT_ROOT
from backend.graph.state import TestContext as WC, TicketData
from backend.graph.workflow import run_workflow
from backend.storage.contexts import save_context, load_context
from backend.tools.self_healing import detect_self_healing

ctx = run_workflow(
    WC(
        created_by="heal-verify",
        ticket=TicketData(
            id="HEAL-1",
            title="Refund approval API check",
            description="Verify refund approval via internal API.",
            acceptance_criteria=["approver required", "audit event written"],
            priority="high",
            labels=["api", "audit"],
        ),
    )
)
save_context(ctx)
print(f"workflow: {ctx.context_id}  automation files: {len(ctx.automation)}")

# Inject a broken keyword into the first generated robot file (simulates a
# renamed/typo'd custom keyword — the real failure mode in this corpus).
first_id, first_block = next(iter(ctx.automation.items()))
robot_path: Path | None = None
for base in (GENERATED_ROOT.parent, PROJECT_ROOT):
    candidate = (base / first_block.robot_file).resolve()
    if candidate.is_file():
        robot_path = candidate
        break
assert robot_path is not None, f"could not locate {first_block.robot_file}"

text = robot_path.read_text(encoding="utf-8")
# Append a step that calls a typo of the real registry keyword 'Do Get'.
injected = text.rstrip() + "\n    ${out}    Do Geet    /api/v1/refund    params\n"
robot_path.write_text(injected, encoding="utf-8")
print(f"injected broken keyword 'Do Geet' into {first_block.robot_file}")

# Run the detector exactly as the chat copilot's _self_healing_response does.
reloaded = load_context(ctx.context_id) or ctx
block = detect_self_healing(reloaded)
print("-" * 60)
print("status:", block.status)
print("summary:", block.summary)
kw = [s for s in block.suggestions if s.kind == "keyword"]
print(f"keyword suggestions: {len(kw)}")
for s in kw:
    print(f"  broken `{s.broken_reference}` @ {s.robot_file}:{s.line}")
    print(f"    status: {s.status}  (must be awaiting_approval)")
    if s.recommended:
        print(f"    recommended: `{s.recommended.value}` score={s.recommended.score:.2f}")

ok = bool(kw) and any(
    s.broken_reference == "Do Geet"
    and s.recommended and s.recommended.value == "Do Get"
    and s.status == "awaiting_approval"
    for s in kw
)

# Restore the file so we don't leave injected breakage behind.
robot_path.write_text(text, encoding="utf-8")
print("restored original robot file")
print("=" * 60)
print("VERDICT:", "SELF-HEALING LIVE OK ✅" if ok else "FAILED ❌")
print("CONTEXT_ID", ctx.context_id)
