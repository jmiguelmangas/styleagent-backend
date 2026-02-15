import hashlib

from app.core.models import SafePolicy, Style, StyleSpec, StyleVersion
from app.core.services import compile_style_version
from app.storage.fs_store import FSStore


def _create_style_with_version(store: FSStore) -> tuple[Style, StyleVersion]:
    style = store.create_style(Style(name="Nolan Warm", slug="nolan-warm"))
    spec = StyleSpec(
        name="Nolan Warm",
        intent=["cinematic"],
        captureone={
            "keys": {
                "Exposure": 0.35,
                "Contrast": 12,
                "WhiteBalance": "AsShot",
            }
        },
    )
    version = StyleVersion(
        style_id=style.style_id,
        version="v1",
        style_spec=spec,
        safe_policy=SafePolicy(),
    )
    store.create_version(style.style_id, version)
    return style, version


def test_compile_style_version_persists_artifact(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    style, _ = _create_style_with_version(store)

    artifact = compile_style_version(store=store, style_id=style.style_id, version="v1")
    stored = store.get_artifact(artifact.artifact_id)

    assert stored is not None
    artifact_meta, content = stored
    assert artifact_meta.sha256 == hashlib.sha256(content).hexdigest()
    text = content.decode("utf-8")
    assert '<E K="Exposure" V="0.35"/>' in text
    assert '<E K="Contrast" V="12"/>' in text
    assert "WhiteBalance" not in text


def test_compile_style_version_is_deterministic_for_same_inputs(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    style, _ = _create_style_with_version(store)

    first = compile_style_version(store=store, style_id=style.style_id, version="v1")
    second = compile_style_version(store=store, style_id=style.style_id, version="v1")

    assert first.sha256 == second.sha256
