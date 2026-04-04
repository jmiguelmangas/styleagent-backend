class ConflictError(ValueError):
    """Raised when a storage write violates a uniqueness/business constraint."""

