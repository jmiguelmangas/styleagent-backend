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


def test_list_runner_jobs_is_empty_by_default(client: TestClient) -> None:
    response = client.get("/runner/jobs?status=pending&limit=1")
    assert response.status_code == 200
    assert response.json() == []


def test_runner_job_lifecycle_endpoints(client: TestClient) -> None:
    create_response = client.post(
        "/runner/jobs",
        json={
            "job_type": "compile_captureone",
            "payload": {"style_id": "style_1", "version": "v1"},
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    job_id = created["job_id"]
    assert created["status"] == "pending"

    list_response = client.get("/runner/jobs?status=pending&limit=1")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["job_id"] == job_id

    get_response = client.get(f"/runner/jobs/{job_id}")
    assert get_response.status_code == 200
    assert get_response.json()["job_id"] == job_id

    claim_response = client.post(f"/runner/jobs/{job_id}/claim")
    assert claim_response.status_code == 200
    assert claim_response.json()["status"] == "picked_up"

    heartbeat_response = client.post(
        f"/runner/jobs/{job_id}/heartbeat",
        json={"status": "running"},
    )
    assert heartbeat_response.status_code == 200
    assert heartbeat_response.json()["status"] == "running"

    complete_response = client.post(
        f"/runner/jobs/{job_id}/complete",
        json={
            "status": "succeeded",
            "result": {"artifact_id": "artifact_1"},
            "error": None,
            "logs": [{"event": "job_succeeded"}],
        },
    )
    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["status"] == "succeeded"
    assert completed["result"] == {"artifact_id": "artifact_1"}
    assert completed["logs"] == [{"event": "job_succeeded"}]


def test_runner_job_endpoints_return_404_for_missing_job(client: TestClient) -> None:
    get_response = client.get("/runner/jobs/missing")
    claim_response = client.post("/runner/jobs/missing/claim")
    heartbeat_response = client.post("/runner/jobs/missing/heartbeat", json={"status": "running"})
    complete_response = client.post(
        "/runner/jobs/missing/complete",
        json={"status": "failed", "result": None, "error": "boom", "logs": []},
    )

    assert get_response.status_code == 404
    assert claim_response.status_code == 404
    assert heartbeat_response.status_code == 404
    assert complete_response.status_code == 404

