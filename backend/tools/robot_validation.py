from __future__ import annotations

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
from backend.tools.base import BaseTool, tool_registry


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
            validation.errors = [*errors, *validation.errors]
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
        return AutomationValidation(
            artifact_exists=robot_file.is_file(),
            dry_run_passed=None,
            dry_run_skipped_reason="Robot Framework CLI is not installed",
            validation_attempts=0,
        )

    try:
        result = subprocess.run(
            [
                *command,
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
