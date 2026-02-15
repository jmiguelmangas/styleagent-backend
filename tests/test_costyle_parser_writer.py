from pathlib import Path

from app.core.captureone import parse_costyle, write_costyle


FIXTURE = Path(__file__).parent / "fixtures" / "sample.costyle"


def test_parse_costyle_extracts_entries_in_order() -> None:
    content = FIXTURE.read_text(encoding="utf-8")

    document = parse_costyle(content)

    assert [entry.key for entry in document.entries] == ["Exposure", "Contrast", "Saturation"]
    assert [entry.value for entry in document.entries] == ["0.35", "12", "4"]


def test_write_costyle_preserves_unknown_tags_and_normalizes_newline() -> None:
    content = FIXTURE.read_text(encoding="utf-8").replace("\n", "\r\n")

    document = parse_costyle(content)
    rendered = write_costyle(document)

    assert '<UnknownTag attr="kept" />' in rendered
    assert "\r\n" not in rendered
    assert rendered.endswith("\n")


def test_parse_write_roundtrip_is_deterministic() -> None:
    content = FIXTURE.read_text(encoding="utf-8")

    first_doc = parse_costyle(content)
    first_render = write_costyle(first_doc)

    second_doc = parse_costyle(first_render)
    second_render = write_costyle(second_doc)

    assert first_render == second_render
