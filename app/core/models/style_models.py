from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.models.style_spec import SafePolicySpec, StyleSpec
from app.core.utils import generate_id, slugify


class StyleCreate(BaseModel):
    name: str = Field(min_length=1)
    slug: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("name must not be blank")
        return trimmed

    @model_validator(mode="after")
    def set_slug_from_name(self) -> "StyleCreate":
        if self.slug is None:
            self.slug = slugify(self.name)
        return self


class Style(BaseModel):
    style_id: str = Field(default_factory=generate_id)
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StyleVersionCreate(BaseModel):
    version: str = Field(min_length=1)
    style_spec: StyleSpec
    safe_policy: SafePolicySpec | None = None

    @field_validator("version")
    @classmethod
    def validate_version_not_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("version must not be blank")
        return trimmed


class StyleVersion(BaseModel):
    style_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    style_spec: StyleSpec
    safe_policy: SafePolicySpec = Field(default_factory=SafePolicySpec)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Artifact(BaseModel):
    artifact_id: str = Field(default_factory=generate_id)
    style_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    target: Literal["captureone"]
    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
