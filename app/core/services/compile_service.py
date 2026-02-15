from __future__ import annotations

from pathlib import Path
from typing import Literal

from app.core.captureone import apply_safe_policy, parse_costyle, write_costyle
from app.core.captureone.costyle_parser import CostyleDocument, Entry
from app.core.models import Artifact
from app.storage.base import Store

_TARGET = "captureone"
_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "captureone" / "templates" / "base.costyle"


def compile_style_version(
    store: Store,
    style_id: str,
    version: str,
    target: Literal["captureone"] = "captureone",
    template_path: Path | None = None,
) -> Artifact:
    if target != _TARGET:
        raise ValueError(f"unsupported target: {target}")

    style = store.get_style(style_id)
    if style is None:
        raise ValueError(f"style not found: {style_id}")

    style_version = store.get_version(style_id, version)
    if style_version is None:
        raise ValueError(f"version not found: {version}")

    template_content = _load_template(template_path)
    template_document = parse_costyle(template_content)

    patched = _patch_entries(template_document, style_version.style_spec.captureone.keys)
    filtered_entries = apply_safe_policy(patched.entries, policy=style_version.safe_policy)
    compiled = _drop_removed_entry_lines(patched, filtered_entries)

    rendered = write_costyle(compiled)
    filename = _artifact_filename(style.name)

    return store.save_artifact(
        style_id=style_id,
        version=version,
        target=target,
        filename=filename,
        content=rendered.encode("utf-8"),
    )


def _load_template(template_path: Path | None) -> str:
    path = template_path or _TEMPLATE_PATH
    if not path.exists():
        raise ValueError(f"template not found: {path}")
    return path.read_text(encoding="utf-8")


def _patch_entries(
    document: CostyleDocument, keys: dict[str, str | int | float]
) -> CostyleDocument:
    lines = list(document.lines)
    patched_keys: set[str] = set()

    existing_entries: list[Entry] = []
    for entry in document.entries:
        if entry.key in keys:
            existing_entries.append(
                Entry(
                    key=entry.key,
                    value=str(keys[entry.key]),
                    line_index=entry.line_index,
                    prefix=entry.prefix,
                    suffix=entry.suffix,
                )
            )
            patched_keys.add(entry.key)
        else:
            existing_entries.append(entry)

    missing_keys = sorted(set(keys.keys()) - patched_keys)
    if not missing_keys:
        return CostyleDocument(lines=lines, entries=existing_entries)

    insert_index = _closing_tag_index(lines)
    inserted_entries: list[Entry] = []
    for offset, key in enumerate(missing_keys):
        line_index = insert_index + offset
        lines.insert(line_index, f'  <E K="{key}" V="{keys[key]}"/>')
        inserted_entries.append(
            Entry(
                key=key,
                value=str(keys[key]),
                line_index=line_index,
                prefix="  ",
            )
        )

    delta = len(inserted_entries)
    adjusted_existing = [
        Entry(
            key=entry.key,
            value=entry.value,
            line_index=(
                entry.line_index + delta
                if entry.line_index >= insert_index
                else entry.line_index
            ),
            prefix=entry.prefix,
            suffix=entry.suffix,
        )
        for entry in existing_entries
    ]

    entries = sorted(adjusted_existing + inserted_entries, key=lambda item: item.line_index)
    return CostyleDocument(lines=lines, entries=entries)


def _drop_removed_entry_lines(
    document: CostyleDocument, kept_entries: list[Entry]
) -> CostyleDocument:
    original_entry_indices = {entry.line_index for entry in document.entries}
    kept_indices = {entry.line_index for entry in kept_entries}

    index_map: dict[int, int] = {}
    filtered_lines: list[str] = []
    for original_index, line in enumerate(document.lines):
        if original_index in original_entry_indices and original_index not in kept_indices:
            continue

        index_map[original_index] = len(filtered_lines)
        filtered_lines.append(line)

    remapped_entries = [
        Entry(
            key=entry.key,
            value=entry.value,
            line_index=index_map[entry.line_index],
            prefix=entry.prefix,
            suffix=entry.suffix,
        )
        for entry in kept_entries
    ]

    return CostyleDocument(lines=filtered_lines, entries=remapped_entries)


def _closing_tag_index(lines: list[str]) -> int:
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip() == "</SL>":
            return index
    return len(lines)


def _artifact_filename(style_name: str) -> str:
    normalized = style_name.strip().replace(" ", "_")
    if not normalized:
        normalized = "style"
    return f"{normalized}.costyle"
