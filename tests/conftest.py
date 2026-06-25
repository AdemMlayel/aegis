from __future__ import annotations

import os
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_RUNTIME_ROOT = (PROJECT_ROOT / "generated" / "test-runtime").resolve()
if TEST_RUNTIME_ROOT.parent == (PROJECT_ROOT / "generated").resolve():
    shutil.rmtree(TEST_RUNTIME_ROOT, ignore_errors=True)

TEST_DB_PATH = TEST_RUNTIME_ROOT / "storage" / "aegisqa-test.sqlite3"
os.environ["AEGISQA_SQLITE_DB_PATH"] = str(TEST_DB_PATH)
os.environ["AEGISQA_GENERATED_ROOT"] = str(TEST_RUNTIME_ROOT)
os.environ["AEGISQA_EXTERNAL_CONNECTORS_ENABLED"] = "false"
os.environ["AEGISQA_DEFAULT_LLM_PROVIDER"] = "mock_llm"
os.environ["AEGISQA_DEFAULT_EMBEDDING_PROVIDER"] = "local_hash_embeddings"
os.environ["AEGISQA_DEFAULT_EXECUTION_ADAPTER"] = "mock"

for suffix in ("", "-shm", "-wal"):
    path = Path(f"{TEST_DB_PATH}{suffix}")
    if path.is_file():
        path.unlink()
