from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.core.models.style_spec import StyleSpec


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
