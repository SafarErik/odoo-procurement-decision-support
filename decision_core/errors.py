"""Domain-specific errors raised by the Decision Core."""


class DomainValidationError(ValueError):
    """Raised when canonical decision input violates a domain invariant."""
