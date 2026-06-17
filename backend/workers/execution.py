from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from backend.config.settings import settings
from backend.services.executions import process_execution_run


LocalEnqueue = Callable[[str], None]


@dataclass(frozen=True)
class WorkerBackendSpec:
    name: str
    mode: str
    description: str
    durable: bool
    requires_broker: bool = False


@dataclass(frozen=True)
class WorkerDispatchResult:
    run_id: str
    backend: str
    durable: bool
    task_id: str | None = None
    fallback_used: bool = False
    message: str = ""


class ExecutionWorkerBackend(Protocol):
    spec: WorkerBackendSpec

    def enqueue_execution(
        self,
        run_id: str,
        *,
        local_enqueue: LocalEnqueue | None = None,
    ) -> WorkerDispatchResult:
        ...


class ExecutionWorkerBackendRegistry:
    def __init__(self) -> None:
        self._backends: dict[str, type[ExecutionWorkerBackend]] = {}

    def register(self, backend: type[ExecutionWorkerBackend]) -> type[ExecutionWorkerBackend]:
        self._backends[backend.spec.name] = backend
        return backend

    def has(self, name: str) -> bool:
        return name in self._backends

    def create(self, name: str) -> ExecutionWorkerBackend:
        backend = self._backends.get(name)
        if backend is None:
            raise KeyError(f"Execution worker backend '{name}' is not registered")
        return backend()

    def list_specs(self) -> list[WorkerBackendSpec]:
        return sorted((backend.spec for backend in self._backends.values()), key=lambda spec: spec.name)


execution_worker_backend_registry = ExecutionWorkerBackendRegistry()


@execution_worker_backend_registry.register
class LocalExecutionWorkerBackend:
    spec = WorkerBackendSpec(
        name="local",
        mode="background-task",
        description="Dispatches execution through the local FastAPI background task fallback.",
        durable=False,
        requires_broker=False,
    )

    def enqueue_execution(
        self,
        run_id: str,
        *,
        local_enqueue: LocalEnqueue | None = None,
    ) -> WorkerDispatchResult:
        if local_enqueue is None:
            process_execution_run(run_id)
            message = "Execution run processed synchronously by the local fallback."
        else:
            local_enqueue(run_id)
            message = "Execution run queued on the local background fallback."
        return WorkerDispatchResult(
            run_id=run_id,
            backend=self.spec.name,
            durable=self.spec.durable,
            message=message,
        )


@execution_worker_backend_registry.register
class CeleryExecutionWorkerBackend:
    spec = WorkerBackendSpec(
        name="celery",
        mode="brokered-task",
        description="Dispatches execution to a Celery-compatible worker through Redis.",
        durable=True,
        requires_broker=True,
    )

    def enqueue_execution(
        self,
        run_id: str,
        *,
        local_enqueue: LocalEnqueue | None = None,
    ) -> WorkerDispatchResult:
        try:
            from backend.workers.celery_app import celery_app

            async_result = celery_app.send_task(settings.celery_task_name, args=[run_id])
            return WorkerDispatchResult(
                run_id=run_id,
                backend=self.spec.name,
                durable=self.spec.durable,
                task_id=async_result.id,
                message="Execution run dispatched to Celery.",
            )
        except Exception as exc:  # noqa: BLE001 - broker/import failures use local fallback.
            if not settings.celery_fallback_to_local or local_enqueue is None:
                raise
            local_enqueue(run_id)
            return WorkerDispatchResult(
                run_id=run_id,
                backend="local",
                durable=False,
                fallback_used=True,
                message=f"Celery dispatch unavailable; local fallback used: {exc}",
            )


def dispatch_execution_run(
    run_id: str,
    *,
    local_enqueue: LocalEnqueue | None = None,
    backend_name: str | None = None,
) -> WorkerDispatchResult:
    selected_backend = backend_name or settings.execution_worker_backend
    if not execution_worker_backend_registry.has(selected_backend):
        if local_enqueue is None:
            process_execution_run(run_id)
        else:
            local_enqueue(run_id)
        return WorkerDispatchResult(
            run_id=run_id,
            backend="local",
            durable=False,
            fallback_used=True,
            message=f"Unknown worker backend '{selected_backend}'; local fallback used.",
        )
    backend = execution_worker_backend_registry.create(selected_backend)
    return backend.enqueue_execution(run_id, local_enqueue=local_enqueue)
