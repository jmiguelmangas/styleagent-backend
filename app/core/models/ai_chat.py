from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.models.style_spec import StyleSpec
from app.core.utils import generate_id


class AIParameterChange(BaseModel):
    key: str = Field(min_length=1, description="Capture One key to modify.")
    from_value: float = Field(description="Current numeric value before applying change.")
    to_value: float = Field(description="Target numeric value after applying change.")
    reason: str | None = Field(default=None, description="Optional short rationale for this specific change.")


class AIChatSession(BaseModel):
    session_id: str = Field(default_factory=generate_id, description="Unique AI chat session identifier.")
    title: str | None = Field(default=None, description="Optional user-facing session title.")
    status: Literal["active", "archived"] = Field(default="active", description="Session lifecycle state.")
    style_spec: StyleSpec = Field(description="Current mutable style spec state for this conversation.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp in UTC.",
    )


class AIChatTurn(BaseModel):
    turn_id: str = Field(default_factory=generate_id, description="Unique turn identifier.")
    session_id: str = Field(min_length=1, description="Owning AI chat session identifier.")
    user_message: str = Field(min_length=1, description="User message for this turn.")
    assistant_message: str = Field(min_length=1, description="Assistant response for this turn.")
    proposed_changes: list[AIParameterChange] = Field(
        default_factory=list,
        description="Guard-railed parameter changes proposed for this turn.",
    )
    warnings: list[str] = Field(default_factory=list, description="Guard-rail warnings for skipped/adjusted changes.")
    applied: bool = Field(default=False, description="Whether this turn was applied to session style spec.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC.",
    )


class AIChatSessionCreateRequest(BaseModel):
    title: str | None = Field(default=None, description="Optional session title.")
    style_spec: StyleSpec = Field(description="Initial style spec to seed the AI conversation.")

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class AIChatTurnCreateRequest(BaseModel):
    message: str = Field(min_length=1, description="User prompt/message for this conversation turn.")
    auto_apply: bool = Field(
        default=False,
        description="If true, apply guard-railed proposed changes immediately after generation.",
    )

    @field_validator("message")
    @classmethod
    def validate_message_not_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("message must not be blank")
        return trimmed


class AIChatTurnResponse(BaseModel):
    session: AIChatSession
    turn: AIChatTurn


class AIChatSessionDetail(BaseModel):
    session: AIChatSession
    turns: list[AIChatTurn] = Field(default_factory=list)
