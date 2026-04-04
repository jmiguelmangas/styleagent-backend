import hashlib
from pathlib import Path

import pytest

from app.core.models import SafePolicy, Style, StyleSpec, StyleVersion
from app.core.services import compile_style_version
from app.core.services.errors import CompileConfigurationError, CompileValidationError
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


def test_compile_style_version_includes_richer_captureone_keys(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    style = store.create_style(Style(name="Editorial Rich", slug="editorial-rich"))
    spec = StyleSpec(
        name="Editorial Rich",
        intent=["cinematic", "portrait"],
        captureone={
            "keys": {
                "Exposure": 0.15,
                "Contrast": 14,
                "Saturation": 5,
                "Clarity": 10,
                "Highlights": -12,
                "Shadows": 14,
                "WhiteBalanceTemperature": 5900,
                "WhiteBalanceTint": 3,
                "ColorBalanceRed": 7,
                "ColorBalanceGreen": 1,
                "ColorBalanceBlue": -2,
                "ToneCurve": "Film Standard",
            }
        },
    )
    version = StyleVersion(
        style_id=style.style_id,
        version="v1",
        style_spec=spec,
        safe_policy=SafePolicy(remove_white_balance=False),
    )
    store.create_version(style.style_id, version)

    artifact = compile_style_version(store=store, style_id=style.style_id, version="v1")
    _, content = store.get_artifact(artifact.artifact_id)
    text = content.decode("utf-8")

    assert '<E K="Saturation" V="5"/>' in text
    assert '<E K="Clarity" V="10"/>' in text
    assert '<E K="Highlights" V="-12"/>' in text
    assert '<E K="WhiteBalanceTemperature" V="5900"/>' in text
    assert '<E K="ColorBalanceRed" V="7"/>' in text
    assert '<E K="ToneCurve" V="Film Standard"/>' in text


def test_compile_style_version_raises_lookup_for_missing_style(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")

    with pytest.raises(LookupError, match="style not found: missing-style"):
        compile_style_version(store=store, style_id="missing-style", version="v1")


def test_compile_style_version_raises_lookup_for_missing_version(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    style = store.create_style(Style(name="Nolan Warm", slug="nolan-warm"))

    with pytest.raises(LookupError, match="version not found: missing"):
        compile_style_version(store=store, style_id=style.style_id, version="missing")


def test_compile_style_version_rejects_unsupported_target(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    style, _ = _create_style_with_version(store)

    with pytest.raises(CompileValidationError, match="unsupported target: lightroom"):
        compile_style_version(store=store, style_id=style.style_id, version="v1", target="lightroom")  # type: ignore[arg-type]


def test_compile_style_version_raises_configuration_error_for_missing_template(tmp_path) -> None:
    store = FSStore(base_dir=tmp_path / "data")
    style, _ = _create_style_with_version(store)

    with pytest.raises(CompileConfigurationError, match="template not found:"):
        compile_style_version(
            store=store,
            style_id=style.style_id,
            version="v1",
            template_path=Path(tmp_path / "missing-template.costyle"),
        )
