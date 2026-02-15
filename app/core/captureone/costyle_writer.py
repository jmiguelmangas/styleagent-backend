from __future__ import annotations

from app.core.captureone.costyle_parser import CostyleDocument


def write_costyle(document: CostyleDocument) -> str:
    """Write a deterministic .costyle output preserving template order and non-entry lines."""
    lines = list(document.lines)
    for entry in document.entries:
        lines[entry.line_index] = f'{entry.prefix}<E K="{entry.key}" V="{entry.value}"/>{entry.suffix}'

    rendered = "\n".join(lines)
    if not rendered.endswith("\n"):
        rendered += "\n"
    return rendered
