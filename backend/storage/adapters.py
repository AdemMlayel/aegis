from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.config.settings import settings
from backend.graph.artifacts import GENERATED_STORAGE_ROOT
from backend.storage.migrations import run_migrations


@dataclass(frozen=True)
class StorageAdapterSpec:
    name: str
    mode: Literal["local", "external", "placeholder"] = "local"
    description: str = ""
    requires_external_service: bool = False


class BaseStorageAdapter(ABC):
    spec = StorageAdapterSpec(name="base")

    @abstractmethod
    def initialize(self) -> Path | str:
        raise NotImplementedError

    @abstractmethod
    def connect(self):
        raise NotImplementedError


class SQLiteStorageAdapter(BaseStorageAdapter):
    spec = StorageAdapterSpec(
        name="sqlite",
        mode="local",
        description="Local SQLite storage adapter used for demo and tests.",
        requires_external_service=False,
    )

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or _sqlite_path()

    def initialize(self) -> Path:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            self._configure(connection)
            run_migrations(connection)
        return self.db_path

    def connect(self) -> sqlite3.Connection:
        self.initialize()
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        self._configure(connection)
        return connection

    @staticmethod
    def _configure(connection: sqlite3.Connection) -> None:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")


class PostgresStorageAdapter(BaseStorageAdapter):
    spec = StorageAdapterSpec(
        name="postgres",
        mode="placeholder",
        description=(
            "Future PostgreSQL storage adapter. The interface is present so the "
            "code can migrate without changing services, but it is intentionally "
            "disabled until the project adds a PostgreSQL driver and migrations."
        ),
        requires_external_service=True,
    )

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or settings.database_url

    def initialize(self) -> str:
        raise NotImplementedError(
            "PostgreSQL storage is not implemented in this local demo package. "
            "Use AEGISQA_STORAGE_BACKEND=sqlite until the company runtime is available."
        )

    def connect(self):
        raise NotImplementedError(
            "PostgreSQL storage is not implemented in this local demo package."
        )


class StorageAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, type[BaseStorageAdapter]] = {
            SQLiteStorageAdapter.spec.name: SQLiteStorageAdapter,
            PostgresStorageAdapter.spec.name: PostgresStorageAdapter,
        }

    def create(self, name: str | None = None) -> BaseStorageAdapter:
        selected = (name or settings.storage_backend or "sqlite").strip().lower()
        if selected not in self._adapters:
            raise ValueError(f"Unsupported storage backend: {selected}")
        return self._adapters[selected]()

    def list_specs(self) -> list[StorageAdapterSpec]:
        return sorted((adapter.spec for adapter in self._adapters.values()), key=lambda item: item.name)


def _sqlite_path() -> Path:
    return (
        Path(settings.sqlite_db_path).expanduser().resolve()
        if settings.sqlite_db_path
        else GENERATED_STORAGE_ROOT / "aegisqa.sqlite3"
    )


storage_adapter_registry = StorageAdapterRegistry()
default_storage_adapter = storage_adapter_registry.create()
SQLITE_DB_PATH = _sqlite_path()
