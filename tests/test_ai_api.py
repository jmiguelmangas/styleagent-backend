import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_store
from app.api.routers.ai import reset_ai_rate_limiter_for_tests
from app.core.ai.factory import get_ai_generator_instance
from app.main import app
from app.storage.fs_store import FSStore


@pytest.fixture
def store(tmp_path) -> FSStore:
    return FSStore(base_dir=tmp_path / "data")


@pytest.fixture
def client(store: FSStore) -> TestClient:
    app.dependency_overrides[get_store] = lambda: store
    reset_ai_rate_limiter_for_tests()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    reset_ai_rate_limiter_for_tests()


def test_generate_style_spec_returns_mock_payload(client: TestClient, store: FSStore) -> None:
    response = client.post(
        "/ai/generate-style-spec",
        json={
            "prompt": "Create a moody warm cinematic preset for portraits",
            "intent": ["portrait", "moody"],
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-v1"
    assert payload["rationale"]
    assert isinstance(payload["generation_ms"], int)
    assert payload["fallback_used"] is False

    style_spec = payload["style_spec"]
    assert style_spec["name"].startswith("AI ")
    assert style_spec["intent"] == ["portrait", "moody"]
    assert style_spec["captureone"]["keys"]["Contrast"] >= 8
    assert style_spec["captureone"]["keys"]["ColorBalanceRed"] == 4

    history = store.list_ai_generations()
    assert len(history) == 1
    assert history[0].prompt == "Create a moody warm cinematic preset for portraits"
    assert history[0].provider == "mock"
    assert history[0].model == "mock-v1"
    assert history[0].style_spec.name.startswith("AI ")


def test_generate_style_spec_rejects_blank_prompt(client: TestClient) -> None:
    response = client.post(
        "/ai/generate-style-spec",
        json={"prompt": "   "},
    )

    assert response.status_code == 422


def test_generate_style_spec_rejects_unsupported_target(client: TestClient) -> None:
    response = client.post(
        "/ai/generate-style-spec",
        json={"prompt": "Clean editorial look", "target": "lightroom"},
    )

    assert response.status_code == 422


def test_generate_style_spec_with_ollama_provider(client: TestClient, monkeypatch) -> None:
    class _FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "response": (
                    '{"name":"AI Editorial Clean","intent":["editorial"],'
                    '"captureone":{"keys":{"Exposure":0.1,"Contrast":6}}}'
                )
            }

    def _fake_post(url: str, json: dict, timeout: float):  # noqa: ANN001
        assert url.endswith("/api/generate")
        assert json["model"] == "llama3.1:8b"
        return _FakeResponse()

    monkeypatch.setenv("STYLEAGENT_AI_PROVIDER", "ollama")
    monkeypatch.setenv("STYLEAGENT_AI_MODEL", "llama3.1:8b")
    monkeypatch.setenv("STYLEAGENT_AI_BASE_URL", "http://localhost:11434")
    monkeypatch.setattr(httpx, "post", _fake_post)
    get_ai_generator_instance.cache_clear()

    response = client.post(
        "/ai/generate-style-spec",
        json={"prompt": "Clean editorial look"},
    )
    get_ai_generator_instance.cache_clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "ollama"
    assert payload["model"] == "llama3.1:8b"
    assert payload["warnings"] == []
    assert payload["fallback_used"] is False


def test_generate_style_spec_rate_limited(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("STYLEAGENT_AI_RATE_LIMIT_PER_MINUTE", "1")

    first = client.post("/ai/generate-style-spec", json={"prompt": "first request"})
    second = client.post("/ai/generate-style-spec", json={"prompt": "second request"})

    assert first.status_code == 200
    assert second.status_code == 429
    payload = second.json()
    assert payload["error_id"] == "rate_limited"


def test_generate_style_spec_warns_when_history_persistence_fails(client: TestClient, store: FSStore) -> None:
    def _boom(*_args, **_kwargs):  # noqa: ANN002, ANN003
        raise RuntimeError("storage failure")

    store.create_ai_generation = _boom  # type: ignore[method-assign]
    response = client.post("/ai/generate-style-spec", json={"prompt": "clean crisp preset"})

    assert response.status_code == 200
    payload = response.json()
    assert "Generation saved failed; result returned without history persistence." in payload["warnings"]
