"""Application error contracts shared by use cases, adapters and the HTTP layer."""


class CodedError(Exception):
    """An error with a stable machine-readable ``code`` that the HTTP layer maps to a status."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class PlanningCaseError(CodedError, ValueError):
    """The caller's planning request cannot be accepted (the HTTP layer answers 4xx/503)."""


class RepositoryError(CodedError, RuntimeError):
    """Storage or a runtime dependency (database, solver, renderer) is unavailable or invalid."""


class ProcurementDataUnavailable(RuntimeError):
    """The procurement source is not configured or cannot be reached."""


class ProcurementDataResponseError(RuntimeError):
    """The procurement source rejected a request or returned invalid data."""
