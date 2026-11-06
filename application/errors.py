"""Stable application error contracts shared by use cases and adapters."""


class RepositoryError(RuntimeError):
    """Stable failure contract implemented by persistence and runtime adapters."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ProcurementDataUnavailable(RuntimeError):
    """The procurement source is not configured or cannot be reached."""


class ProcurementDataResponseError(RuntimeError):
    """The procurement source rejected a request or returned invalid data."""
