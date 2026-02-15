from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
from typing import Any, Literal

from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.collection import Collection

from app.core.models import Artifact, RunnerJob, Style, StyleVersion
from app.storage.fs_store import FSStore


class MongoStore(FSStore):
    """Hybrid store for current migration phase.

    MongoDB stores:
    - styles
    - style_versions
    - artifacts metadata
    - runner jobs

    Filesystem stores:
    - artifact bytes (.costyle)
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
        self._client = MongoClient(db_url, tz_aware=True)
        self._db = self._client[db_name]
        self._styles: Collection = self._db["styles"]
        self._style_versions: Collection = self._db["style_versions"]
        self._artifacts: Collection = self._db["artifacts"]
        self._runner_jobs: Collection = self._db["runner_jobs"]
        self._indexes_ready = False

    def create_style(self, style: Style) -> Style:
        self._ensure_indexes()
        self._styles.insert_one(style.model_dump(mode="python"))
        return style

    def get_style(self, style_id: str) -> Style | None:
        self._ensure_indexes()
        doc = self._styles.find_one({"style_id": style_id})
        return None if doc is None else Style.model_validate(_without_id(doc))

    def list_styles(self) -> list[Style]:
        self._ensure_indexes()
        cursor = self._styles.find({}).sort("created_at", ASCENDING)
        return [Style.model_validate(_without_id(doc)) for doc in cursor]

    def create_version(self, style_id: str, version: StyleVersion) -> StyleVersion:
        self._ensure_indexes()
        if self.get_style(style_id) is None:
            raise ValueError(f"style not found: {style_id}")

        self._style_versions.insert_one(version.model_dump(mode="python"))
        return version

    def get_version(self, style_id: str, version: str) -> StyleVersion | None:
        self._ensure_indexes()
        doc = self._style_versions.find_one({"style_id": style_id, "version": version})
        return None if doc is None else StyleVersion.model_validate(_without_id(doc))

    def save_artifact(
        self,
        style_id: str,
        version: str,
        target: Literal["captureone"],
        filename: str,
        content: bytes,
    ) -> Artifact:
        self._ensure_indexes()
        style = self.get_style(style_id)
        if style is None:
            raise ValueError(f"style not found: {style_id}")
        if self.get_version(style_id, version) is None:
            raise ValueError(f"version not found: {version}")

        sha256 = hashlib.sha256(content).hexdigest()
        artifact_rel_path = (
            Path("styles")
            / style.slug
            / "versions"
            / version
            / "artifacts"
            / target
            / filename
        )
        artifact_abs_path = self.base_dir / artifact_rel_path
        artifact_abs_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_abs_path.write_bytes(content)

        artifact = Artifact(
            style_id=style_id,
            version=version,
            target=target,
            path=str(artifact_rel_path),
            sha256=sha256,
        )
        self._artifacts.insert_one(artifact.model_dump(mode="python"))
        return artifact

    def get_artifact(self, artifact_id: str) -> tuple[Artifact, bytes] | None:
        self._ensure_indexes()
        doc = self._artifacts.find_one({"artifact_id": artifact_id})
        if doc is None:
            return None
        artifact = Artifact.model_validate(_without_id(doc))
        artifact_path = self.base_dir / artifact.path
        if not artifact_path.exists():
            return None
        return artifact, artifact_path.read_bytes()

    def list_artifacts(self, style_id: str | None = None) -> list[Artifact]:
        self._ensure_indexes()
        query: dict[str, Any] = {}
        if style_id is not None:
            query["style_id"] = style_id
        cursor = self._artifacts.find(query).sort("created_at", ASCENDING)
        return [Artifact.model_validate(_without_id(doc)) for doc in cursor]

    def create_runner_job(self, job: RunnerJob) -> RunnerJob:
        self._ensure_indexes()
        self._runner_jobs.insert_one(job.model_dump(mode="python"))
        return job

    def get_runner_job(self, job_id: str) -> RunnerJob | None:
        self._ensure_indexes()
        doc = self._runner_jobs.find_one({"job_id": job_id})
        return None if doc is None else RunnerJob.model_validate(_without_id(doc))

    def list_runner_jobs(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[RunnerJob]:
        self._ensure_indexes()
        now = datetime.now(timezone.utc)
        query: dict[str, Any] = {}
        if status == "pending":
            query = {
                "$or": [
                    {"status": "pending"},
                    {"status": {"$in": ["picked_up", "running"]}, "locked_until": {"$lte": now}},
                ]
            }
        elif status is not None:
            query = {"status": status}

        cursor = self._runner_jobs.find(query).sort("created_at", ASCENDING)
        if limit is not None:
            cursor = cursor.limit(limit)
        return [RunnerJob.model_validate(_without_id(doc)) for doc in cursor]

    def update_runner_job(
        self,
        job_id: str,
        *,
        status: str | None = None,
        claimed_by: str | None = None,
        locked_until: datetime | None = None,
        attempt_inc: int = 0,
        result: dict | None = None,
        error: str | None = None,
        logs: list[dict] | None = None,
    ) -> RunnerJob | None:
        self._ensure_indexes()
        update_set: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
        update_ops: dict[str, Any] = {"$set": update_set}

        if status is not None:
            update_set["status"] = status
        if claimed_by is not None:
            update_set["claimed_by"] = claimed_by
        if locked_until is not None:
            update_set["locked_until"] = locked_until
        if result is not None:
            update_set["result"] = result
        if error is not None:
            update_set["error"] = error
        if logs is not None:
            update_set["logs"] = logs
        if attempt_inc:
            update_ops["$inc"] = {"attempt": attempt_inc}

        doc = self._runner_jobs.find_one_and_update(
            {"job_id": job_id},
            update_ops,
            return_document=ReturnDocument.AFTER,
        )
        return None if doc is None else RunnerJob.model_validate(_without_id(doc))

    def claim_runner_job(self, job_id: str, *, claimed_by: str = "runner") -> RunnerJob | None:
        self._ensure_indexes()
        now = datetime.now(timezone.utc)
        lock_until = now + _runner_lock_ttl()
        query = {
            "job_id": job_id,
            "$or": [
                {"status": "pending"},
                {"status": {"$in": ["picked_up", "running"]}, "locked_until": {"$lte": now}},
            ],
        }
        update = {
            "$set": {
                "status": "running",
                "claimed_by": claimed_by,
                "locked_until": lock_until,
                "updated_at": now,
            },
            "$inc": {"attempt": 1},
        }
        doc = self._runner_jobs.find_one_and_update(
            query,
            update,
            return_document=ReturnDocument.AFTER,
        )
        return None if doc is None else RunnerJob.model_validate(_without_id(doc))

    def _ensure_indexes(self) -> None:
        if self._indexes_ready:
            return
        self._styles.create_index("style_id", unique=True)
        self._styles.create_index("slug", unique=True)
        self._style_versions.create_index([("style_id", ASCENDING), ("version", ASCENDING)], unique=True)
        self._artifacts.create_index("artifact_id", unique=True)
        self._artifacts.create_index("sha256")
        self._runner_jobs.create_index(
            [("status", ASCENDING), ("locked_until", ASCENDING), ("updated_at", DESCENDING)]
        )
        self._runner_jobs.create_index("job_id", unique=True)
        self._indexes_ready = True


def _without_id(doc: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in doc.items() if key != "_id"}


def _runner_lock_ttl() -> timedelta:
    raw = os.getenv("RUNNER_JOB_LOCK_TTL_SECONDS", "60").strip()
    try:
        seconds = max(1, int(raw))
    except ValueError:
        seconds = 60
    return timedelta(seconds=seconds)

