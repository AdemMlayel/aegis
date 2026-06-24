from fastapi import FastAPI

from backend.api.routes.executions import router as executions_router
from backend.api.routes.integrations import router as integrations_router
from backend.api.routes.intelligence import router as intelligence_router
from backend.api.routes.report_packages import router as report_packages_router
from backend.api.routes.security import router as security_router
from backend.api.routes.tickets import router as tickets_router
from backend.api.routes.workflows import router as workflows_router
from backend.api.routes.workflow_control import router as workflow_control_router


app = FastAPI(title="AegisQA", version="0.1.0")
app.include_router(executions_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")
app.include_router(intelligence_router, prefix="/api/v1")
app.include_router(report_packages_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(workflow_control_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
