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


def _create_style_and_version(client: TestClient) -> str:
    style_resp = client.post("/styles", json={"name": "Compile Warm"})
    assert style_resp.status_code == 201
    style_id = style_resp.json()["style_id"]

    version_payload = {
        "version": "v1",
        "style_spec": {
            "name": "Compile Warm",
            "intent": ["cinematic", "warm"],
            "captureone": {
                "keys": {
                    "Exposure": 0.3,
                    "Contrast": 9,
                    "WhiteBalance": "AsShot",
                }
            },
        },
    }
    version_resp = client.post(f"/styles/{style_id}/versions", json=version_payload)
    assert version_resp.status_code == 201
    return style_id


def test_compile_endpoint_returns_artifact_metadata(client: TestClient) -> None:
    style_id = _create_style_and_version(client)

    compile_resp = client.post(f"/styles/{style_id}/versions/v1/compile?target=captureone")
    assert compile_resp.status_code == 200

    payload = compile_resp.json()
    assert payload["artifact_id"]
    assert len(payload["sha256"]) == 64
    assert payload["download_url"].startswith("/artifacts/")


def test_compile_endpoint_returns_404_for_missing_version(client: TestClient) -> None:
    style_id = _create_style_and_version(client)

    missing_resp = client.post(f"/styles/{style_id}/versions/missing/compile?target=captureone")
    assert missing_resp.status_code == 404
