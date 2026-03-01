from app.core.ai.factory import get_ai_generator_instance
from app.core.ai.mock_generator import MockStyleGenerator
from app.core.ai.ollama_generator import OllamaStyleGenerator


def test_ai_factory_defaults_to_mock(monkeypatch) -> None:
    monkeypatch.delenv("STYLEAGENT_AI_PROVIDER", raising=False)
    monkeypatch.delenv("STYLEAGENT_AI_MODEL", raising=False)
    monkeypatch.delenv("STYLEAGENT_AI_BASE_URL", raising=False)

    get_ai_generator_instance.cache_clear()
    generator = get_ai_generator_instance()

    assert isinstance(generator, MockStyleGenerator)
    assert generator.model == "mock-v1"


def test_ai_factory_selects_ollama(monkeypatch) -> None:
    monkeypatch.setenv("STYLEAGENT_AI_PROVIDER", "ollama")
    monkeypatch.setenv("STYLEAGENT_AI_MODEL", "llama3.1:8b-instruct")
    monkeypatch.setenv("STYLEAGENT_AI_BASE_URL", "http://localhost:11434")

    get_ai_generator_instance.cache_clear()
    generator = get_ai_generator_instance()

    assert isinstance(generator, OllamaStyleGenerator)
    assert generator.model == "llama3.1:8b-instruct"
    assert generator.base_url == "http://localhost:11434"


def test_ai_factory_falls_back_to_mock_for_unknown_provider(monkeypatch) -> None:
    monkeypatch.setenv("STYLEAGENT_AI_PROVIDER", "unknown")
    monkeypatch.delenv("STYLEAGENT_AI_MODEL", raising=False)

    get_ai_generator_instance.cache_clear()
    generator = get_ai_generator_instance()

    assert isinstance(generator, MockStyleGenerator)
    assert generator.model == "mock-v1"
