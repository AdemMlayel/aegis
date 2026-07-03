from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.api.routes.chat import router as chat_router
from backend.api.routes.executions import router as executions_router
from backend.api.routes.governance import router as governance_router
from backend.api.routes.integrations import router as integrations_router
from backend.api.routes.intelligence import router as intelligence_router
from backend.api.routes.report_packages import router as report_packages_router
from backend.api.routes.security import router as security_router
from backend.api.routes.tickets import router as tickets_router
from backend.api.routes.workflows import router as workflows_router
from backend.api.routes.workflow_control import router as workflow_control_router
from backend.config.settings import settings
from backend.observability import (
    configure_structured_logging,
    install_gateway_middleware,
    liveness_status,
    readiness_status,
    render_prometheus_metrics,
)
from backend.governance.gateway import GatewayLimitExceeded
from backend.governance.policy import AgentPolicyDenied
from backend.storage.contexts import OptimisticConcurrencyError


configure_structured_logging()
app = FastAPI(title="AegisQA", version="0.1.0")

# CORS (C4): browsers may only call this API from explicitly allow-listed
# origins. Combined with the unauthenticated default posture, a wildcard here
# would let any web page drive state-changing POSTs, so origins are explicit
# and credentials are allowed only against that fixed list (never "*").
_cors_origins = [
    origin.strip()
    for origin in settings.cors_allow_origins.split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_gateway_middleware(app)
app.include_router(chat_router, prefix="/api/v1")
app.include_router(executions_router, prefix="/api/v1")
app.include_router(governance_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")
app.include_router(intelligence_router, prefix="/api/v1")
app.include_router(report_packages_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(workflow_control_router, prefix="/api/v1")


@app.exception_handler(AgentPolicyDenied)
def agent_policy_denied(
    request: Request,
    exc: AgentPolicyDenied,
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(GatewayLimitExceeded)
def gateway_limit_exceeded(
    request: Request,
    exc: GatewayLimitExceeded,
) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": str(exc)})


@app.exception_handler(OptimisticConcurrencyError)
def optimistic_concurrency_conflict(
    request: Request,
    exc: OptimisticConcurrencyError,
) -> JSONResponse:
    # W1: a concurrent writer modified the same workflow context between our load
    # and save. Surface 409 so the client reloads and retries instead of the
    # write silently clobbering the other writer's changes.
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/live")
def health_live() -> dict[str, object]:
    return liveness_status()


@app.get("/health/ready")
def health_ready() -> JSONResponse:
    payload, status_code = readiness_status()
    return JSONResponse(status_code=status_code, content=payload)


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> PlainTextResponse:
    return PlainTextResponse(
        render_prometheus_metrics(),
        media_type="text/plain; version=0.0.4",
    )
