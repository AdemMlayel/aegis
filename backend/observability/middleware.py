from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.config.settings import settings
from backend.governance.context import request_context_scope
from backend.governance.gateway import (
    GatewayLimitExceeded,
    gateway_limiter,
)
from backend.observability.structured_logging import log_event
from backend.storage.observability import (
    RequestObservation,
    count_requests_today,
    save_request_observation,
)


logger = logging.getLogger("aegisqa.gateway")
UNMETERED_PATHS = {
    "/health",
    "/health/live",
    "/health/ready",
    "/metrics",
}


def install_gateway_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def governed_gateway(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        actor = (
            request.headers.get("X-Aegis-User")
            or settings.local_user
        )
        organization_id = (
            request.headers.get("X-Aegis-Organization")
            or "local"
        )
        request.state.request_id = request_id
        started = perf_counter()
        status_code = 500
        error_type: str | None = None

        with request_context_scope(
            request_id=request_id,
            actor=actor,
            organization_id=organization_id,
        ):
            try:
                if request.url.path not in UNMETERED_PATHS:
                    gateway_limiter.check_rate(
                        f"{organization_id}:{actor}"
                    )
                    if (
                        count_requests_today(organization_id=organization_id)
                        >= settings.gateway_daily_request_quota
                    ):
                        raise GatewayLimitExceeded(
                            "Organization daily request quota exceeded"
                        )
                response = await asyncio.wait_for(
                    call_next(request),
                    timeout=settings.gateway_request_timeout_seconds,
                )
                status_code = response.status_code
            except GatewayLimitExceeded as exc:
                status_code = 429
                error_type = type(exc).__name__
                response = JSONResponse(
                    status_code=status_code,
                    content={"detail": str(exc)},
                )
            except TimeoutError:
                status_code = 504
                error_type = "GatewayTimeout"
                response = JSONResponse(
                    status_code=status_code,
                    content={"detail": "Gateway request timed out"},
                )
            except Exception as exc:
                error_type = type(exc).__name__
                raise
            finally:
                duration_ms = round((perf_counter() - started) * 1000)
                route = request.scope.get("route")
                observed_path = getattr(
                    route,
                    "path",
                    request.url.path,
                )
                try:
                    save_request_observation(
                        RequestObservation(
                            request_id=request_id,
                            actor=actor,
                            organization_id=organization_id,
                            method=request.method,
                            path=observed_path,
                            status_code=status_code,
                            duration_ms=duration_ms,
                            error_type=error_type,
                        )
                    )
                except Exception as telemetry_exc:  # noqa: BLE001 - telemetry must not replace the API response.
                    log_event(
                        logger,
                        "telemetry_persistence_failed",
                        level=logging.ERROR,
                        request_id=request_id,
                        error_type=type(telemetry_exc).__name__,
                    )
                log_event(
                    logger,
                    "http_request",
                    request_id=request_id,
                    actor=actor,
                    organization_id=organization_id,
                    method=request.method,
                    path=observed_path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    error_type=error_type,
                )

        response.headers["X-Request-ID"] = request_id
        return response
