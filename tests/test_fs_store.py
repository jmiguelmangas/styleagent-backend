import hashlib

from app.core.models import AIGenerationRecord, SafePolicy, Style, StyleSpec, StyleVersion
from app.storage.fs_store import FSStore


def _build_style() -> Style:
    return Style(name="Nolan Warm", slug="nolan-warm")


def _build_style_version(style_id: str, version: str = "1") -> StyleVersion:
    spec = StyleSpec(
        name="Nolan Warm",
        intent=["cinematic", "warm"],
        captureone={"keys": {"Exposure": 0.25}},
    )
    return StyleVersion(
        style_id=style_id,
        version=version,
        style_spec=spec,
        safe_policy=SafePolicy(),
    )


def test_create_and_get_style_roundtrip(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    style = _build_style()

    created = store.create_style(style)
    loaded = store.get_style(created.style_id)

    assert loaded is not None
    assert loaded.style_id == created.style_id
    assert loaded.slug == "nolan-warm"
    assert (tmp_path / "data" / "styles" / "nolan-warm" / "style.json").exists()


def test_create_and_get_version_roundtrip(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    style = store.create_style(_build_style())
    version = _build_style_version(style.style_id, version="v1")

    created = store.create_version(style.style_id, version)
    loaded = store.get_version(style.style_id, "v1")

    assert loaded is not None
    assert loaded.style_id == style.style_id
    assert loaded.version == created.version
    assert (tmp_path / "data" / "styles" / "nolan-warm" / "versions" / "v1" / "spec.json").exists()
    assert (
        tmp_path / "data" / "styles" / "nolan-warm" / "versions" / "v1" / "policy.json"
    ).exists()


def test_save_and_get_artifact_roundtrip(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    style = store.create_style(_build_style())
    version = _build_style_version(style.style_id, version="v2")
    store.create_version(style.style_id, version)

    content = b"<costyle>test</costyle>"
    artifact = store.save_artifact(
        style_id=style.style_id,
        version="v2",
        target="captureone",
        filename="NolanWarm.costyle",
        content=content,
    )

    loaded = store.get_artifact(artifact.artifact_id)

    assert loaded is not None
    loaded_artifact, loaded_content = loaded
    assert loaded_content == content
    assert loaded_artifact.sha256 == hashlib.sha256(content).hexdigest()
    assert loaded_artifact.path.endswith(
        "styles/nolan-warm/versions/v2/artifacts/captureone/NolanWarm.costyle"
    )
    assert (tmp_path / "data" / loaded_artifact.path).exists()


def test_missing_entries_return_none(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")

    assert store.get_style("missing") is None
    assert store.get_version("missing", "v1") is None
    assert store.get_artifact("missing") is None


def test_list_styles_returns_stored_styles(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    first = store.create_style(Style(name="First Style", slug="first-style"))
    second = store.create_style(Style(name="Second Style", slug="second-style"))

    styles = store.list_styles()
    style_ids = {style.style_id for style in styles}

    assert first.style_id in style_ids
    assert second.style_id in style_ids


def test_list_artifacts_can_filter_by_style(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")

    style_a = store.create_style(Style(name="Style A", slug="style-a"))
    style_b = store.create_style(Style(name="Style B", slug="style-b"))
    version_a = _build_style_version(style_a.style_id, version="v1")
    version_b = _build_style_version(style_b.style_id, version="v1")
    store.create_version(style_a.style_id, version_a)
    store.create_version(style_b.style_id, version_b)

    store.save_artifact(
        style_id=style_a.style_id,
        version="v1",
        target="captureone",
        filename="a.costyle",
        content=b"a",
    )
    store.save_artifact(
        style_id=style_b.style_id,
        version="v1",
        target="captureone",
        filename="b.costyle",
        content=b"b",
    )

    artifacts_a = store.list_artifacts(style_id=style_a.style_id)
    artifacts_b = store.list_artifacts(style_id=style_b.style_id)

    assert len(artifacts_a) == 1
    assert len(artifacts_b) == 1
    assert artifacts_a[0].style_id == style_a.style_id
    assert artifacts_b[0].style_id == style_b.style_id


def test_create_and_list_ai_generations(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    first = store.create_ai_generation(
        AIGenerationRecord(
            client_key="client-a",
            prompt="warm cinematic preset",
            target="captureone",
            style_spec=StyleSpec(
                name="AI Warm",
                intent=["warm"],
                captureone={"keys": {"Contrast": 8}},
            ),
            provider="mock",
            model="mock-v1",
        )
    )
    second = store.create_ai_generation(
        AIGenerationRecord(
            client_key="client-b",
            prompt="neutral editorial preset",
            target="captureone",
            style_spec=StyleSpec(
                name="AI Neutral",
                intent=["editorial"],
                captureone={"keys": {"Saturation": -2}},
            ),
            provider="mock",
            model="mock-v1",
        )
    )

    all_records = store.list_ai_generations()
    assert len(all_records) == 2
    assert all_records[0].generation_id == second.generation_id
    assert all_records[1].generation_id == first.generation_id

    limited_records = store.list_ai_generations(limit=1)
    assert len(limited_records) == 1
    assert limited_records[0].generation_id == second.generation_id
