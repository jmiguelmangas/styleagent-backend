from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from app.api.deps import get_store
from app.core.models import (
    Artifact,
    CompileResponse,
    SafePolicy,
    Style,
    StyleCreate,
    StyleVersion,
    StyleVersionCreate,
)
from app.core.services import CompileConfigurationError, CompileValidationError, compile_style_version
from app.storage.base import Store
from app.storage.errors import ConflictError

router = APIRouter(prefix="/styles", tags=["styles"])


@router.get(
    "",
    response_model=list[Style],
    summary="List Styles",
    description="Return all styles currently stored in the backend.",
    response_description="List of style resources.",
)
def list_styles(store: Store = Depends(get_store)) -> list[Style]:
    return store.list_styles()


@router.post(
    "",
    response_model=Style,
    status_code=status.HTTP_201_CREATED,
    summary="Create Style",
    description="Create a new style resource. If `slug` is omitted, it is generated from `name`.",
    response_description="Created style resource.",
)
def create_style(
    payload: StyleCreate = Body(..., description="Style creation payload."),
    store: Store = Depends(get_store),
) -> Style:
    style = Style(name=payload.name, slug=payload.slug or "")
    try:
        return store.create_style(style)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get(
    "/{style_id}",
    response_model=Style,
    summary="Get Style",
    description="Fetch a single style by its identifier.",
    response_description="Style resource.",
)
def get_style(
    style_id: str = Path(..., description="Style identifier."),
    store: Store = Depends(get_store),
) -> Style:
    style = store.get_style(style_id)
    if style is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="style not found")
    return style


@router.post(
    "/{style_id}/versions",
    response_model=StyleVersion,
    status_code=status.HTTP_201_CREATED,
    summary="Create Style Version",
    description="Create a new version under an existing style using a StyleSpec payload.",
    response_description="Created style version.",
)
def create_style_version(
    style_id: str = Path(..., description="Style identifier."),
    payload: StyleVersionCreate = Body(..., description="Version creation payload."),
    store: Store = Depends(get_store),
) -> StyleVersion:
    safe_policy = payload.safe_policy or SafePolicy.model_validate(
        payload.style_spec.safe.model_dump()
    )

    version = StyleVersion(
        style_id=style_id,
        version=payload.version,
        style_spec=payload.style_spec,
        safe_policy=safe_policy,
    )

    try:
        return store.create_version(style_id, version)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{style_id}/versions/{version}",
    response_model=StyleVersion,
    summary="Get Style Version",
    description="Fetch a specific stored version for a style.",
    response_description="Style version resource.",
)
def get_style_version(
    style_id: str = Path(..., description="Style identifier."),
    version: str = Path(..., description="Version label (for example: v1)."),
    store: Store = Depends(get_store),
) -> StyleVersion:
    stored = store.get_version(style_id, version)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version not found")
    return stored


@router.get(
    "/{style_id}/artifacts",
    response_model=list[Artifact],
    summary="List Style Artifacts",
    description="List all compiled artifacts that belong to the specified style.",
    response_description="List of artifact metadata.",
)
def list_style_artifacts(
    style_id: str = Path(..., description="Style identifier."),
    store: Store = Depends(get_store),
) -> list[Artifact]:
    style = store.get_style(style_id)
    if style is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="style not found")
    return store.list_artifacts(style_id=style_id)


@router.post(
    "/{style_id}/versions/{version}/compile",
    response_model=CompileResponse,
    summary="Compile Style Version",
    description=(
        "Compile a stored style version into a target artifact (currently Capture One only). "
        "Applies safe-policy filtering and stores the generated artifact."
    ),
    response_description="Metadata of the generated artifact.",
)
def compile_version(
    style_id: str = Path(..., description="Style identifier."),
    version: str = Path(..., description="Version label to compile."),
    target: Literal["captureone"] = Query(
        "captureone",
        description="Compilation target. Current supported value: `captureone`.",
    ),
    store: Store = Depends(get_store),
) -> CompileResponse:
    try:
        artifact = compile_style_version(
            store=store,
            style_id=style_id,
            version=version,
            target=target,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CompileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CompileConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return CompileResponse(
        artifact_id=artifact.artifact_id,
        sha256=artifact.sha256,
        download_url=f"/artifacts/{artifact.artifact_id}",
    )
