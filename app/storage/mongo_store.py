from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from pymongo.results import InsertOneResult

from app.core.models import RunnerJob
from app.storage.fs_store import FSStore


class MongoStore(FSStore):
    """Hybrid store: Mongo for metadata selected in current phase, FS for artifacts/styles."""

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
        self._runner_jobs: Collection = self._db["runner_jobs"]
        self._indexes_ready = False

    def create_runner_job(self, job: RunnerJob) -> RunnerJob:
        self._ensure_indexes()
        payload = job.model_dump(mode="python")
        insert_result: InsertOneResult = self._runner_jobs.insert_one(payload)
        created = self._runner_jobs.find_one({"_id": insert_result.inserted_id})
        if created is None:
            raise ValueError("failed to create runner job")
        return self._runner_job_from_doc(created)

    def get_runner_job(self, job_id: str) -> RunnerJob | None:
        self._ensure_indexes()
        doc = self._runner_jobs.find_one({"job_id": job_id})
        if doc is None:
            return None
        return self._runner_job_from_doc(doc)

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
                    {
                        "status": {"$in": ["picked_up", "running"]},
                        "locked_until": {"$lte": now},
                    },
                ]
            }
        elif status is not None:
            query = {"status": status}

        cursor = self._runner_jobs.find(query).sort("created_at", ASCENDING)
        if limit is not None:
            cursor = cursor.limit(limit)

        return [self._runner_job_from_doc(doc) for doc in cursor]

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

        try:
            doc = self._runner_jobs.find_one_and_update(
                {"job_id": job_id},
                update_ops,
                return_document=ReturnDocument.AFTER,
            )
        except PyMongoError as exc:
            raise ValueError(f"failed to update runner job: {exc}") from exc

        if doc is None:
            return None
        return self._runner_job_from_doc(doc)

    def claim_runner_job(self, job_id: str, *, claimed_by: str = "runner") -> RunnerJob | None:
        self._ensure_indexes()
        now = datetime.now(timezone.utc)
        lock_until = now + self._runner_lock_ttl()
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
        if doc is None:
            return None
        return self._runner_job_from_doc(doc)

    def _runner_job_from_doc(self, doc: dict[str, Any]) -> RunnerJob:
        normalized = {key: value for key, value in doc.items() if key != "_id"}
        return RunnerJob.model_validate(normalized)

    def _ensure_indexes(self) -> None:
        if self._indexes_ready:
            return
        self._runner_jobs.create_index(
            [("status", ASCENDING), ("locked_until", ASCENDING), ("updated_at", DESCENDING)]
        )
        self._runner_jobs.create_index("job_id", unique=True)
        self._indexes_ready = True

    def _runner_lock_ttl(self) -> timedelta:
        raw = os.getenv("RUNNER_JOB_LOCK_TTL_SECONDS", "60").strip()
        try:
            seconds = max(1, int(raw))
        except ValueError:
            seconds = 60
        return timedelta(seconds=seconds)
