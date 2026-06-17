from __future__ import annotations

from backend.config.settings import settings
from backend.services.executions import process_execution_run

try:
    from celery import Celery
except ImportError as exc:  # pragma: no cover - exercised when optional extra is absent.
    raise RuntimeError(
        "Celery is not installed. Install the worker extra or use AEGISQA_EXECUTION_WORKER_BACKEND=local."
    ) from exc


celery_app = Celery(
    "aegisqa",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)


@celery_app.task(name=settings.celery_task_name)
def process_execution_task(run_id: str) -> str:
    process_execution_run(run_id)
    return run_id
