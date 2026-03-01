from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.core.models.style_spec import StyleSpec
from app.core.utils import generate_id


class PromptGenerateRequest(BaseModel):
    prompt: str = Field(
        min_length=1,
        description="Natural-language prompt describing the desired visual style.",
    )
    intent: list[str] | None = Field(
        default=None,
        description="Optional intent tags to guide generation (for example: cinematic, warm, moody).",
    )
    constraints: dict[str, Any] | None = Field(
        default=None,
        description="Optional provider-agnostic constraints for future AI backends.",
    )
    target: Literal["captureone"] = Field(
        default="captureone",
        description="Generation target. Current supported value: `captureone`.",
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt_not_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("prompt must not be blank")
        return trimmed


class GeneratedStyleSpecResponse(BaseModel):
    style_spec: StyleSpec = Field(description="Generated style specification payload.")
    rationale: str | None = Field(
        default=None,
        description="Optional short explanation of generation decisions.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal generation warnings.",
    )
    provider: str = Field(description="Provider identifier used for generation.")
    model: str = Field(description="Model identifier used for generation.")
    generation_ms: int | None = Field(
        default=None,
        description="Generation latency in milliseconds (best effort).",
    )
    fallback_used: bool = Field(
        default=False,
        description="Whether provider generation fell back to mock behavior.",
    )


class AIGenerationRecord(BaseModel):
    generation_id: str = Field(default_factory=generate_id, description="Unique AI generation identifier.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC.",
    )
    client_key: str = Field(min_length=1, description="Client identifier used for rate-limiting/audit.")
    prompt: str = Field(min_length=1, description="Input natural-language prompt.")
    intent: list[str] | None = Field(
        default=None,
        description="Optional intent tags submitted by client.",
    )
    constraints: dict[str, Any] | None = Field(
        default=None,
        description="Optional constraints submitted by client.",
    )
    target: Literal["captureone"] = Field(description="Generation target.")
    style_spec: StyleSpec = Field(description="Generated style specification payload.")
    rationale: str | None = Field(
        default=None,
        description="Optional model rationale.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Generation warnings.",
    )
    provider: str = Field(description="Provider identifier used for generation.")
    model: str = Field(description="Model identifier used for generation.")
    generation_ms: int | None = Field(
        default=None,
        description="Generation latency in milliseconds.",
    )
    fallback_used: bool = Field(
        default=False,
        description="Whether provider generation fell back to mock behavior.",
    )


class AIPromptPreviewResponse(BaseModel):
    provider: str = Field(description="Provider identifier used for preview.")
    model: str = Field(description="Model identifier used for preview.")
    prompt: str = Field(description="Rendered provider prompt that would be sent to the model.")
    examples_count: int = Field(
        ge=0,
        description="Number of in-context examples injected into the prompt.",
    )
    examples: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Selected in-context examples used to build the prompt.",
    )
