"""Backend RFQ client and presentation mapping for the Reflex frontend."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)
_STATUS_LABELS = {
    "draft": "Draft",
    "sent": "Sent",
    "awaiting_approval": "Awaiting approval",
    "unknown": "Unknown",
}


@dataclass(frozen=True, slots=True)
class RfqDisplay:
    """One frontend-ready RFQ ledger row."""

    source_id: str
    reference: str
    vendor_name: str
    order_date: str
    status: str
    status_label: str
    total: str


@dataclass(frozen=True, slots=True)
class RfqDashboardResult:
    """Complete result needed to update the dashboard state once."""

    items: tuple[RfqDisplay, ...]
    connected: bool
    last_refreshed: str
    error_message: str


async def fetch_rfq_dashboard(
    rfqs_url: str,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> RfqDashboardResult:
    """Fetch and validate the backend's ERP-neutral RFQ response."""

    try:
        async with httpx.AsyncClient(timeout=7.0, transport=transport) as client:
            response = await client.get(rfqs_url, params={"limit": 20})
            response.raise_for_status()
        payload = response.json()
        items = payload["items"]
        if not isinstance(items, list):
            raise TypeError("Expected an RFQ list")
        retrieved_at = _parse_datetime(payload["retrieved_at"])
        return RfqDashboardResult(
            items=tuple(_map_rfq(item) for item in items),
            connected=True,
            last_refreshed=f"{retrieved_at.hour:02d}:{retrieved_at.minute:02d} UTC",
            error_message="",
        )
    except (httpx.HTTPError, KeyError, TypeError, ValueError, InvalidOperation):
        return RfqDashboardResult(
            items=(),
            connected=False,
            last_refreshed="Not available",
            error_message=(
                "Odoo data is unavailable. Check that Odoo is running and the "
                "integration key is valid."
            ),
        )


def _map_rfq(value: Any) -> RfqDisplay:
    if not isinstance(value, dict):
        raise TypeError("Expected an RFQ object")

    status = _required_string(value, "status")
    total = value["total"]
    if not isinstance(total, dict):
        raise TypeError("Expected an RFQ total")
    amount = Decimal(_required_string(total, "amount"))
    currency = _required_string(total, "currency")
    order_date = _parse_datetime(_required_string(value, "order_date"))

    return RfqDisplay(
        source_id=_required_string(value, "source_id"),
        reference=_required_string(value, "reference"),
        vendor_name=_required_string(value, "vendor_name"),
        order_date=f"{order_date.day:02d} {_MONTHS[order_date.month - 1]} {order_date.year}",
        status=status,
        status_label=_STATUS_LABELS.get(status, "Unknown"),
        total=f"{amount:,.2f} {currency}",
    )


def _required_string(value: dict[str, Any], field: str) -> str:
    item = value[field]
    if not isinstance(item, str) or not item.strip():
        raise TypeError(f"Expected a non-empty string for {field}")
    return item


def _parse_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise TypeError("Expected an ISO datetime")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
