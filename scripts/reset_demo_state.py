from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
GENERATED_ROOT = (PROJECT_ROOT / "generated").resolve()
DATABASE_PATH = GENERATED_ROOT / "storage" / "aegisqa.sqlite3"


def _assert_workspace_path(path: Path) -> None:
    path.resolve().relative_to(PROJECT_ROOT)


def reset_demo_state(*, keep_backup: bool = False) -> Path | None:
    _assert_workspace_path(GENERATED_ROOT)
    backup_bytes: bytes | None = None
    backup_name: str | None = None
    if keep_backup and DATABASE_PATH.is_file():
        backup_bytes = DATABASE_PATH.read_bytes()
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_name = f"aegisqa-before-reset-{timestamp}.sqlite3"

    if GENERATED_ROOT.is_dir():
        shutil.rmtree(GENERATED_ROOT)
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    if backup_bytes is not None and backup_name is not None:
        backup_root = GENERATED_ROOT / "backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        backup_path = backup_root / backup_name
        backup_path.write_bytes(backup_bytes)

    os.environ["AEGISQA_GENERATED_ROOT"] = str(GENERATED_ROOT)
    os.environ["AEGISQA_SQLITE_DB_PATH"] = str(DATABASE_PATH)
    from backend.storage.database import initialize_database
    from backend.storage.mock_tickets import list_mock_tickets

    initialize_database(DATABASE_PATH)
    tickets = list_mock_tickets()
    print(f"Reset demo runtime with {len(tickets)} ticket fixtures and no workflow history.")
    if backup_path is not None:
        print(f"Backup: {backup_path}")
    return backup_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove generated runtime data and create a clean ticket-only demo state."
    )
    parser.add_argument(
        "--keep-backup",
        action="store_true",
        help="Keep a copy of the previous SQLite database under generated/backups.",
    )
    args = parser.parse_args()
    reset_demo_state(keep_backup=args.keep_backup)


if __name__ == "__main__":
    main()
