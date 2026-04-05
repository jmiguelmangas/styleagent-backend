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
        assert "Allowed families" in json["prompt"]
        assert "Reference examples" in json["prompt"]
        assert timeout == 20.0
        return _FakeResponse(
            {
                "response": (
                    '{"family":"cinematic_portrait","refinements":["warm_skin","soft_rolloff"],'
                    '"intensity":"balanced","name":"AI Cinematic Warm","notes":"Generated"}'
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
    assert response.style_spec.name == "AI Cinematic Warm"
    assert response.planner_trace is not None
    assert response.planner_trace.mode == "family_planner"
    assert response.planner_trace.family_id == "cinematic_portrait"
    assert "warm_skin" in response.planner_trace.refinement_ids
    assert response.style_spec.captureone.keys["Contrast"] >= 10
    assert response.style_spec.captureone.keys["WhiteBalanceTemperature"] >= 5400
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
                    '{"family":"cinematic_portrait","refinements":["cool_teal"],'
                    '"intensity":"balanced","name":"AI Retry Success","notes":"Retry worked"}'
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
    assert response.planner_trace is not None
    assert response.planner_trace.family_id == "cinematic_portrait"
    assert response.style_spec.captureone.keys["Contrast"] >= 9


def test_ollama_generator_fallback_when_invalid_json(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        return _FakeResponse({"response": "{not-valid-json"})

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(PromptGenerateRequest(prompt="moody warm"))

    assert response.provider == "ollama"
    assert response.model == "llama3.1:8b"
    assert any("fallback mock used" in warning for warning in response.warnings)
    assert response.planner_trace is not None
    assert response.planner_trace.mode == "mock_rule_based"
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
    assert response.planner_trace is not None
    assert response.planner_trace.mode == "mock_rule_based"
    assert response.style_spec.captureone.keys


def test_ollama_generator_keeps_chat_delta_payload_sparse(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        assert "Do not output Capture One key values directly." not in json["prompt"]
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
    assert response.planner_trace is not None
    assert response.planner_trace.mode == "direct_style_spec"


def test_ollama_generator_respects_max_prompt_examples(monkeypatch) -> None:
    captured_prompt = {"value": ""}

    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        captured_prompt["value"] = json["prompt"]
        return _FakeResponse(
            {
                "response": (
                    '{"family":"cinematic_portrait","refinements":["soft_rolloff"],'
                    '"intensity":"balanced","name":"AI Test"}'
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
    assert "Allowed families" in captured_prompt["value"]


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
        assert "gothic fantasy" in json["prompt"].lower()
        assert "cinematic portrait" in json["prompt"].lower()
        assert "tim burton" in json["prompt"].lower()
        return _FakeResponse(
            {
                "response": (
                    '{"family":"gothic_fantasy","refinements":["porcelain_skin","moonlit_blue"],'
                    '"intensity":"bold","name":"AI Gothic Portrait","notes":"Generated"}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(
        PromptGenerateRequest(prompt="portrait in the style of Tim Burton")
    )

    keys = response.style_spec.captureone.keys
    assert response.planner_trace is not None
    assert response.planner_trace.family_id == "gothic_fantasy"
    assert keys["Contrast"] >= 16
    assert keys["ColorBalanceBlue"] >= 1
    assert keys["ColorBalanceGreen"] >= 1
    assert keys["ToneCurve"] == "Film Extra Shadow"


def test_ollama_generator_falls_back_when_planner_selects_unknown_family(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        return _FakeResponse(
            {
                "response": (
                    '{"family":"unknown_family","refinements":["soft_rolloff"],'
                    '"intensity":"balanced","name":"Broken Plan"}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(PromptGenerateRequest(prompt="cinematic portrait"))

    assert response.provider == "ollama"
    assert any("fallback mock used" in warning for warning in response.warnings)
    assert response.planner_trace is not None
    assert response.planner_trace.mode == "mock_rule_based"


def test_ollama_generator_normalizes_pastel_maternity_family(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        return _FakeResponse(
            {
                "response": (
                    '{"family":"bridal_luminous","refinements":["warm_skin","soft_rolloff"],'
                    '"intensity":"subtle","name":"Pastel Motherhood"}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(
        PromptGenerateRequest(
            prompt="pastel maternity portrait with milky tones, luminous skin and gentle blush warmth"
        )
    )

    assert response.planner_trace is not None
    assert response.planner_trace.mode == "family_planner"
    assert response.planner_trace.family_id == "pastel_airy"
    assert response.planner_trace.intensity == "subtle"
    assert response.style_spec.captureone.keys["Contrast"] <= 5
    assert response.style_spec.captureone.keys["Clarity"] <= 5


def test_ollama_generator_normalizes_snowy_architecture_family(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        return _FakeResponse(
            {
                "response": (
                    '{"family":"cozy_autumn","refinements":["soft_highlights","cool_white"],'
                    '"intensity":"balanced","name":"Winter Minimalist"}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(
        PromptGenerateRequest(
            prompt="minimal winter architecture scene with clean whites, cold steel and soft blue daylight"
        )
    )

    assert response.planner_trace is not None
    assert response.planner_trace.mode == "family_planner"
    assert response.planner_trace.family_id == "crisp_winter"
    assert response.planner_trace.intensity == "balanced"
    assert response.style_spec.captureone.keys["Contrast"] >= 8
    assert response.style_spec.captureone.keys["WhiteBalanceTemperature"] <= 5500


def test_ollama_generator_normalizes_food_firelight_family(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        return _FakeResponse(
            {
                "response": (
                    '{"family":"clean_commercial","refinements":["warm_grain","rich_reds"],'
                    '"intensity":"balanced","name":"Restaurant Firelight"}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(
        PromptGenerateRequest(
            prompt="restaurant food photo with firelit warmth, glossy sauce and rich charred texture"
        )
    )

    assert response.planner_trace is not None
    assert response.planner_trace.family_id == "food_rich_color"


def test_ollama_generator_normalizes_product_tech_family(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        return _FakeResponse(
            {
                "response": (
                    '{"family":"editorial_fashion","refinements":["cool_teal","soft_rolloff"],'
                    '"intensity":"bold","name":"Luxury Watch"}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(
        PromptGenerateRequest(
            prompt="luxury smartwatch product shot on black acrylic with icy highlights and precise contrast"
        )
    )

    assert response.planner_trace is not None
    assert response.planner_trace.family_id == "clean_commercial"


def test_ollama_generator_normalizes_wildlife_safari_family(monkeypatch) -> None:
    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        return _FakeResponse(
            {
                "response": (
                    '{"family":"portra_film","refinements":["warm_skin"],'
                    '"intensity":"balanced","name":"Safari Realism"}'
                )
            }
        )

    monkeypatch.setattr(httpx, "post", _fake_post)
    generator = OllamaStyleGenerator(base_url="http://localhost:11434", model="llama3.1:8b")

    response = generator.generate_style_spec(
        PromptGenerateRequest(
            prompt="safari wildlife portrait with dry golden grass, dusty air and restrained documentary realism"
        )
    )

    assert response.planner_trace is not None
    assert response.planner_trace.family_id == "travel_earth"
