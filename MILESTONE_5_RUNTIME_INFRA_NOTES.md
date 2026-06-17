# Milestone 5 - Runtime Infrastructure and Retrieval Upgrade

## Goal

Add the next runtime boundary after the service-layer milestone: durable execution dispatch, a containerized local stack, and a stronger local retrieval path for RAG/memory.

## Implemented

### Durable Worker Boundary

- Added `backend/workers/`.
- Added `local` execution worker backend for FastAPI background fallback.
- Added `celery` execution worker backend for Redis/Celery-compatible dispatch.
- Added Celery app/task wiring in `backend/workers/celery_app.py`.
- Added local polling worker entry point: `python -m backend.worker`.
- `/api/v1/execute` now returns worker dispatch metadata.

### Docker Compose

- Added root `Dockerfile` for API/worker.
- Added `frontend/Dockerfile`.
- Added `docker-compose.yml` with:
  - API
  - frontend
  - Redis
  - Postgres
  - Celery worker
- Added `.dockerignore`.

### RAG / Memory Retrieval

- Added deterministic local embedding model: `local_hash_embedding`.
- Added local in-memory vector store: `local_in_memory_vector`.
- Added local hybrid reranker: `local_hybrid_reranker`.
- Upgraded knowledge and memory search to use vector scoring plus lexical/tag reranking.
- Added retention/invalidation controls for local stores.
- Added retrieval profile endpoint: `GET /api/v1/intelligence/retrieval-profile`.

## Verification

```bash
python -m pytest -q
# 86 passed
```

```bash
cd frontend
npm run build
```

```bash
docker compose config
```

`docker compose config` validated the compose file. Docker also emitted a local user-config access warning on this machine, unrelated to compose syntax.

## Remaining Infrastructure Work

- Implement a real Postgres storage adapter behind the current SQLite storage API.
- Add production-grade memory access controls and tenant-aware retention.
- Add external embedding/vector providers such as pgvector, Qdrant, or an internal vector service.
- Add worker retry/dead-letter policies once real CI execution is connected.
