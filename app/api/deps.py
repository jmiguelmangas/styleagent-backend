from pathlib import Path

from app.storage.fs_store import FSStore


def get_store() -> FSStore:
    return FSStore(base_dir=Path("data"))
