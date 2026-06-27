from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterable

from backend.config.settings import settings
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
    name="robot_docker",
    engine="docker-robot-framework",
    capabilities=("docker-isolation", "robot-framework", "artifact-capture"),
    description=(
        "Executes generated Robot Framework files in a Docker container. "
        "This is disabled gracefully when Docker or the configured image is unavailable."
    ),
)
class DockerRobotExecutionAdapter(BaseExecutionAdapter):
    def execute(
        self,
        context: TestContext,
        *,
        actor: str,
        env: str,
        branch: str | None = None,
        tags: Iterable[str] = (),
    ) -> TestContext:
        docker_cli = shutil.which("docker")
        if docker_cli is None:
            raise ValueError(
                "Docker is not installed or not on PATH; use the local robot or mock adapter for this demo."
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
            case_output = output_root / test_case.id.lower()
            case_output.mkdir(parents=True, exist_ok=True)
            command = [
                docker_cli,
                "run",
                "--rm",
                "--network",
                "none",
                "-v",
                f"{PROJECT_ROOT.as_posix()}:/workspace:ro",
                "-v",
                f"{case_output.as_posix()}:/output",
                "-w",
                "/workspace",
                settings.robot_docker_image,
                "robot",
                "--outputdir",
                "/output",
                automation.robot_file,
            ]
            run_started = utc_now()
            completed = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=settings.robot_docker_timeout_seconds,
                check=False,
            )
            duration_ms = max(0, int((utc_now() - run_started).total_seconds() * 1000))
            stdout_path = case_output / "docker_stdout.log"
            stderr_path = case_output / "docker_stderr.log"
            stdout_path.write_text(completed.stdout or "", encoding="utf-8")
            stderr_path.write_text(completed.stderr or "", encoding="utf-8")
            status = "passed" if completed.returncode == 0 else "failed"
            results.append(
                ExecutionCaseResult(
                    test_case_id=test_case.id,
                    title=test_case.title,
                    status=status,
                    duration_ms=duration_ms,
                    robot_file=automation.robot_file,
                    message=(
                        "Docker-isolated Robot execution completed successfully."
                        if status == "passed"
                        else "Docker-isolated Robot execution failed; inspect output artifacts."
                    ),
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
                (stdout_path, "Docker stdout"),
                (stderr_path, "Docker stderr"),
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
            adapter="robot_docker",
            env=env,
            artifacts=artifacts,
        )
        context.mark(f"robot_docker_execution_{execution_status}")
        context.record_event(
            actor=actor,
            event_type="execution_completed",
            summary=f"Docker Robot execution {execution_status}.",
            metadata={
                "context_id": context.context_id,
                "adapter": "robot_docker",
                "env": env,
                "branch": branch,
                "tags": list(tags),
                "artifact_count": len(artifacts),
                "docker_image": settings.robot_docker_image,
            },
        )
        return context
