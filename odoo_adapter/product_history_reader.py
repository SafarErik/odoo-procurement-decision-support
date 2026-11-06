"""Read the bounded product purchase-history export through Odoo JSON-2."""

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from application.errors import ProcurementDataResponseError, ProcurementDataUnavailable
from application.purchase_history import (
    PurchaseHistoryQuery,
    PurchaseHistorySnapshot,
    PurchaseLineHistory,
    ReceiptEvent,
)
from odoo_adapter.json2_client import (
    Json2Reader,
    format_odoo_datetime,
    odoo_errors,
    parse_canonical_datetime,
    prefixed_id,
    required_int,
)
from supplier_evaluation.contracts import HISTORY_SOURCE

MODEL = "procurement.product.history.export"
METHOD = "read_product_history"
SCHEMA_VERSION = "pdss.product_history.v1"
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


class OdooProductHistoryReader(Json2Reader):
    """Adapter exposing only the approved export method as a neutral port."""

    def __init__(self, *, timeout_seconds: float = 15.0, **settings) -> None:
        super().__init__(timeout_seconds=timeout_seconds, **settings)

    async def read_purchase_history(self, query: PurchaseHistoryQuery) -> PurchaseHistorySnapshot:
        if not self._configured:
            raise ProcurementDataUnavailable("Odoo purchase history is not configured")
        with odoo_errors(
            "Odoo purchase history", "Odoo purchase history returned an invalid response"
        ):
            payload = {
                "company_id": prefixed_id(query.company_id, "odoo:res.company:"),
                "product_id": prefixed_id(query.product_id, "odoo:product.product:"),
                "date_from": format_odoo_datetime(query.window_start),
                "date_to": format_odoo_datetime(query.window_end),
                "limit": query.limit,
            }
            async with self._client() as client:
                response = await client.post(
                    f"{self._base_url}/json/2/{MODEL}/{METHOD}", json=payload
                )
                response.raise_for_status()
                result = response.json()
            lines = _map_response(result, query, payload)
        reference = (
            f"{MODEL}.{METHOD}|database={self._database}|company={query.company_id}"
            f"|product={query.product_id}|window=[{query.window_start.isoformat()},"
            f"{query.window_end.isoformat()})"
        )
        try:
            return PurchaseHistorySnapshot(
                query, lines, datetime.now(UTC).replace(microsecond=0), HISTORY_SOURCE, reference
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
                f"odoo:stock.move:{required_int(receipt, 'stock_move_id')}",
                parse_canonical_datetime(receipt["processed_at"]),
                Decimal(str(receipt["quantity"])),
                None
                if backorder is None
                else f"odoo:stock.picking:{required_int(receipt, 'backorder_of_picking_id')}",
            )
        )
    return PurchaseLineHistory(
        f"odoo:purchase.order.line:{required_int(line, 'purchase_order_line_id')}",
        f"odoo:purchase.order:{required_int(line, 'purchase_order_id')}",
        query.company_id,
        f"odoo:res.partner:{required_int(line, 'commercial_partner_id')}",
        query.product_id,
        f"odoo:uom.uom:{required_int(line, 'product_uom_id')}",
        Decimal(str(line["ordered_quantity"])),
        parse_canonical_datetime(line["expected_arrival_at"]),
        parse_canonical_datetime(line["order_confirmed_at"]),
        tuple(receipts),
        Decimal(str(line["returned_quantity"])),
    )
