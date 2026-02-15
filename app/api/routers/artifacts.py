from pathlib import Path as FilePath

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import FileResponse

from app.api.deps import get_store
from app.storage.fs_store import FSStore

router = APIRouter(tags=["artifacts"])


@router.get(
    "/artifacts/{artifact_id}",
    summary="Download Artifact",
    description="Download a previously compiled artifact binary by artifact identifier.",
    response_description="Artifact file stream.",
)
def download_artifact(
    artifact_id: str = Path(..., description="Artifact identifier."),
    store: FSStore = Depends(get_store),
) -> FileResponse:
    artifact_result = store.get_artifact(artifact_id)
    if artifact_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="artifact not found")

    artifact, _ = artifact_result
    absolute_path = store.base_dir / FilePath(artifact.path)
    filename = FilePath(artifact.path).name

    return FileResponse(
        path=absolute_path,
        media_type="application/octet-stream",
        filename=filename,
    )
