from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

from backend.config.settings import settings
from backend.graph.artifacts import GENERATED_KNOWLEDGE_ROOT, PROJECT_ROOT, slug
from backend.knowledge.base import KnowledgeChunk

SUPPORTED_SUFFIXES = {".md", ".txt", ".rst"}


@dataclass(frozen=True)
class IngestionResult:
    document_id: str
    title: str
    source: str
    chunk_ids: list[str]
    chunk_count: int
    tags: list[str]
    stored_path: str | None = None


def local_document_roots() -> list[Path]:
    roots: list[Path] = []
    if settings.knowledge_documents_dir:
        roots.append(Path(settings.knowledge_documents_dir).expanduser())
    roots.append(PROJECT_ROOT / "fixtures" / "knowledge")
    return [root.resolve() for root in roots]


def load_local_document_chunks() -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for root in local_document_roots():
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="latin-1")
            title = _title_from_text_or_path(text, path)
            tags = _tags_from_path(path, root)
            chunks.extend(
                _chunk_text(
                    document_id=f"DOC-{slug(path.stem).upper()}",
                    title=title,
                    source=f"local://knowledge-docs/{path.relative_to(root).as_posix()}",
                    text=text,
                    tags=tags,
                )
            )
    return chunks


def load_ingested_document_chunks() -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    if not GENERATED_KNOWLEDGE_ROOT.is_dir():
        return chunks
    for path in sorted(GENERATED_KNOWLEDGE_ROOT.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in payload.get("chunks", []):
            try:
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=str(item["chunk_id"]),
                        title=str(item["title"]),
                        source=str(item["source"]),
                        text=str(item["text"]),
                        tags=tuple(str(tag) for tag in item.get("tags", [])),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
    return chunks


def ingest_local_document(
    *,
    title: str,
    text: str,
    source: str = "local://manual-upload",
    tags: list[str] | None = None,
) -> IngestionResult:
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Cannot ingest an empty knowledge document")
    clean_title = title.strip() or _title_from_text_or_path(clean_text, Path("document.md"))
    document_id = f"doc-{uuid4().hex[:10]}"
    chunks = _chunk_text(
        document_id=document_id,
        title=clean_title,
        source=source.strip() or "local://manual-upload",
        text=clean_text,
        tags=tuple(tags or []),
    )
    GENERATED_KNOWLEDGE_ROOT.mkdir(parents=True, exist_ok=True)
    stored_path = GENERATED_KNOWLEDGE_ROOT / f"{slug(clean_title)}_{document_id}.json"
    stored_path.write_text(
        json.dumps(
            {
                "document_id": document_id,
                "title": clean_title,
                "source": source,
                "tags": tags or [],
                "chunks": [asdict(chunk) for chunk in chunks],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    reset_local_knowledge_cache()
    return IngestionResult(
        document_id=document_id,
        title=clean_title,
        source=source,
        chunk_ids=[chunk.chunk_id for chunk in chunks],
        chunk_count=len(chunks),
        tags=list(tags or []),
        stored_path=stored_path.as_posix(),
    )


def reset_local_knowledge_cache() -> None:
    from backend.knowledge.local import reset_local_knowledge_store

    reset_local_knowledge_store()


def _chunk_text(
    *,
    document_id: str,
    title: str,
    source: str,
    text: str,
    tags: tuple[str, ...] | list[str],
    max_chars: int = 900,
) -> list[KnowledgeChunk]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    raw_chunks: list[str] = []
    current = ""
    for paragraph in paragraphs or [text]:
        if len(current) + len(paragraph) + 2 <= max_chars:
            current = f"{current}\n\n{paragraph}".strip()
            continue
        if current:
            raw_chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            for offset in range(0, len(paragraph), max_chars):
                raw_chunks.append(paragraph[offset: offset + max_chars])
            current = ""
    if current:
        raw_chunks.append(current)
    return [
        KnowledgeChunk(
            chunk_id=f"{document_id.upper()}-{index:03d}",
            title=title if len(raw_chunks) == 1 else f"{title} / chunk {index}",
            source=source,
            text=chunk,
            tags=tuple(tags),
        )
        for index, chunk in enumerate(raw_chunks, start=1)
    ]


def _title_from_text_or_path(text: str, path: Path) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem.replace("_", " ").title()
    return path.stem.replace("_", " ").replace("-", " ").title()


def _tags_from_path(path: Path, root: Path) -> tuple[str, ...]:
    rel = path.relative_to(root)
    tags = [part.lower().replace(" ", "-") for part in rel.parts[:-1]]
    tags.extend(path.stem.lower().split("_"))
    return tuple(tag for tag in tags if tag)
