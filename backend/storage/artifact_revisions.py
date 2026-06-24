from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import Field

from backend.graph.state import StrictModel, utc_now
from backend.storage.database import connect, initialize_database


class ArtifactRevision(StrictModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    context_id: str
    test_case_id: str
    artifact_path: str
    version: int = Field(ge=1)
    source: Literal["generated", "manual"]
    actor: str
    comment: str | None = None
    content: str
    created_at: datetime = Field(default_factory=utc_now)


def save_artifact_revision(revision: ArtifactRevision) -> ArtifactRevision:
    initialize_database()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO artifact_revisions (
                id,
                context_id,
                test_case_id,
                artifact_path,
                version,
                source,
                actor,
                comment,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                revision.id,
                revision.context_id,
                revision.test_case_id,
                revision.artifact_path,
                revision.version,
                revision.source,
                revision.actor,
                revision.comment,
                revision.content,
                revision.created_at.isoformat(),
            ),
        )
    return revision


def list_artifact_revisions(
    *,
    context_id: str,
    test_case_id: str,
) -> list[ArtifactRevision]:
    initialize_database()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                context_id,
                test_case_id,
                artifact_path,
                version,
                source,
                actor,
                comment,
                content,
                created_at
            FROM artifact_revisions
            WHERE context_id = ? AND test_case_id = ?
            ORDER BY version ASC
            """,
            (context_id, test_case_id),
        ).fetchall()
    return [
        ArtifactRevision(
            id=row["id"],
            context_id=row["context_id"],
            test_case_id=row["test_case_id"],
            artifact_path=row["artifact_path"],
            version=row["version"],
            source=row["source"],
            actor=row["actor"],
            comment=row["comment"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]
