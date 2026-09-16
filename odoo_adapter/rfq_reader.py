"""Read-only Odoo JSON-2 adapter for open RFQs."""

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from application.rfqs import (
    Money,
    ProcurementDataResponseError,
    ProcurementDataUnavailable,
    RfqStatus,
    RfqSummary,
)

_OPEN_STATES = ("draft", "sent", "to approve")
_STATE_MAP: dict[str, RfqStatus] = {
    "draft": "draft",
    "sent": "sent",
    "to approve": "awaiting_approval",
}
_FIELDS = (
    "id",
    "name",
    "partner_id",
    "date_order",
    "state",
    "amount_total",
    "currency_id",
)


class OdooRfqReader:
    """Retrieve and map open RFQs through Odoo's external JSON-2 API."""

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

    async def list_open_rfqs(self, limit: int) -> list[RfqSummary]:
        """Return recent open RFQs without exposing Odoo payloads upstream."""

        if not self._base_url or not self._database or not self._api_key:
            raise ProcurementDataUnavailable("Odoo integration is not configured")

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                transport=self._transport,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "X-Odoo-Database": self._database,
                    "User-Agent": "odoo-procurement-decision-support/0.0.1",
                },
            ) as client:
                response = await client.post(
                    f"{self._base_url}/json/2/purchase.order/search_read",
                    json={
                        "domain": [["state", "in", list(_OPEN_STATES)]],
                        "fields": list(_FIELDS),
                        "limit": limit,
                        "order": "date_order desc, id desc",
                    },
                )
                response.raise_for_status()
        except httpx.RequestError as error:
            raise ProcurementDataUnavailable("Odoo could not be reached") from error
        except httpx.HTTPStatusError as error:
            raise ProcurementDataResponseError(
                f"Odoo returned HTTP {error.response.status_code}"
            ) from error

        try:
            payload = response.json()
            if not isinstance(payload, list):
                raise TypeError("Expected an RFQ list")
            return [_map_record(record) for record in payload]
        except (KeyError, TypeError, ValueError, InvalidOperation) as error:
            raise ProcurementDataResponseError("Odoo returned an invalid RFQ payload") from error


def _map_record(record: Any) -> RfqSummary:
    """Map one validated Odoo record to the application contract."""

    if not isinstance(record, Mapping):
        raise TypeError("Expected an RFQ object")

    raw_state = _required_string(record, "state")
    return RfqSummary(
        source_id=str(record["id"]),
        reference=_required_string(record, "name"),
        vendor_name=_many2one_name(record["partner_id"], "partner_id"),
        order_date=_parse_odoo_datetime(_required_string(record, "date_order")),
        status=_STATE_MAP.get(raw_state, "unknown"),
        total=Money(
            amount=Decimal(str(record["amount_total"])),
            currency=_many2one_name(record["currency_id"], "currency_id"),
        ),
    )


def _required_string(record: Mapping[str, Any], field: str) -> str:
    value = record[field]
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"Expected a non-empty string for {field}")
    return value


def _many2one_name(value: Any, field: str) -> str:
    if (
        not isinstance(value, (list, tuple))
        or len(value) < 2
        or not isinstance(value[1], str)
        or not value[1].strip()
    ):
        raise TypeError(f"Expected a many2one display value for {field}")
    return value[1]


def _parse_odoo_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace(" ", "T").replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
