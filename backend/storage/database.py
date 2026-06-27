from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.storage.adapters import SQLITE_DB_PATH, default_storage_adapter


def initialize_database(db_path: Path = SQLITE_DB_PATH) -> Path:
    if db_path != SQLITE_DB_PATH:
        from backend.storage.adapters import SQLiteStorageAdapter

        return SQLiteStorageAdapter(db_path=db_path).initialize()
    initialized = default_storage_adapter.initialize()
    if not isinstance(initialized, Path):
        raise RuntimeError("The selected storage backend does not expose a local path")
    return initialized


def connect(db_path: Path = SQLITE_DB_PATH) -> sqlite3.Connection:
    if db_path != SQLITE_DB_PATH:
        from backend.storage.adapters import SQLiteStorageAdapter

        return SQLiteStorageAdapter(db_path=db_path).connect()
    connection = default_storage_adapter.connect()
    if not isinstance(connection, sqlite3.Connection):
        raise RuntimeError("The selected storage backend is not SQLite-compatible")
    return connection
