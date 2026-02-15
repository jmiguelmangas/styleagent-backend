from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import get_store
from app.storage.fs_store import FSStore

router = APIRouter(tags=["artifacts"])


@router.get("/artifacts/{artifact_id}")
def download_artifact(
    artifact_id: str,
    store: FSStore = Depends(get_store),
) -> FileResponse:
    artifact_result = store.get_artifact(artifact_id)
    if artifact_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="artifact not found")

    artifact, _ = artifact_result
    absolute_path = store.base_dir / Path(artifact.path)
    filename = Path(artifact.path).name

    return FileResponse(
        path=absolute_path,
        media_type="application/octet-stream",
        filename=filename,
    )
