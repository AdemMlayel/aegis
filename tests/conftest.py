from __future__ import annotations

import os
from pathlib import Path


TEST_DB_PATH = (
    Path(__file__).resolve().parents[1]
    / "generated"
    / "storage"
    / "aegisqa-test.sqlite3"
)
os.environ["AEGISQA_SQLITE_DB_PATH"] = str(TEST_DB_PATH)
os.environ["AEGISQA_EXTERNAL_CONNECTORS_ENABLED"] = "false"
os.environ["AEGISQA_DEFAULT_LLM_PROVIDER"] = "mock_llm"
os.environ["AEGISQA_DEFAULT_EMBEDDING_PROVIDER"] = "local_hash_embeddings"

for suffix in ("", "-shm", "-wal"):
    path = Path(f"{TEST_DB_PATH}{suffix}")
    if path.is_file():
        path.unlink()
