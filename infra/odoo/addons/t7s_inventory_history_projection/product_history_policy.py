"""Pure validation and fail-closed mapping for the bounded product-history export.

The export lists confirmed purchase obligations (lines) of one company and product
whose Expected Arrival lies in a bounded window, with their completed receipts and
supplier returns. It computes no KPI: features and labels are derived outside Odoo.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LINES = 500
MAX_MOVES_PER_LINE = 8
MAX_WINDOW = timedelta(days=366)
SCHEMA_VERSION = "pdss.product_history.v1"

LINE_FIELDS = (
    "purchase_order_line_id",
    "purchase_order_id",
    "commercial_partner_id",
    "product_uom_id",
    "ordered_quantity",
    "expected_arrival_at",
    "order_confirmed_at",
    "receipts",
    "returned_quantity",
)
RECEIPT_FIELDS = (
    "stock_move_id",
    "stock_picking_id",
    "processed_at",
    "quantity",
    "backorder_of_picking_id",
)


class ProductHistoryPolicyError(ValueError):
    """The requested or observed history is outside the supported export subset."""


@dataclass(frozen=True, slots=True)
class ProductHistoryRequest:
    company_id: int
    product_id: int
    date_from: datetime
    date_to: datetime
    limit: int

    @property
    def date_from_string(self) -> str:
        return self.date_from.strftime(DATETIME_FORMAT)

    @property
    def date_to_string(self) -> str:
        return self.date_to.strftime(DATETIME_FORMAT)


def validate_product_request(
    *, company_id: Any, product_id: Any, date_from: Any, date_to: Any, limit: Any, now: datetime
) -> ProductHistoryRequest:
    """Validate every caller-controlled bound before privileged ORM access."""

    normalized_limit = _positive_integer(limit, "limit")
    if normalized_limit > MAX_LINES:
        raise ProductHistoryPolicyError(f"limit must not exceed {MAX_LINES}")
    normalized_from = _datetime(date_from, "date_from")
    normalized_to = _datetime(date_to, "date_to")
    if normalized_from >= normalized_to:
        raise ProductHistoryPolicyError("date_from must be earlier than date_to")
    if normalized_to - normalized_from > MAX_WINDOW:
        raise ProductHistoryPolicyError("the requested history window must not exceed 366 days")
    if normalized_to > now.replace(microsecond=0):
        raise ProductHistoryPolicyError("date_to must not be in the future")
    return ProductHistoryRequest(
        company_id=_positive_integer(company_id, "company_id"),
        product_id=_positive_integer(product_id, "product_id"),
        date_from=normalized_from,
        date_to=normalized_to,
        limit=normalized_limit,
    )


def build_product_history(
    request: ProductHistoryRequest,
    *,
    lines: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    partners: list[dict[str, Any]],
    moves: list[dict[str, Any]],
    pickings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate joined evidence and emit only the fixed sanitized line schema."""

    if len(lines) > request.limit:
        raise ProductHistoryPolicyError("the bounded result exceeds the requested limit")
    line_by_id = _unique_by_id(lines, "purchase order line")
    order_by_id = _unique_by_id(orders, "purchase order")
    partner_by_id = _unique_by_id(partners, "supplier")
    picking_by_id = _unique_by_id(pickings, "stock picking")
    receipts: dict[int, list[dict[str, Any]]] = {line_id: [] for line_id in line_by_id}
    returned: dict[int, Decimal] = dict.fromkeys(line_by_id, Decimal(0))

    for line in line_by_id.values():
        _require_company(line, request.company_id, "purchase order line")
        if line.get("product_id") != request.product_id:
            raise ProductHistoryPolicyError("purchase order line has another product")
        if line.get("qty_received_method") != "stock_moves":
            raise ProductHistoryPolicyError("purchase order line is not stock-move-backed")
        expected = _datetime(line.get("expected_arrival_at"), "expected_arrival_at")
        if not request.date_from <= expected < request.date_to:
            raise ProductHistoryPolicyError("purchase order line leaves the requested window")
        _positive_decimal(line.get("ordered_quantity"), "ordered_quantity")
        order = order_by_id.get(line.get("purchase_order_id"))
        if order is None:
            raise ProductHistoryPolicyError("purchase order relationship is incomplete")
        _require_company(order, request.company_id, "purchase order")
        if order.get("state") not in {"purchase", "done"}:
            raise ProductHistoryPolicyError("purchase order state is unsupported")
        _datetime(order.get("confirmed_at"), "order_confirmed_at")
        if order.get("supplier_id") not in partner_by_id:
            raise ProductHistoryPolicyError("supplier relationship is incomplete")

    for move in _unique_by_id(moves, "stock move").values():
        _require_company(move, request.company_id, "stock move")
        line = line_by_id.get(move.get("purchase_order_line_id"))
        if line is None:
            raise ProductHistoryPolicyError("stock move purchase-line relationship is incomplete")
        if move.get("state") != "done":
            raise ProductHistoryPolicyError("stock move state is unsupported")
        if (
            move.get("product_id") != line["product_id"]
            or move.get("product_uom_id") != line["product_uom_id"]
        ):
            raise ProductHistoryPolicyError("stock move product or unit relationship is ambiguous")
        picking = picking_by_id.get(move.get("stock_picking_id"))
        if picking is None:
            raise ProductHistoryPolicyError("stock picking relationship is incomplete")
        _require_company(picking, request.company_id, "stock picking")
        if picking.get("state") != "done" or picking.get("processed_at") != move.get(
            "processed_at"
        ):
            raise ProductHistoryPolicyError("move and picking completion disagree")
        _datetime(move.get("processed_at"), "processed_at")
        quantity = _positive_decimal(move.get("quantity"), "quantity")
        direction = (move.get("source_location_usage"), move.get("destination_location_usage"))
        if direction == ("supplier", "internal") and not move.get("return_of_move_id"):
            if picking.get("picking_type_code") != "incoming":
                raise ProductHistoryPolicyError("receipt picking type is unsupported")
            receipts[line["id"]].append(
                {
                    "stock_move_id": move["id"],
                    "stock_picking_id": picking["id"],
                    "processed_at": move["processed_at"],
                    "quantity": format(quantity, "f"),
                    "backorder_of_picking_id": picking.get("backorder_of_picking_id") or None,
                }
            )
        elif direction == ("internal", "supplier") and move.get("return_of_move_id"):
            returned[line["id"]] += quantity
        else:
            raise ProductHistoryPolicyError("stock move direction is outside the supported subset")

    output = []
    for line in line_by_id.values():
        line_receipts = sorted(
            receipts[line["id"]], key=lambda r: (r["processed_at"], r["stock_move_id"])
        )
        if len(line_receipts) > MAX_MOVES_PER_LINE:
            raise ProductHistoryPolicyError("purchase order line has too many receipts")
        order = order_by_id[line["purchase_order_id"]]
        partner = partner_by_id[order["supplier_id"]]
        record = {
            "purchase_order_line_id": line["id"],
            "purchase_order_id": order["id"],
            "commercial_partner_id": _positive_integer(
                partner.get("commercial_partner_id"), "commercial_partner_id"
            ),
            "product_uom_id": _positive_integer(line.get("product_uom_id"), "product_uom_id"),
            "ordered_quantity": format(_positive_decimal(line["ordered_quantity"], "q"), "f"),
            "expected_arrival_at": line["expected_arrival_at"],
            "order_confirmed_at": order["confirmed_at"],
            "receipts": line_receipts,
            "returned_quantity": format(returned[line["id"]], "f"),
        }
        if tuple(record) != LINE_FIELDS:
            raise ProductHistoryPolicyError("export schema changed unexpectedly")
        output.append(record)
    return sorted(output, key=lambda r: (r["expected_arrival_at"], r["purchase_order_line_id"]))


