from uuid import uuid4


def generate_id() -> str:
    """Generate stable string identifiers for domain entities."""
    return str(uuid4())
