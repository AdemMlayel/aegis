from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Iterable
from importlib.util import find_spec

from backend.execution.base import BaseExecutionAdapter, execution_adapter_registry
from backend.graph.artifacts import PROJECT_ROOT, execution_output_dir, relative_to_project
from backend.graph.state import (
    ExecutionArtifact,
    ExecutionBlock,
    ExecutionCaseResult,
    ExecutionSummary,
    TestContext,
    utc_now,
)


@execution_adapter_registry.register(
    name="robot",
    engine="robot-framework",
    capabilities=("local-cli", "robot-framework", "artifact-capture"),
    description="Executes generated Robot Framework files with the local Robot CLI.",
)
class RobotExecutionAdapter(BaseExecutionAdapter):
    def execute(
        self,
        context: TestContext,
        *,
        actor: str,
        env: str,
        branch: str | None = None,
        tags: Iterable[str] = (),
    ) -> TestContext:
        command = _robot_command()
        if command is None:
            raise ValueError(
                "Robot Framework CLI is not installed; install the project dependencies "
                "or use the mock adapter only for automated tests"
            )
        if not context.test_cases or not context.automation:
            raise ValueError("Workflow has no generated automation to execute")

        started_at = utc_now()
        output_root = execution_output_dir(context.context_id)
        output_root.mkdir(parents=True, exist_ok=True)
        results: list[ExecutionCaseResult] = []
        artifacts: list[ExecutionArtifact] = []

        for test_case in context.test_cases:
            automation = context.automation.get(test_case.id)
            if automation is None:
                results.append(
                    ExecutionCaseResult(
                        test_case_id=test_case.id,
                        title=test_case.title,
                        status="skipped",
                        robot_file=None,
                        message="Skipped because no generated automation artifact exists.",
                    )
                )
                continue

            robot_file = (PROJECT_ROOT / automation.robot_file).resolve()
            case_output = output_root / test_case.id.lower()
            case_output.mkdir(parents=True, exist_ok=True)
            run_started = utc_now()
            completed = subprocess.run(
                [
                    *command,
                    "--outputdir",
                    str(case_output),
                    "--name",
                    f"AegisQA {test_case.id}",
                    str(robot_file),
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            duration_ms = max(
                0, int((utc_now() - run_started).total_seconds() * 1000)
            )
            stdout_path = case_output / "stdout.log"
            stderr_path = case_output / "stderr.log"
            stdout_path.write_text(completed.stdout or "", encoding="utf-8")
            stderr_path.write_text(completed.stderr or "", encoding="utf-8")
            status = "passed" if completed.returncode == 0 else "failed"
            message = (
                "Robot execution completed successfully."
                if status == "passed"
                else "Robot execution failed; inspect captured output artifacts."
            )
            results.append(
                ExecutionCaseResult(
                    test_case_id=test_case.id,
                    title=test_case.title,
                    status=status,
                    duration_ms=duration_ms,
                    robot_file=automation.robot_file,
                    message=message,
                    logs=[
                        completed.stdout.strip()[-1000:] if completed.stdout else "",
                        completed.stderr.strip()[-1000:] if completed.stderr else "",
                    ],
                )
            )
            for artifact_path, description in (
                (case_output / "output.xml", "Robot output XML"),
                (case_output / "log.html", "Robot HTML log"),
                (case_output / "report.html", "Robot HTML report"),
                (stdout_path, "Robot stdout"),
                (stderr_path, "Robot stderr"),
            ):
                if artifact_path.exists():
                    artifacts.append(
                        ExecutionArtifact(
                            kind="robot-output" if artifact_path.suffix == ".xml" else "log",
                            path=relative_to_project(artifact_path),
                            content_type="application/xml" if artifact_path.suffix == ".xml" else "text/plain",
                            description=description,
                        )
                    )

        finished_at = utc_now()
        summary = ExecutionSummary(
            total=len(results),
            passed=sum(1 for result in results if result.status == "passed"),
            failed=sum(1 for result in results if result.status == "failed"),
            skipped=sum(1 for result in results if result.status == "skipped"),
            duration_ms=sum(result.duration_ms for result in results),
        )
        execution_status = "failed" if summary.failed else "skipped" if summary.skipped and not summary.passed else "passed"
        context.execution = ExecutionBlock(
            status=execution_status,
            run_by=actor,
            started_at=started_at,
            finished_at=finished_at,
            summary=summary,
            results=results,
            adapter="robot",
            env=env,
            artifacts=artifacts,
        )
        context.mark(f"robot_execution_{execution_status}")
        context.record_event(
            actor=actor,
            event_type="execution_completed",
            summary=f"Robot execution {execution_status}.",
            metadata={
                "context_id": context.context_id,
                "adapter": "robot",
                "env": env,
                "branch": branch,
                "tags": list(tags),
                "artifact_count": len(artifacts),
            },
        )
        return context


def _robot_command() -> list[str] | None:
    robot_cli = shutil.which("robot")
    if robot_cli is not None:
        return [robot_cli]
    if find_spec("robot") is not None:
        return [sys.executable, "-m", "robot"]
    return None
