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
