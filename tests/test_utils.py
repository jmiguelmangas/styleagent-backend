from app.core.utils import generate_id, slugify


def test_slugify_normalizes_spaces_and_symbols() -> None:
    assert slugify("Nolan 04 Warm v1") == "nolan-04-warm-v1"
    assert slugify("  Neon__Blue!!! ") == "neon-blue"


def test_slugify_transliterates_unicode() -> None:
    assert slugify("Árbol cálido") == "arbol-calido"


def test_generate_id_returns_uuid_string() -> None:
    first = generate_id()
    second = generate_id()

    assert first != second
    assert len(first) == 36
    assert len(second) == 36
