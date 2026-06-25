from __future__ import annotations

import json
from pathlib import Path

from backend.artifacts.base import (
    ArtifactRecord,
    ArtifactStoreMode,
    BaseArtifactStore,
    artifact_store_registry,
)
from backend.graph.artifacts import (
    GENERATED_ARTIFACT_ROOT,
    PROJECT_ROOT,
    relative_to_project,
    slug,
)


@artifact_store_registry.register(
    name="local_fs",
    mode=ArtifactStoreMode.LOCAL,
    description="Local filesystem artifact store for workflow execution evidence.",
    root="configured-generated-root/artifacts",
    requires_external_api=False,
)
class LocalFilesystemArtifactStore(BaseArtifactStore):
    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or GENERATED_ARTIFACT_ROOT).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "index.jsonl"

    def put_text(
        self,
        *,
        context_id: str,
        kind: str,
        name: str,
        content: str,
        content_type: str = "text/plain",
        description: str = "",
        metadata: dict[str, object] | None = None,
    ) -> ArtifactRecord:
        safe_context = slug(context_id)
        safe_kind = slug(kind)
        safe_name = Path(name).name
        if not safe_name:
            raise ValueError("Artifact name cannot be empty")
        target_dir = self.root / safe_context / safe_kind
        target_dir.mkdir(parents=True, exist_ok=True)
        target = (target_dir / safe_name).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Artifact path escapes the local artifact store") from exc
        target.write_text(content, encoding="utf-8")
        record = ArtifactRecord(
            context_id=context_id,
            kind=kind,
            path=relative_to_project(target),
            content_type=content_type,
            description=description,
            metadata=metadata or {},
        )
        self._append_index(record)
        return record

    def read_text(self, record: ArtifactRecord) -> str:
        path = (PROJECT_ROOT / record.path).resolve()
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Artifact path is outside the configured local store") from exc
        return path.read_text(encoding="utf-8")

    def list(self, *, context_id: str | None = None) -> list[ArtifactRecord]:
        if not self.index_path.exists():
            return []
        records: list[ArtifactRecord] = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = ArtifactRecord.model_validate(json.loads(line))
            if context_id is None or record.context_id == context_id:
                records.append(record)
        return records

    def _append_index(self, record: ArtifactRecord) -> None:
        with self.index_path.open("a", encoding="utf-8") as stream:
            stream.write(record.model_dump_json() + "\n")
