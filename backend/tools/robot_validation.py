from __future__ import annotations

import os
import shutil
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from backend.graph.artifacts import PROJECT_ROOT
from backend.graph.state import (
    AutomationBlock,
    AutomationValidation,
    TestDataBlock,
)
from backend.robot_libraries.registry import list_robot_keyword_capabilities
from backend.tools.base import BaseTool, tool_registry

BUILTIN_KEYWORDS = {
    "log",
    "should be true",
    "should be equal",
    "should be equal as strings",
    "should contain",
    "should not contain",
    "should not be empty",
    "create dictionary",
    "create list",
    "set variable",
    "no operation",
    "fail",
    "sleep",
    "run keyword",
    "run keyword if",
    "run keywords",
    "call method",
    "get library instance",
}
ROBOT_CONTROL_TOKENS = {"for", "end", "if", "else", "else if", "while", "try", "except", "finally"}


@tool_registry.register(
    name="LocalRobotValidationTool",
    isolation="process",
    description="Validates generated Robot Framework artifacts and data references.",
)
class LocalRobotValidationTool(BaseTool):
    def invoke(self, **kwargs: Any) -> dict[str, AutomationBlock]:
        automation = kwargs.get("automation")
        test_data = kwargs.get("test_data")
        if not isinstance(automation, dict) or not all(
            isinstance(block, AutomationBlock) for block in automation.values()
        ):
            raise TypeError(
                "LocalRobotValidationTool requires dict[str, AutomationBlock]"
            )
        if not isinstance(test_data, dict) or not all(
            isinstance(block, TestDataBlock) for block in test_data.values()
        ):
            raise TypeError(
                "LocalRobotValidationTool requires dict[str, TestDataBlock]"
            )

        return validate_robot_automation(
            automation=automation,
            test_data=test_data,
        )


def validate_robot_automation(
    *,
    automation: dict[str, AutomationBlock],
    test_data: dict[str, TestDataBlock],
) -> dict[str, AutomationBlock]:
    for test_case_id, automation_block in automation.items():
        robot_file = (PROJECT_ROOT / automation_block.robot_file).resolve()
        errors: list[str] = []

        artifact_exists = robot_file.is_file()
        if not artifact_exists:
            errors.append(
                f"Generated Robot file does not exist: {automation_block.robot_file}"
            )
        if robot_file.suffix != ".robot":
            errors.append(
                "Generated automation is not a .robot file: "
                f"{automation_block.robot_file}"
            )

        data_reference_check_passed = test_case_id in test_data
        automation_block.data_reference_check_passed = data_reference_check_passed
        if not data_reference_check_passed:
            errors.append(f"Missing resolved test data for {test_case_id}")

        if artifact_exists and robot_file.suffix == ".robot":
            validation = _run_robot_dryrun(robot_file)
            profile_errors = _validate_known_keywords(robot_file)
            validation.errors = [*errors, *validation.errors, *profile_errors]
            if profile_errors:
                validation.dry_run_passed = False
        else:
            validation = AutomationValidation(
                artifact_exists=artifact_exists,
                dry_run_passed=False,
                validation_attempts=0,
                errors=errors,
            )

        automation_block.validation = validation

    return automation


def _robot_command() -> list[str] | None:
    robot_cli = shutil.which("robot")
    if robot_cli is not None:
        return [robot_cli]
    if find_spec("robot") is not None:
        return [sys.executable, "-m", "robot"]
    return None


