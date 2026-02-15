from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol

from app.core.models import Artifact, RunnerJob, Style, StyleVersion


class Store(Protocol):
    base_dir: Path

    def create_style(self, style: Style) -> Style: ...
    def get_style(self, style_id: str) -> Style | None: ...
    def list_styles(self) -> list[Style]: ...

    def create_version(self, style_id: str, version: StyleVersion) -> StyleVersion: ...
    def get_version(self, style_id: str, version: str) -> StyleVersion | None: ...

    def save_artifact(
        self,
        style_id: str,
        version: str,
        target: Literal["captureone"],
        filename: str,
        content: bytes,
    ) -> Artifact: ...
    def get_artifact(self, artifact_id: str) -> tuple[Artifact, bytes] | None: ...
    def list_artifacts(self, style_id: str | None = None) -> list[Artifact]: ...

    def create_runner_job(self, job: RunnerJob) -> RunnerJob: ...
    def get_runner_job(self, job_id: str) -> RunnerJob | None: ...
    def list_runner_jobs(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[RunnerJob]: ...
    def update_runner_job(
        self,
        job_id: str,
        *,
        status: str | None = None,
        result: dict | None = None,
        error: str | None = None,
        logs: list[dict] | None = None,
    ) -> RunnerJob | None: ...

