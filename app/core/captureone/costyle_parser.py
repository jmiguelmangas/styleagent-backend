from __future__ import annotations

import re
from dataclasses import dataclass

_ENTRY_LINE_RE = re.compile(
    r'^(?P<prefix>\s*)<E\s+K="(?P<key>[^"]+)"\s+V="(?P<value>[^"]*)"\s*/>(?P<suffix>\s*)$'
)


@dataclass(frozen=True)
class Entry:
    key: str
    value: str
    line_index: int
    prefix: str = ""
    suffix: str = ""


@dataclass(frozen=True)
class CostyleDocument:
    lines: list[str]
    entries: list[Entry]


def parse_costyle(content: str) -> CostyleDocument:
    """Parse .costyle content, extracting ordered E entries while preserving all lines."""
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    entries: list[Entry] = []
    for index, line in enumerate(lines):
        match = _ENTRY_LINE_RE.match(line)
        if match is None:
            continue

        entries.append(
            Entry(
                key=match.group("key"),
                value=match.group("value"),
                line_index=index,
                prefix=match.group("prefix"),
                suffix=match.group("suffix"),
            )
        )

    return CostyleDocument(lines=lines, entries=entries)
