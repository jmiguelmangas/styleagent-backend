class CompileValidationError(ValueError):
    """Raised when compile input is invalid for the requested operation."""


class CompileConfigurationError(RuntimeError):
    """Raised when compile cannot run because server-side configuration is broken."""