def _unique_by_id(rows: list[dict[str, Any]], label: str) -> dict[int, dict[str, Any]]:
    output: dict[int, dict[str, Any]] = {}
    for row in rows:
        record_id = _positive_integer(row.get("id"), f"{label} id")
        if record_id in output:
            raise ProductHistoryPolicyError(f"duplicate {label} identity")
        output[record_id] = row
    return output


def _require_company(row: dict[str, Any], company_id: int, label: str) -> None:
    if row.get("company_id") != company_id:
        raise ProductHistoryPolicyError(f"{label} crosses the authorized company boundary")


def _datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ProductHistoryPolicyError(f"{label} must use {DATETIME_FORMAT}")
    try:
        parsed = datetime.strptime(value, DATETIME_FORMAT)
    except ValueError as error:
        raise ProductHistoryPolicyError(f"{label} must use {DATETIME_FORMAT}") from error
    if parsed.strftime(DATETIME_FORMAT) != value:
        raise ProductHistoryPolicyError(f"{label} must use {DATETIME_FORMAT}")
    return parsed


def _positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ProductHistoryPolicyError(f"{label} must be a positive integer")
    return value


def _positive_decimal(value: Any, label: str) -> Decimal:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ProductHistoryPolicyError(f"{label} must be numeric") from error
    if not decimal_value.is_finite() or decimal_value <= 0:
        raise ProductHistoryPolicyError(f"{label} must be greater than zero")
    return decimal_value
