from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.utils import generate_id

RunnerJobType = Literal["compile_captureone"]
RunnerJobStatus = Literal["pending", "picked_up", "running", "succeeded", "failed"]
RunnerExecutionMode = Literal["api", "host"]
HostErrorCode = Literal[
    "APP_NOT_INSTALLED",
    "APPLE_EVENT_DENIED",
    "OPEN_TIMEOUT",
    "IMPORT_DIR_NOT_WRITABLE",
    "DOWNLOAD_FAILED",
]
HostLaunchMethod = Literal["open", "cli"]


class RunnerCompilePayload(BaseModel):
    style_id: str = Field(min_length=1, description="Target style identifier.")
    version: str = Field(min_length=1, description="Target style version.")
    execution_mode: RunnerExecutionMode = Field(
        default="api",
        description="Runner execution mode. `api` keeps backend-only compile, `host` enables desktop app integration.",
    )


class RunnerJobCreate(BaseModel):
    job_type: RunnerJobType = Field(description="Runner job type.")
    payload: RunnerCompilePayload = Field(description="Runner job payload.")


class HostIntegrationResult(BaseModel):
    mode: Literal["host"] = Field(description="Host execution mode marker.")
    launch_method: HostLaunchMethod | None = Field(
        default=None,
        description="Method used to trigger Capture One import (`open` or `cli`).",
    )
    captureone_app_path: str | None = Field(default=None, description="Capture One application path.")
    imported_costyle_path: str | None = Field(default=None, description="Local imported .costyle path.")
    error_code: HostErrorCode | None = Field(default=None, description="Host integration error code.")
    error_message: str | None = Field(default=None, description="Host integration error message.")
    error_details: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured diagnostics for host integration failures.",
    )


class RunnerJobResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    artifact_id: str | None = Field(default=None, description="Compiled artifact identifier.")
    sha256: str | None = Field(default=None, description="Compiled artifact SHA256.")
    download_url: str | None = Field(default=None, description="Compiled artifact download URL.")
    host_integration: HostIntegrationResult | None = Field(
        default=None,
        description="Optional host-mode integration result details.",
    )


class RunnerJob(BaseModel):
    job_id: str = Field(default_factory=generate_id, description="Unique runner job id.")
    job_type: RunnerJobType = Field(description="Runner job type.")
    payload: RunnerCompilePayload = Field(description="Runner job payload.")
    status: RunnerJobStatus = Field(default="pending", description="Current runner job status.")
    claimed_by: str | None = Field(default=None, description="Runner instance currently owning the job.")
    locked_until: datetime | None = Field(
        default=None,
        description="Lease expiration timestamp in UTC for in-progress jobs.",
    )
    attempt: int = Field(default=0, ge=0, description="Number of processing attempts.")
    result: RunnerJobResult | None = Field(default=None, description="Optional execution result payload.")
    error: str | None = Field(default=None, description="Optional execution error.")
    logs: list[dict[str, Any]] = Field(default_factory=list, description="Structured execution logs.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Update timestamp in UTC.",
    )


class RunnerJobHeartbeat(BaseModel):
    status: RunnerJobStatus = Field(description="Runner heartbeat status.")


class RunnerJobComplete(BaseModel):
    status: Literal["succeeded", "failed"] = Field(description="Final job status.")
    result: RunnerJobResult | None = Field(default=None, description="Execution result.")
    error: str | None = Field(default=None, description="Execution error message.")
    logs: list[dict[str, Any]] = Field(default_factory=list, description="Execution logs.")
