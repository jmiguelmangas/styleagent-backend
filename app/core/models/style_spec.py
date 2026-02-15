from typing import Union

from pydantic import BaseModel, Field, field_validator

from app.core.models.safe_policy import SafePolicy

CaptureOneValue = Union[str, int, float]


class CaptureOneSpec(BaseModel):
    keys: dict[str, CaptureOneValue] = Field(
        default_factory=dict,
        description="Capture One key/value overrides to patch into the template.",
    )
    notes: str | None = Field(default=None, description="Optional notes for this capture profile.")

    @field_validator("keys")
    @classmethod
    def validate_keys_not_empty(
        cls, value: dict[str, CaptureOneValue]
    ) -> dict[str, CaptureOneValue]:
        if not value:
            raise ValueError("captureone.keys must include at least one key")
        return value


class StyleSpec(BaseModel):
    name: str = Field(min_length=1, description="Style specification display name.")
    intent: list[str] = Field(
        default_factory=list,
        description="Intent tags (for example: cinematic, warm, moody).",
    )
    captureone: CaptureOneSpec = Field(description="Capture One compile payload.")
    safe: SafePolicy = Field(
        default_factory=SafePolicy,
        description="Safe-policy defaults to apply during compile/export.",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("name must not be blank")
        return trimmed