def _run_robot_dryrun(robot_file: Path) -> AutomationValidation:
    command = _robot_command()
    if command is None:
        return _run_local_robot_syntax_check(robot_file)

    # Robot may be the system CLI rather than the venv's, so its subprocess does
    # not automatically have the project root importable. Generated suites import
    # backend.robot_libraries.* (the telecom trace library), so we put PROJECT_ROOT
    # on both PYTHONPATH and robot's --pythonpath; without this the library fails to
    # import and every keyword reports "No keyword found".
    #
    # S4: build a *minimal* env rather than os.environ.copy(). The dry-run runs
    # untrusted generated suites; copying the whole environment would leak every
    # AEGISQA_* secret, API key, and token into that subprocess. Pass only what
    # Robot genuinely needs to locate Python, the venv, and the project package.
    project_root = str(PROJECT_ROOT)
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    scrubbed_pythonpath = (
        f"{project_root}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else project_root
    )
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": scrubbed_pythonpath,
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    # Preserve the active virtualenv pointer when present so the right Python and
    # site-packages are used, without dragging the rest of the environment along.
    for passthrough in ("VIRTUAL_ENV", "PYTHONHOME", "SYSTEMROOT", "TEMP", "TMP"):
        value = os.environ.get(passthrough)
        if value:
            env[passthrough] = value

    try:
        result = subprocess.run(
            [
                *command,
                "--pythonpath",
                project_root,
                "--dryrun",
                "--output",
                "NONE",
                "--log",
                "NONE",
                "--report",
                "NONE",
                str(robot_file),
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return AutomationValidation(
            artifact_exists=robot_file.is_file(),
            dry_run_passed=False,
            validation_attempts=1,
            errors=["Robot Framework dry-run timed out after 30 seconds"],
        )

    errors: list[str] = []
    if result.returncode != 0:
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        errors.append(output.strip() or "Robot Framework dry-run failed")

    return AutomationValidation(
        artifact_exists=robot_file.is_file(),
        dry_run_passed=result.returncode == 0,
        validation_attempts=1,
        errors=errors,
    )


def _run_local_robot_syntax_check(robot_file: Path) -> AutomationValidation:
    """Reproducible local validator used when Robot Framework is unavailable."""
    errors: list[str] = []
    try:
        content = robot_file.read_text(encoding="utf-8")
    except OSError as exc:
        return AutomationValidation(
            artifact_exists=False,
            dry_run_passed=False,
            validation_attempts=1,
            errors=[f"Unable to read Robot file: {exc}"],
        )

    if "*** Settings ***" not in content:
        errors.append("Robot file is missing the Settings section")
    if "*** Test Cases ***" not in content:
        errors.append("Robot file is missing the Test Cases section")
    if "Library" not in content:
        errors.append("Robot file does not declare any library")
    executable_lines = [
        line
        for line in content.splitlines()
        if line.startswith("    ") and not line.strip().startswith("#")
    ]
    if not executable_lines:
        errors.append("Robot file has no executable test steps")

    return AutomationValidation(
        artifact_exists=robot_file.is_file(),
        dry_run_passed=not errors,
        dry_run_skipped_reason=(
            "Robot Framework CLI is not installed; local structural validation was used"
        ),
        validation_attempts=1,
        errors=errors,
    )


def _validate_known_keywords(robot_file: Path) -> list[str]:
    known = {capability.name.lower() for capability in list_robot_keyword_capabilities(include_corpus=True)}
    known |= BUILTIN_KEYWORDS
    errors: list[str] = []
    in_test_cases = False
    try:
        lines = robot_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return [f"Unable to read Robot file for keyword validation: {exc}"]

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("***") and stripped.endswith("***"):
            in_test_cases = stripped.strip("* ").lower() == "test cases"
            continue
        if not in_test_cases or not raw_line.startswith((" ", "\t")):
            continue
        cells = _robot_cells(stripped)
        if not cells:
            continue
        first_cell = cells[0].strip()
        # Skip variable-assignment cells (e.g. "${USERS} =" / "@{LIST} ="): the
        # keyword is the NEXT cell, which we validate instead.
        if first_cell.startswith(("${", "@{", "&{")):
            if len(cells) < 2:
                continue
            first_cell = cells[1].strip()
        lowered = first_cell.lower()
        if first_cell.startswith("[") or lowered in ROBOT_CONTROL_TOKENS:
            continue
        if lowered not in known:
            errors.append(
                f"Unknown Robot keyword '{first_cell}' in {robot_file.relative_to(PROJECT_ROOT)}. "
                "Generated automation must use BuiltIn or approved reference-corpus keywords."
            )
    return errors


def _robot_cells(text: str) -> list[str]:
    if "    " in text:
        return [cell.strip() for cell in text.split("    ") if cell.strip()]
    return [cell.strip() for cell in text.split("\t") if cell.strip()]
