import httpx

from app.core.ai.ollama_generator import OllamaStyleGenerator
from app.core.models.ai import PromptGenerateRequest


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"status={self.status_code}",
                request=httpx.Request("POST", "http://localhost"),
                response=httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self._payload


def test_ollama_generator_returns_model_output(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        assert url == "http://localhost:11434/api/generate"
        assert json["stream"] is False
        assert json["format"] == "json"
        assert timeout == 20.0
        return _FakeResponse(
            {
                "response": (
                    '{"name":"AI Cinematic Warm","intent":["cinematic","warm"],'
                    '"captureone":{"keys":{"Contrast":10,"Exposure":0.2},"notes":"Generated"}}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(
        PromptGenerateRequest(prompt="cinematic warm portrait", intent=["portrait"])
    )

    assert response.provider == "ollama"
    assert response.model == "llama3.1:8b"
    assert response.warnings == []
    assert response.style_spec.captureone.keys["Contrast"] == 10


def test_ollama_generator_fallback_when_invalid_json(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        return _FakeResponse({"response": "{not-valid-json"})

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(PromptGenerateRequest(prompt="moody warm"))

    assert response.provider == "ollama"
    assert response.model == "llama3.1:8b"
    assert any("fallback mock used" in warning for warning in response.warnings)
    assert response.style_spec.captureone.keys


def test_ollama_generator_fallback_when_http_error(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        return _FakeResponse({}, status_code=500)

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(PromptGenerateRequest(prompt="bright airy profile"))

    assert response.provider == "ollama"
    assert response.model == "llama3.1:8b"
    assert any("fallback mock used" in warning for warning in response.warnings)
    assert response.style_spec.captureone.keys
