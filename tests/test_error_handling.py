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


def test_404_error_response_is_structured_with_request_id(client: TestClient) -> None:
    response = client.get("/styles/missing", headers={"X-Request-ID": "req-123"})

    assert response.status_code == 404
    assert response.headers["x-request-id"] == "req-123"

    payload = response.json()
    assert payload["error_id"] == "not_found"
    assert payload["message"] == "style not found"
    assert payload["context"]["request_id"] == "req-123"


def test_validation_error_response_is_structured(client: TestClient) -> None:
    response = client.post("/styles", json={"name": "   "})

    assert response.status_code == 422
    assert response.headers["x-request-id"]

    payload = response.json()
    assert payload["error_id"] == "validation_error"
    assert payload["message"] == "request validation failed"
    assert payload["context"]["request_id"]
    assert payload["context"]["errors"]
