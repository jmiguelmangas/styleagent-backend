from __future__ import annotations

from typing import Protocol

from app.core.models.ai import (
    AIHealthResponse,
    AIPromptPreviewResponse,
    GeneratedStyleSpecResponse,
    PromptGenerateRequest,
)


class AIStyleGenerator(Protocol):
    def generate_style_spec(self, payload: PromptGenerateRequest) -> GeneratedStyleSpecResponse:
        """Generate a style specification from prompt-based input."""

    def preview_prompt(self, payload: PromptGenerateRequest) -> AIPromptPreviewResponse:
        """Render provider prompt preview for debugging and evaluation."""

    def health_check(self) -> AIHealthResponse:
        """Report current provider availability and effective model configuration."""
