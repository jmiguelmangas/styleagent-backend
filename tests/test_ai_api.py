import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_store
from app.main import app
from app.storage.fs_store import FSStore


@pytest.fixture
def client(tmp_path) -> TestClient:
    store = FSStore(base_dir=tmp_path / "data")
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_generate_style_spec_returns_mock_payload(client: TestClient) -> None:
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

    style_spec = payload["style_spec"]
    assert style_spec["name"].startswith("AI ")
    assert style_spec["intent"] == ["portrait", "moody"]
    assert style_spec["captureone"]["keys"]["Contrast"] >= 8
    assert style_spec["captureone"]["keys"]["ColorBalanceRed"] == 4


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
