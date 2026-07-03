"""Throwaway: prove the N3 [Teardown] clause is dry-run valid (not just present)."""
import subprocess
import sys
import tempfile
from pathlib import Path

from backend.graph.state import TestCase, TestDataBlock
from backend.tools.automation_heuristics import _render_robot_file

tc = TestCase(
    id="TC001",
    title="Valid transfer",
    type="functional",
    expected_outcome="Transfer succeeds",
    steps=["Submit transfer"],
    test_data_requirements={"users": ["valid_user"]},
)
# Multi-step teardown -> exercises the Run Keywords ... AND ... branch.
td = TestDataBlock(
    test_case_id="TC001",
    strategy="factory",
    resolved_data={"users": ["tc001_valid_user"]},
    teardown=["cleanup_tc001_data", "reset_tc001_fixtures"],
)
content = _render_robot_file(tc, "TD-1", 1, [], ticket=None, test_data=td)
print("=== GENERATED ROBOT FILE ===")
print(content)

with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "tc001.robot"
    f.write_text(content, encoding="utf-8")
    proc = subprocess.run(
        ["robot", "--dryrun", "--outputdir", d, str(f)],
        capture_output=True, text=True,
    )
    print("=== DRYRUN STDOUT ===")
    print(proc.stdout)
    print("=== DRYRUN STDERR ===")
    print(proc.stderr)
    print("=== EXIT:", proc.returncode, "===")
    sys.exit(proc.returncode)
