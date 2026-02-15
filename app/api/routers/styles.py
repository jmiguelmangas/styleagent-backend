from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_store
from app.core.models import SafePolicySpec, Style, StyleCreate, StyleVersion, StyleVersionCreate
from app.storage.fs_store import FSStore

router = APIRouter(prefix="/styles", tags=["styles"])


@router.post("", response_model=Style, status_code=status.HTTP_201_CREATED)
def create_style(payload: StyleCreate, store: FSStore = Depends(get_store)) -> Style:
    style = Style(name=payload.name, slug=payload.slug or "")
    return store.create_style(style)


@router.get("/{style_id}", response_model=Style)
def get_style(style_id: str, store: FSStore = Depends(get_store)) -> Style:
    style = store.get_style(style_id)
    if style is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="style not found")
    return style


@router.post(
    "/{style_id}/versions",
    response_model=StyleVersion,
    status_code=status.HTTP_201_CREATED,
)
def create_style_version(
    style_id: str,
    payload: StyleVersionCreate,
    store: FSStore = Depends(get_store),
) -> StyleVersion:
    safe_policy = payload.safe_policy or SafePolicySpec.model_validate(
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
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{style_id}/versions/{version}", response_model=StyleVersion)
def get_style_version(
    style_id: str, version: str, store: FSStore = Depends(get_store)
) -> StyleVersion:
    stored = store.get_version(style_id, version)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version not found")
    return stored
