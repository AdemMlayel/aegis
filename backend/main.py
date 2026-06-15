from fastapi import FastAPI

from backend.api.routes.tickets import router as tickets_router
from backend.api.routes.workflows import router as workflows_router


app = FastAPI(title="AegisQA", version="0.1.0")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
