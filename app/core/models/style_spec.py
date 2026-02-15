from typing import Union

from pydantic import BaseModel, Field, field_validator

from app.core.models.safe_policy import SafePolicy

CaptureOneValue = Union[str, int, float]


class CaptureOneSpec(BaseModel):
    keys: dict[str, CaptureOneValue] = Field(default_factory=dict)
    notes: str | None = None

    @field_validator("keys")
    @classmethod
    def validate_keys_not_empty(cls, value: dict[str, CaptureOneValue]) -> dict[str, CaptureOneValue]:
        if not value:
            raise ValueError("captureone.keys must include at least one key")
        return value


class StyleSpec(BaseModel):
    name: str = Field(min_length=1)
    intent: list[str] = Field(default_factory=list)
    captureone: CaptureOneSpec
    safe: SafePolicy = Field(default_factory=SafePolicy)

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("name must not be blank")
        return trimmed
