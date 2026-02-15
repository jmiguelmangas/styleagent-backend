import re
import unicodedata

_slug_non_alnum_re = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Convert a style name into a deterministic URL-safe slug."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower().strip()
    slug = _slug_non_alnum_re.sub("-", lowered).strip("-")
    return slug
