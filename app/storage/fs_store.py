from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from app.core.models import Artifact, Style, StyleVersion


class FSStore:
    def __init__(self, base_dir: str | Path = "data") -> None:
        self.base_dir = Path(base_dir)
        self.styles_dir = self.base_dir / "styles"
        self.index_dir = self.base_dir / "index"
        self.styles_index_path = self.index_dir / "styles.json"
        self.artifacts_index_path = self.index_dir / "artifacts.json"

    def create_style(self, style: Style) -> Style:
        self._ensure_layout()
        style_path = self._style_dir(style.slug)
        style_path.mkdir(parents=True, exist_ok=True)
        self._write_json(style_path / "style.json", style.model_dump(mode="json"))

        styles_index = self._read_json(self.styles_index_path)
        styles_index[style.style_id] = style.slug
        self._write_json(self.styles_index_path, styles_index)
        return style

    def get_style(self, style_id: str) -> Style | None:
        styles_index = self._read_json(self.styles_index_path)
        slug = styles_index.get(style_id)
        if slug is None:
            return None

        style_json_path = self._style_dir(slug) / "style.json"
        if not style_json_path.exists():
            return None

        return Style.model_validate(self._read_json(style_json_path))

    def list_styles(self) -> list[Style]:
        styles_index = self._read_json(self.styles_index_path)
        styles: list[Style] = []
        for style_id in sorted(styles_index.keys()):
            style = self.get_style(style_id)
            if style is not None:
                styles.append(style)
        return styles

    def create_version(self, style_id: str, version: StyleVersion) -> StyleVersion:
        style = self.get_style(style_id)
        if style is None:
            raise ValueError(f"style not found: {style_id}")

        version_dir = self._version_dir(style.slug, version.version)
        version_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(version_dir / "version.json", version.model_dump(mode="json"))
        self._write_json(version_dir / "spec.json", version.style_spec.model_dump(mode="json"))
        self._write_json(version_dir / "policy.json", version.safe_policy.model_dump(mode="json"))
        return version

    def get_version(self, style_id: str, version: str) -> StyleVersion | None:
        style = self.get_style(style_id)
        if style is None:
            return None

        version_json_path = self._version_dir(style.slug, version) / "version.json"
        if not version_json_path.exists():
            return None

        return StyleVersion.model_validate(self._read_json(version_json_path))

    def save_artifact(
        self,
        style_id: str,
        version: str,
        target: Literal["captureone"],
        filename: str,
        content: bytes,
    ) -> Artifact:
        style = self.get_style(style_id)
        if style is None:
            raise ValueError(f"style not found: {style_id}")

        if self.get_version(style_id, version) is None:
            raise ValueError(f"version not found: {version}")

        sha256 = hashlib.sha256(content).hexdigest()

        artifact_rel_path = (
            Path("styles")
            / style.slug
            / "versions"
            / version
            / "artifacts"
            / target
            / filename
        )
        artifact_abs_path = self.base_dir / artifact_rel_path
        artifact_abs_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_abs_path.write_bytes(content)

        artifact = Artifact(
            style_id=style_id,
            version=version,
            target=target,
            path=str(artifact_rel_path),
            sha256=sha256,
        )

        artifacts_index = self._read_json(self.artifacts_index_path)
        artifacts_index[artifact.artifact_id] = artifact.model_dump(mode="json")
        self._write_json(self.artifacts_index_path, artifacts_index)
        return artifact

    def get_artifact(self, artifact_id: str) -> tuple[Artifact, bytes] | None:
        artifacts_index = self._read_json(self.artifacts_index_path)
        raw_artifact = artifacts_index.get(artifact_id)
        if raw_artifact is None:
            return None

        artifact = Artifact.model_validate(raw_artifact)
        artifact_path = self.base_dir / artifact.path
        if not artifact_path.exists():
            return None

        return artifact, artifact_path.read_bytes()

    def list_artifacts(self, style_id: str | None = None) -> list[Artifact]:
        artifacts_index = self._read_json(self.artifacts_index_path)
        artifacts = [Artifact.model_validate(raw) for raw in artifacts_index.values()]
        if style_id is not None:
            artifacts = [artifact for artifact in artifacts if artifact.style_id == style_id]
        return sorted(artifacts, key=lambda artifact: artifact.created_at)

    def _style_dir(self, slug: str) -> Path:
        return self.styles_dir / slug

    def _version_dir(self, slug: str, version: str) -> Path:
        return self._style_dir(slug) / "versions" / version

    def _ensure_layout(self) -> None:
        self.styles_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        if not self.styles_index_path.exists():
            self._write_json(self.styles_index_path, {})
        if not self.artifacts_index_path.exists():
            self._write_json(self.artifacts_index_path, {})

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


_default_store = FSStore()


def create_style(style: Style) -> Style:
    return _default_store.create_style(style)


def get_style(style_id: str) -> Style | None:
    return _default_store.get_style(style_id)


def list_styles() -> list[Style]:
    return _default_store.list_styles()


def create_version(style_id: str, version: StyleVersion) -> StyleVersion:
    return _default_store.create_version(style_id, version)


def get_version(style_id: str, version: str) -> StyleVersion | None:
    return _default_store.get_version(style_id, version)


def save_artifact(
    style_id: str, version: str, target: Literal["captureone"], filename: str, content: bytes
) -> Artifact:
    return _default_store.save_artifact(style_id, version, target, filename, content)


def get_artifact(artifact_id: str) -> tuple[Artifact, bytes] | None:
    return _default_store.get_artifact(artifact_id)


def list_artifacts(style_id: str | None = None) -> list[Artifact]:
    return _default_store.list_artifacts(style_id=style_id)
