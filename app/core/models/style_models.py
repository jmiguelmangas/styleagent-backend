from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.models.safe_policy import SafePolicy
from app.core.models.style_spec import StyleSpec
from app.core.utils import generate_id, slugify


class StyleCreate(BaseModel):
    name: str = Field(
        min_length=1,
        description="Human-readable style name (for example: 'Nolan Warm V1').",
    )
    slug: str | None = Field(
        default=None,
        description="Optional URL-friendly identifier. If omitted, generated from name.",
    )

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
    style_id: str = Field(default_factory=generate_id, description="Unique style identifier.")
    name: str = Field(min_length=1, description="Style display name.")
    slug: str = Field(min_length=1, description="URL-safe style slug.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC.",
    )


class StyleVersionCreate(BaseModel):
    version: str = Field(min_length=1, description="Version label (for example: 'v1').")
    style_spec: StyleSpec = Field(description="Style specification used for compilation.")
    safe_policy: SafePolicy | None = Field(
        default=None,
        description="Optional override for safe-policy rules. Defaults to style_spec.safe.",
    )

    @field_validator("version")
    @classmethod
    def validate_version_not_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("version must not be blank")
        return trimmed


class StyleVersion(BaseModel):
    style_id: str = Field(min_length=1, description="Related style identifier.")
    version: str = Field(min_length=1, description="Version label.")
    style_spec: StyleSpec = Field(description="Stored style specification payload.")
    safe_policy: SafePolicy = Field(
        default_factory=SafePolicy,
        description="Resolved safe-policy used for compile/export.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC.",
    )


class Artifact(BaseModel):
    artifact_id: str = Field(
        default_factory=generate_id,
        description="Unique artifact identifier.",
    )
    style_id: str = Field(min_length=1, description="Related style identifier.")
    version: str = Field(min_length=1, description="Version label used to compile artifact.")
    target: Literal["captureone"] = Field(description="Compilation target.")
    path: str = Field(min_length=1, description="Filesystem-relative artifact path.")
    sha256: str = Field(
        min_length=64,
        max_length=64,
        description="SHA-256 digest of artifact bytes.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC.",
    )


class CompileResponse(BaseModel):
    artifact_id: str = Field(description="Generated artifact identifier.")
    sha256: str = Field(description="SHA-256 digest of generated artifact.")
    download_url: str = Field(description="Relative URL to download the artifact file.")
