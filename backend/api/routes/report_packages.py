from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.security import Capability, Principal, require_capability
from backend.services.report_packages import (
    ReportPackageManifest,
    ReportPackageNotFound,
    ReportPackageNotReady,
    build_report_package,
    get_report_package_manifest,
    render_executive_report,
    render_technical_report,
)
from backend.storage.audit import append_audit_event


router = APIRouter(tags=["report-packages"])


@router.get(
    "/workflows/{context_id}/package/manifest",
    response_model=ReportPackageManifest,
)
def read_report_package_manifest(
    context_id: str,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_ARTIFACTS)),
    ],
) -> ReportPackageManifest:
    return _translate_package_errors(
        lambda: get_report_package_manifest(context_id)
    )


@router.get("/workflows/{context_id}/package/technical.md")
def read_technical_report(
    context_id: str,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_ARTIFACTS)),
    ],
) -> Response:
    content = _translate_package_errors(lambda: render_technical_report(context_id))
    return Response(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": (
                f'attachment; filename="aegisqa-{context_id}-technical.md"'
            )
        },
    )


@router.get("/workflows/{context_id}/package/executive.md")
def read_executive_report(
    context_id: str,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_ARTIFACTS)),
    ],
) -> Response:
    content = _translate_package_errors(lambda: render_executive_report(context_id))
    return Response(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": (
                f'attachment; filename="aegisqa-{context_id}-executive.md"'
            )
        },
    )


@router.get("/workflows/{context_id}/package.zip")
def download_report_package(
    context_id: str,
    principal: Annotated[
        Principal,
        Depends(require_capability(Capability.READ_ARTIFACTS)),
    ],
) -> Response:
    package = _translate_package_errors(lambda: build_report_package(context_id))
    append_audit_event(
        actor=principal.user_id,
        event_type="report_package_exported",
        summary="Workflow report package exported.",
        metadata={
            "context_id": context_id,
            "file_name": package.file_name,
            "package_status": package.manifest.package_status,
            "file_count": len(package.manifest.files),
        },
    )
    return Response(
        content=package.content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{package.file_name}"'
        },
    )


def _translate_package_errors(action):
    try:
        return action()
    except ReportPackageNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ReportPackageNotReady as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
