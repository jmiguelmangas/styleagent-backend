from __future__ import annotations

from typing import Protocol

from app.core.models.ai import GeneratedStyleSpecResponse, PromptGenerateRequest


class AIStyleGenerator(Protocol):
    def generate_style_spec(self, payload: PromptGenerateRequest) -> GeneratedStyleSpecResponse:
        """Generate a style specification from prompt-based input."""
