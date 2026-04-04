from datetime import datetime, timedelta, timezone

import mongomock
import pytest

from app.core.models import (
    AIGenerationRecord,
    AIConversationGuidance,
    AIChatSession,
    AIChatTurn,
    RunnerJob,
    SafePolicy,
    Style,
    StyleSpec,
    StyleVersion,
)
from app.storage.errors import ConflictError
from app.storage.mongo_store import MongoStore


@pytest.fixture
def store(tmp_path, monkeypatch) -> MongoStore:
    monkeypatch.setattr("app.storage.mongo_store.MongoClient", mongomock.MongoClient)
    return MongoStore(db_url="mongodb://unused/test", db_name="test", base_dir=tmp_path / "data")


def _style_spec(name: str = "Tokyo Night") -> StyleSpec:
    return StyleSpec(
        name=name,
        intent=["cinematic"],
        captureone={"keys": {"Exposure": 0.2, "Contrast": 10}},
    )


def test_mongo_store_rejects_duplicate_style_slug(store: MongoStore) -> None:
    store.create_style(Style(name="Tokyo Night", slug="tokyo-night"))

    with pytest.raises(ConflictError, match="style slug already exists: tokyo-night"):
        store.create_style(Style(name="Tokyo Night 2", slug="tokyo-night"))


def test_mongo_store_rejects_duplicate_style_version(store: MongoStore) -> None:
    style = store.create_style(Style(name="Tokyo Night", slug="tokyo-night"))
    version = StyleVersion(
        style_id=style.style_id,
        version="v1",
        style_spec=_style_spec(),
        safe_policy=SafePolicy(),
    )

    store.create_version(style.style_id, version)

    with pytest.raises(
        ConflictError,
        match=rf"style version already exists: {style.style_id}/v1",
    ):
        store.create_version(style.style_id, version)


def test_mongo_store_persists_artifact_metadata_and_bytes(store: MongoStore) -> None:
    style = store.create_style(Style(name="Tokyo Night", slug="tokyo-night"))
    version = StyleVersion(
        style_id=style.style_id,
        version="v1",
        style_spec=_style_spec(),
        safe_policy=SafePolicy(remove_white_balance=False),
    )
    store.create_version(style.style_id, version)

    artifact = store.save_artifact(
        style.style_id,
        "v1",
        "captureone",
        "Tokyo_Night.costyle",
        b"<SL></SL>",
    )
    stored = store.get_artifact(artifact.artifact_id)

    assert stored is not None
    meta, content = stored
    assert meta.style_id == style.style_id
    assert meta.version == "v1"
    assert meta.target == "captureone"
    assert content == b"<SL></SL>"


def test_mongo_store_claims_expired_runner_job(store: MongoStore) -> None:
    expired = datetime.now(timezone.utc) - timedelta(minutes=1)
    job = RunnerJob(
        job_type="compile_captureone",
        payload={"style_id": "style_1", "version": "v1", "execution_mode": "host"},
        status="running",
        claimed_by="other-runner",
        locked_until=expired,
        attempt=1,
    )
    store.create_runner_job(job)

    claimed = store.claim_runner_job(job.job_id, claimed_by="runner")

    assert claimed is not None
    assert claimed.status == "running"
    assert claimed.claimed_by == "runner"
    assert claimed.attempt == 2
    assert claimed.locked_until is not None
    assert claimed.locked_until > datetime.now(timezone.utc)


def test_mongo_store_persists_ai_generation_and_chat_records(store: MongoStore) -> None:
    generation = AIGenerationRecord(
        client_key="test-client",
        prompt="tokyo night cinematic portrait",
        intent=["cinematic", "portrait"],
        target="captureone",
        style_spec=_style_spec(),
        provider="mock",
        model="mock-v1",
    )
    session = AIChatSession(
        title="Tokyo Night",
        style_spec=_style_spec(),
    )
    turn = AIChatTurn(
        session_id=session.session_id,
        user_message="Make it cooler in the shadows.",
        assistant_message="Try cooler shadows and warmer highlights.",
        proposed_changes=[],
        guidance=AIConversationGuidance(
            detected_goals=["cooler shadows"],
            reasoning_summary="Shifted the look cooler while keeping the portrait cinematic.",
            suggested_next_messages=["Make it more filmic"],
        ),
    )

    store.create_ai_generation(generation)
    store.create_ai_chat_session(session)
    store.create_ai_chat_turn(turn)

    generations = store.list_ai_generations(limit=10)
    sessions = [store.get_ai_chat_session(session.session_id)]
    turns = store.list_ai_chat_turns(session.session_id, limit=10)

    assert generations[0].generation_id == generation.generation_id
    assert sessions[0] is not None
    assert sessions[0].session_id == session.session_id
    assert turns[0].turn_id == turn.turn_id
    assert turns[0].assistant_message == "Try cooler shadows and warmer highlights."
