from __future__ import annotations

from pathlib import Path

from app.storage.fs_store import FSStore


class MongoStore(FSStore):
    """Temporary Mongo-selected store.

    PR2 keeps behavior stable by delegating to filesystem while the store interface
    and selection plumbing are introduced. PR3 will implement real Mongo persistence.
    """

    def __init__(
        self,
        *,
        db_url: str,
        db_name: str = "styleagent",
        base_dir: str | Path = "data",
    ) -> None:
        super().__init__(base_dir=base_dir)
        self.db_url = db_url
        self.db_name = db_name

