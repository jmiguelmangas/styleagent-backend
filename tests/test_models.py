import pytest
from pydantic import ValidationError

from app.core.models import Artifact, StyleCreate, StyleSpec


def test_style_create_autogenerates_slug() -> None:
    created = StyleCreate(name="Cinematic Warm V1")

    assert created.slug == "cinematic-warm-v1"


def test_style_spec_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        StyleSpec(
            name="   ",
            intent=["cinematic"],
            captureone={"keys": {"Exposure": 0.25}},
        )


def test_style_spec_rejects_empty_captureone_keys() -> None:
    with pytest.raises(ValidationError):
        StyleSpec(
            name="Warm",
            intent=["cinematic"],
            captureone={"keys": {}},
        )


def test_artifact_rejects_invalid_target() -> None:
    with pytest.raises(ValidationError):
        Artifact(
            style_id="style-1",
            version="v1",
            target="lightroom",
            path="data/styles/s1/v1/artifacts/lr/file.xmp",
            sha256="a" * 64,
        )
