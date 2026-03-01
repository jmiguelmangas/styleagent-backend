from __future__ import annotations

import os
from functools import lru_cache

from app.core.ai.base import AIStyleGenerator
from app.core.ai.mock_generator import MockStyleGenerator
from app.core.ai.ollama_generator import OllamaStyleGenerator


@lru_cache
def get_ai_generator_instance() -> AIStyleGenerator:
    provider = os.getenv("STYLEAGENT_AI_PROVIDER", "mock").strip().lower() or "mock"
    model = os.getenv("STYLEAGENT_AI_MODEL", "").strip()

    if provider == "ollama":
        ollama_base_url = os.getenv("STYLEAGENT_AI_BASE_URL", "http://localhost:11434").strip()
        effective_model = model or "llama3.1:8b"
        return OllamaStyleGenerator(base_url=ollama_base_url, model=effective_model)

    # Fallback-safe default for unknown or missing providers.
    effective_model = model or "mock-v1"
    return MockStyleGenerator(model=effective_model)
