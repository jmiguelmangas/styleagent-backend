import hashlib

from app.core.models import SafePolicySpec, Style, StyleSpec, StyleVersion
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
        safe_policy=SafePolicySpec(),
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
