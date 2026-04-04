import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_store
from app.main import app
from app.storage.fs_store import FSStore
from app.storage.errors import ConflictError


@pytest.fixture
def client(tmp_path) -> TestClient:
    store = FSStore(base_dir=tmp_path / "data")
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_and_get_style(client: TestClient) -> None:
    create_response = client.post("/styles", json={"name": "Nolan Warm V1"})
    assert create_response.status_code == 201

    created = create_response.json()
    assert created["name"] == "Nolan Warm V1"
    assert created["slug"] == "nolan-warm-v1"
    style_id = created["style_id"]

    get_response = client.get(f"/styles/{style_id}")
    assert get_response.status_code == 200
    assert get_response.json()["style_id"] == style_id

    missing_response = client.get("/styles/missing-style")
    assert missing_response.status_code == 404


def test_list_styles_returns_created_styles(client: TestClient) -> None:
    response_a = client.post("/styles", json={"name": "Style A"})
    response_b = client.post("/styles", json={"name": "Style B"})
    assert response_a.status_code == 201
    assert response_b.status_code == 201

    list_response = client.get("/styles")
    assert list_response.status_code == 200
    names = {style["name"] for style in list_response.json()}
    assert "Style A" in names
    assert "Style B" in names


def test_create_style_rejects_duplicate_slug(client: TestClient) -> None:
    first = client.post("/styles", json={"name": "Tokyo Night"})
    second = client.post("/styles", json={"name": "Tokyo Night"})

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["message"] == "style slug already exists: tokyo-night"


def test_create_style_rejects_blank_slug(client: TestClient) -> None:
    response = client.post("/styles", json={"name": "Tokyo Night", "slug": "   "})

    assert response.status_code == 422
    assert response.json()["error_id"] == "validation_error"


def test_create_and_get_style_version(client: TestClient) -> None:
    create_style_response = client.post("/styles", json={"name": "Film Warm"})
    assert create_style_response.status_code == 201
    style_id = create_style_response.json()["style_id"]

    payload = {
        "version": "v1",
        "style_spec": {
            "name": "Film Warm",
            "intent": ["warm", "cinematic"],
            "captureone": {
                "keys": {
                    "Exposure": 0.35,
                    "Contrast": 12,
                }
            },
        },
    }
    create_version_response = client.post(f"/styles/{style_id}/versions", json=payload)
    assert create_version_response.status_code == 201

    created_version = create_version_response.json()
    assert created_version["style_id"] == style_id
    assert created_version["version"] == "v1"
    assert created_version["safe_policy"]["remove_lens_light_falloff"] is True
    assert created_version["safe_policy"]["remove_white_balance"] is True
    assert created_version["safe_policy"]["remove_exposure"] is False

    get_version_response = client.get(f"/styles/{style_id}/versions/v1")
    assert get_version_response.status_code == 200
    version_data = get_version_response.json()
    assert version_data["style_spec"]["captureone"]["keys"]["Exposure"] == 0.35
    assert version_data["style_spec"]["captureone"]["keys"]["Contrast"] == 12

    missing_version_response = client.get(f"/styles/{style_id}/versions/missing")
    assert missing_version_response.status_code == 404

    missing_style_create_response = client.post(
        "/styles/missing-style/versions",
        json=payload,
    )
    assert missing_style_create_response.status_code == 404


def test_create_style_version_rejects_duplicate_version(client: TestClient) -> None:
    create_style_response = client.post("/styles", json={"name": "Film Warm"})
    style_id = create_style_response.json()["style_id"]
    payload = {
        "version": "v1",
        "style_spec": {
            "name": "Film Warm",
            "intent": ["warm", "cinematic"],
            "captureone": {"keys": {"Exposure": 0.35, "Contrast": 12}},
        },
    }

    first = client.post(f"/styles/{style_id}/versions", json=payload)
    duplicate = client.post(f"/styles/{style_id}/versions", json=payload)

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["message"] == f"style version already exists: {style_id}/v1"


def test_create_style_returns_conflict_from_store_override(tmp_path) -> None:
    class ConflictStore(FSStore):
        def create_style(self, style):  # type: ignore[override]
            raise ConflictError("style slug already exists: duplicated")

    store = ConflictStore(base_dir=tmp_path / "data")
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as test_client:
        response = test_client.post("/styles", json={"name": "Duplicated"})
    app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["message"] == "style slug already exists: duplicated"
