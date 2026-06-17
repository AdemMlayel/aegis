from __future__ import annotations

import time

from backend.config.settings import settings
from backend.services.executions import FINAL_EXECUTION_STATUSES, process_execution_run
from backend.storage.execution_runs import list_execution_runs, load_execution_run


def run_polling_worker(*, once: bool = False) -> int:
    """Process queued execution runs without requiring Celery.

    This is the local durable fallback for environments that share the same
    persisted run store but do not run a broker. Docker Compose uses Celery by
    default, while local development can use this polling worker when desired.
    """
    processed = 0
    while True:
        queued_runs = list_execution_runs(
            status="queued",
            limit=settings.execution_worker_batch_size,
        )
        for run in queued_runs:
            latest = load_execution_run(run.run_id)
            if latest is None or latest.status in FINAL_EXECUTION_STATUSES or latest.status != "queued":
                continue
            process_execution_run(latest.run_id)
            processed += 1

        if once:
            return processed
        time.sleep(settings.execution_worker_poll_interval_seconds)


def main() -> None:
    run_polling_worker()


if __name__ == "__main__":
    main()
