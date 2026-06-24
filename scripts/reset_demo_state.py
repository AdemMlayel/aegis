from __future__ import annotations

import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
STORAGE_ROOT = (PROJECT_ROOT / "generated" / "storage").resolve()
DATABASE_PATH = (STORAGE_ROOT / "aegisqa.sqlite3").resolve()
BACKUP_ROOT = (STORAGE_ROOT / "backups").resolve()


def _assert_workspace_path(path: Path) -> None:
    path.relative_to(PROJECT_ROOT)


def main() -> None:
    _assert_workspace_path(DATABASE_PATH)
    _assert_workspace_path(BACKUP_ROOT)
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    if DATABASE_PATH.is_file():
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = BACKUP_ROOT / f"aegisqa-before-reset-{timestamp}.sqlite3"
        shutil.copy2(DATABASE_PATH, backup_path)

    for suffix in ("", "-shm", "-wal"):
        path = Path(f"{DATABASE_PATH}{suffix}").resolve()
        _assert_workspace_path(path)
        if path.is_file():
            path.unlink()

    from backend.storage.database import initialize_database
    from backend.storage.mock_tickets import list_mock_tickets

    initialize_database()
    tickets = list_mock_tickets()
    print(f"Reset runtime database with {len(tickets)} ticket fixtures.")
    if backup_path is not None:
        print(f"Backup: {backup_path}")


if __name__ == "__main__":
    main()
