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
        assert json["keep_alive"] == "10m"
        assert "Reference examples" in json["prompt"]
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
    assert response.style_spec.captureone.keys["WhiteBalanceTemperature"] >= 5600
    assert "Highlights" in response.style_spec.captureone.keys
    assert "ColorBalanceBlue" in response.style_spec.captureone.keys


def test_ollama_generator_retries_with_cold_start_timeout(monkeypatch) -> None:
    calls: list[float] = []

    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        calls.append(timeout)
        if len(calls) == 1:
            raise httpx.ReadTimeout("cold start timeout")
        return _FakeResponse(
            {
                "response": (
                    '{"name":"AI Retry Success","intent":["cinematic"],'
                    '"captureone":{"keys":{"Contrast":9},"notes":"Retry worked"}}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        timeout_seconds=2.0,
        cold_start_timeout_seconds=15.0,
    )

    response = generator.generate_style_spec(PromptGenerateRequest(prompt="cinematic style"))

    assert calls == [2.0, 15.0]
    assert response.warnings == []
    assert response.style_spec.captureone.keys["Contrast"] == 9


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


def test_ollama_generator_keeps_chat_delta_payload_sparse(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        return _FakeResponse(
            {
                "response": (
                    '{"name":"AI Chat Delta","intent":["portrait"],'
                    '"captureone":{"keys":{"Contrast":7}}}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(
        PromptGenerateRequest(
            prompt="add contrast only",
            intent=["portrait"],
            constraints={
                "mode": "chat_turn_delta",
                "allowed_keys": ["Contrast", "Exposure"],
            },
        )
    )

    assert set(response.style_spec.captureone.keys.keys()) == {"Contrast"}


def test_ollama_generator_respects_max_prompt_examples(monkeypatch) -> None:
    captured_prompt = {"value": ""}

    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        captured_prompt["value"] = json["prompt"]
        return _FakeResponse(
            {
                "response": (
                    '{"name":"AI Test","intent":["cinematic"],'
                    '"captureone":{"keys":{"Contrast":7}}}'
                )
            }
        )

    monkeypatch.setenv("STYLEAGENT_AI_MAX_PROMPT_EXAMPLES", "2")
    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    generator.generate_style_spec(PromptGenerateRequest(prompt="warm moody cinematic landscape"))

    marker = "Reference examples (real styles, use as aesthetic guidance):\n"
    assert marker in captured_prompt["value"]
    section = captured_prompt["value"].split(marker, 1)[1].split("\nInput payload:", 1)[0]
    assert section.count('"source"') <= 2


def test_ollama_generator_uses_semantic_example_for_seasonal_landscape_prompt() -> None:
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    preview = generator.preview_prompt(
        PromptGenerateRequest(
            prompt="moody autumn forest landscape with warm sunlight",
            intent=["landscape", "moody", "autumn"],
        )
    )

    sources = [example["source"] for example in preview.examples]
    assert any("Heavenly Seasons pack /" in source for source in sources)
    assert any("Northlandscapes Moody Landscapes /" in source for source in sources)


def test_ollama_generator_expands_named_style_reference_into_richer_traits(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        assert "gothic cinematic portrait" in json["prompt"].lower()
        assert "tim burton" in json["prompt"].lower()
        return _FakeResponse(
            {
                "response": (
                    '{"name":"AI Gothic Portrait","intent":["portrait"],'
                    '"captureone":{"keys":{"Exposure":0.0,"Contrast":6},"notes":"Generated"}}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(
        PromptGenerateRequest(prompt="portrait in the style of Tim Burton")
    )

    keys = response.style_spec.captureone.keys
    assert keys["Contrast"] >= 16
    assert keys["ColorBalanceBlue"] >= 1
    assert keys["ColorBalanceGreen"] >= 1
    assert keys["ToneCurve"] == "Film Extra Shadow"
