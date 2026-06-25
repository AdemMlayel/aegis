from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.config.settings import settings
from backend.graph.artifacts import GENERATED_STORAGE_ROOT
from backend.storage.migrations import run_migrations


SQLITE_DB_PATH = (
    Path(settings.sqlite_db_path).expanduser().resolve()
    if settings.sqlite_db_path
    else GENERATED_STORAGE_ROOT / "aegisqa.sqlite3"
)


def initialize_database(db_path: Path = SQLITE_DB_PATH) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        _configure_connection(connection)
        run_migrations(connection)
    return db_path


def connect(db_path: Path = SQLITE_DB_PATH) -> sqlite3.Connection:
    initialize_database(db_path)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    _configure_connection(connection)
    return connection


def _configure_connection(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
