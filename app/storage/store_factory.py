from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from app.storage.base import Store
from app.storage.fs_store import FSStore
from app.storage.mongo_store import MongoStore


@lru_cache
def get_store_instance() -> Store:
    db_url = os.getenv("STYLEAGENT_DB_URL", "").strip()
    db_name = os.getenv("MONGO_DB_NAME", "styleagent").strip() or "styleagent"
    base_dir = Path(os.getenv("STYLEAGENT_DATA_DIR", "data"))

    if db_url.startswith("mongodb://") or db_url.startswith("mongodb+srv://"):
        return MongoStore(db_url=db_url, db_name=db_name, base_dir=base_dir)

    return FSStore(base_dir=base_dir)

