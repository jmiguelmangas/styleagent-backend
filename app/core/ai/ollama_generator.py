from __future__ import annotations

from app.core.ai.mock_generator import MockStyleGenerator
from app.core.models.ai import GeneratedStyleSpecResponse, PromptGenerateRequest


class OllamaStyleGenerator:
    """Phase 2 scaffolding for Ollama provider.

    Phase 3 will replace this placeholder implementation with real Ollama inference.
    """

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b-instruct",
    ) -> None:
        self.provider = "ollama"
        self.model = model
        self.base_url = base_url
        self._fallback = MockStyleGenerator(model=model)

    def generate_style_spec(self, payload: PromptGenerateRequest) -> GeneratedStyleSpecResponse:
        response = self._fallback.generate_style_spec(payload)
        response.provider = self.provider
        response.model = self.model
        response.warnings.append("Ollama provider placeholder active; mock generation used.")
        return response
