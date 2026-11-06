"""Shared JSON-2 plumbing for the Odoo readers: client, error mapping and value parsing.

Private to ``odoo_adapter``. Readers stay responsible for which models and read methods
they call; this module never chooses a method.
"""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import InvalidOperation
from typing import Any

import httpx

from application.errors import ProcurementDataResponseError, ProcurementDataUnavailable

USER_AGENT = "odoo-procurement-decision-support/0.0.1"
# Odoo's server-side datetime text (UTC, no zone suffix).
ODOO_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Json2Reader:
    """Connection settings and an authenticated client for one Odoo database."""

    def __init__(
        self,
        *,
        base_url: str,
        database: str,
        api_key: str,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._database = database
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    @property
    def _configured(self) -> bool:
        return bool(self._base_url and self._database and self._api_key)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=self._timeout_seconds,
            transport=self._transport,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "X-Odoo-Database": self._database,
                "User-Agent": USER_AGENT,
            },
        )

    async def _post(
        self, client: httpx.AsyncClient, model: str, method: str, payload: dict[str, Any]
    ) -> Any:
        response = await client.post(f"{self._base_url}/json/2/{model}/{method}", json=payload)
        response.raise_for_status()
        return response.json()


@contextmanager
def odoo_errors(source: str, invalid: str) -> Iterator[None]:
    """Map transport and payload failures to the application's procurement-data errors.

    Unreachable Odoo raises ProcurementDataUnavailable (the API answers 503); an HTTP error
    status or a payload that does not parse raises ProcurementDataResponseError (502).
    """
    try:
        yield
    except httpx.RequestError as error:
        raise ProcurementDataUnavailable(f"{source} could not be reached") from error
    except httpx.HTTPStatusError as error:
        raise ProcurementDataResponseError(
            f"{source} returned HTTP {error.response.status_code}"
        ) from error
    except (KeyError, TypeError, ValueError, InvalidOperation) as error:
        raise ProcurementDataResponseError(invalid) from error


def format_odoo_datetime(value: datetime) -> str:
    return value.astimezone(UTC).replace(tzinfo=None).strftime(ODOO_DATETIME_FORMAT)


def parse_canonical_datetime(value: Any) -> datetime:
    """Strict: only the exact server format, as the bounded history export writes it."""
    if not isinstance(value, str):
        raise TypeError("Export datetime must be a string")
    parsed = datetime.strptime(value, ODOO_DATETIME_FORMAT)
    if parsed.strftime(ODOO_DATETIME_FORMAT) != value:
        raise ValueError("Export datetime is not canonical")
    return parsed.replace(tzinfo=UTC)


def parse_odoo_datetime(value: str) -> datetime:
    """Lenient: the server format or ISO 8601; a value without zone is UTC."""
    parsed = datetime.fromisoformat(value.replace(" ", "T").replace("Z", "+00:00"))
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).astimezone(UTC)


def prefixed_id(value: str, prefix: str) -> int:
    """The Odoo record id inside an ``odoo:<model>:<id>`` identity."""
    suffix = value.removeprefix(prefix) if value.startswith(prefix) else ""
    if not suffix.isdigit() or str(int(suffix)) != suffix or int(suffix) <= 0:
        raise ValueError("Identity has an unsupported source prefix")
    return int(suffix)


def required_int(record: Any, field: str) -> int:
    if not isinstance(record, Mapping):
        raise TypeError("Expected an Odoo record object")
    value = record[field]
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TypeError(f"Expected a positive integer for {field}")
    return value


def required_string(record: Any, field: str) -> str:
    if not isinstance(record, Mapping):
        raise TypeError("Expected an Odoo record object")
    value = record[field]
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"Expected a non-empty string for {field}")
    return value
