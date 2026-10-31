"""Read the bounded product purchase-history export through Odoo JSON-2."""

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from application.purchase_history import (
    PurchaseHistoryQuery,
    PurchaseHistorySnapshot,
    PurchaseLineHistory,
    ReceiptEvent,
)
from application.rfqs import ProcurementDataResponseError, ProcurementDataUnavailable

MODEL = "procurement.product.history.export"
METHOD = "read_product_history"
SCHEMA_VERSION = "pdss.product_history.v1"
SOURCE_TYPE = "odoo_purchase_history"
_ENVELOPE = {"schema_version", "company_id", "product_id", "date_from", "date_to"}
_ENVELOPE |= {"result_count", "lines"}
_LINE = {
    "purchase_order_line_id",
    "purchase_order_id",
    "commercial_partner_id",
    "product_uom_id",
    "ordered_quantity",
    "expected_arrival_at",
    "order_confirmed_at",
    "receipts",
    "returned_quantity",
}
_RECEIPT = {"stock_move_id", "stock_picking_id", "processed_at", "quantity"}
_RECEIPT |= {"backorder_of_picking_id"}
_FORMAT = "%Y-%m-%d %H:%M:%S"


class OdooProductHistoryReader:
    """Adapter exposing only the approved export method as a neutral port."""

    def __init__(
        self,
        *,
        base_url: str,
        database: str,
        api_key: str,
        timeout_seconds: float = 15.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._database = database
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def read_purchase_history(self, query: PurchaseHistoryQuery) -> PurchaseHistorySnapshot:
        if not self._base_url or not self._database or not self._api_key:
            raise ProcurementDataUnavailable("Odoo purchase history is not configured")
        try:
            payload = {
                "company_id": _prefixed_id(query.company_id, "odoo:res.company:"),
                "product_id": _prefixed_id(query.product_id, "odoo:product.product:"),
                "date_from": _odoo_datetime(query.window_start),
                "date_to": _odoo_datetime(query.window_end),
                "limit": query.limit,
            }
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
                    f"{self._base_url}/json/2/{MODEL}/{METHOD}", json=payload
                )
                response.raise_for_status()
                result = response.json()
            lines = _map_response(result, query, payload)
        except httpx.RequestError as error:
            raise ProcurementDataUnavailable(
                "Odoo purchase history could not be reached"
            ) from error
        except httpx.HTTPStatusError as error:
            raise ProcurementDataResponseError(
                f"Odoo purchase history returned HTTP {error.response.status_code}"
            ) from error
        except (KeyError, TypeError, ValueError, InvalidOperation) as error:
            raise ProcurementDataResponseError(
                "Odoo purchase history returned an invalid response"
            ) from error
        reference = (
            f"{MODEL}.{METHOD}|database={self._database}|company={query.company_id}"
            f"|product={query.product_id}|window=[{query.window_start.isoformat()},"
            f"{query.window_end.isoformat()})"
        )
        try:
            return PurchaseHistorySnapshot(
                query, lines, datetime.now(UTC).replace(microsecond=0), SOURCE_TYPE, reference
            )
        except ValueError as error:  # e.g. duplicate or out-of-window lines from Odoo
            raise ProcurementDataResponseError(
                "Odoo purchase history returned an invalid response"
            ) from error


def _map_response(result: Any, query: PurchaseHistoryQuery, payload: dict):
    if not isinstance(result, Mapping) or set(result) != _ENVELOPE:
        raise TypeError("Unexpected export envelope")
    if result["schema_version"] != SCHEMA_VERSION:
        raise TypeError("Unexpected export schema version")
    if any(result[k] != payload[k] for k in ("company_id", "product_id", "date_from", "date_to")):
        raise TypeError("Export does not echo the requested bounds")
    lines = result["lines"]
    if not isinstance(lines, list) or result["result_count"] != len(lines):
        raise TypeError("Export result count is inconsistent")
    if len(lines) >= query.limit:
        raise TypeError("Export may be truncated; narrow the window")
    return tuple(_map_line(line, query) for line in lines)


def _map_line(line: Any, query: PurchaseHistoryQuery) -> PurchaseLineHistory:
    if (
        not isinstance(line, Mapping)
        or set(line) != _LINE
        or not isinstance(line["receipts"], list)
    ):
        raise TypeError("Unexpected export line schema")
    receipts = []
    for receipt in line["receipts"]:
        if not isinstance(receipt, Mapping) or set(receipt) != _RECEIPT:
            raise TypeError("Unexpected export receipt schema")
        backorder = receipt["backorder_of_picking_id"]
        receipts.append(
            ReceiptEvent(
                f"odoo:stock.move:{_int(receipt['stock_move_id'])}",
                _parse(receipt["processed_at"]),
                Decimal(str(receipt["quantity"])),
                None if backorder is None else f"odoo:stock.picking:{_int(backorder)}",
            )
        )
    return PurchaseLineHistory(
        f"odoo:purchase.order.line:{_int(line['purchase_order_line_id'])}",
        f"odoo:purchase.order:{_int(line['purchase_order_id'])}",
        query.company_id,
        f"odoo:res.partner:{_int(line['commercial_partner_id'])}",
        query.product_id,
        f"odoo:uom.uom:{_int(line['product_uom_id'])}",
        Decimal(str(line["ordered_quantity"])),
        _parse(line["expected_arrival_at"]),
        _parse(line["order_confirmed_at"]),
        tuple(receipts),
        Decimal(str(line["returned_quantity"])),
    )


def _odoo_datetime(value: datetime) -> str:
    return value.astimezone(UTC).replace(tzinfo=None).strftime(_FORMAT)


def _parse(value: Any) -> datetime:
    if not isinstance(value, str):
        raise TypeError("Export datetime must be a string")
    parsed = datetime.strptime(value, _FORMAT)
    if parsed.strftime(_FORMAT) != value:
        raise ValueError("Export datetime is not canonical")
    return parsed.replace(tzinfo=UTC)


def _int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TypeError("Expected a positive integer identity")
    return value


def _prefixed_id(value: str, prefix: str) -> int:
    suffix = value.removeprefix(prefix) if value.startswith(prefix) else ""
    if not suffix.isdigit() or str(int(suffix)) != suffix or int(suffix) <= 0:
        raise ValueError("Identity has an unsupported source prefix")
    return int(suffix)
