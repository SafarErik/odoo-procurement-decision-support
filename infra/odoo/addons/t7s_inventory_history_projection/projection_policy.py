"""Pure validation and fail-closed mapping for the T7-S Odoo projection."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LINE_IDS = 50
MAX_RESULTS = 200
MAX_WINDOW = timedelta(days=366)
SCHEMA_VERSION = "t7s.inventory_history.v1"

RECORD_FIELDS = (
    "company_id",
    "commercial_partner_id",
    "purchase_order_id",
    "purchase_order_line_id",
    "product_id",
    "product_uom_id",
    "expected_arrival_at",
    "stock_move_id",
    "stock_picking_id",
    "move_processed_at",
    "ordered_quantity",
    "completed_quantity",
    "state",
    "source_location_usage",
    "destination_location_usage",
    "backorder_of_picking_id",
    "return_of_move_id",
    "return_of_picking_id",
)


class ProjectionPolicyError(ValueError):
    """The requested or observed history is outside the supported T7-S subset."""


@dataclass(frozen=True, slots=True)
class ProjectionRequest:
    company_id: int
    date_from: datetime
    date_to: datetime
    purchase_order_line_ids: tuple[int, ...]
    limit: int

    @property
    def date_from_string(self) -> str:
        return self.date_from.strftime(DATETIME_FORMAT)

    @property
    def date_to_string(self) -> str:
        return self.date_to.strftime(DATETIME_FORMAT)


def validate_request(
    *,
    company_id: Any,
    date_from: Any,
    date_to: Any,
    purchase_order_line_ids: Any,
    limit: Any,
    now: datetime,
) -> ProjectionRequest:
    """Validate every caller-controlled bound before privileged ORM access."""

    normalized_company_id = _positive_integer(company_id, "company_id")
    normalized_limit = _positive_integer(limit, "limit")
    if normalized_limit > MAX_RESULTS:
        raise ProjectionPolicyError(f"limit must not exceed {MAX_RESULTS}")

    if not isinstance(purchase_order_line_ids, list) or not purchase_order_line_ids:
        raise ProjectionPolicyError("purchase_order_line_ids must be a non-empty JSON list")
    if len(purchase_order_line_ids) > MAX_LINE_IDS:
        raise ProjectionPolicyError(
            f"purchase_order_line_ids must not contain more than {MAX_LINE_IDS} values"
        )
    normalized_line_ids = tuple(
        _positive_integer(value, "purchase_order_line_ids") for value in purchase_order_line_ids
    )
    if len(set(normalized_line_ids)) != len(normalized_line_ids):
        raise ProjectionPolicyError("purchase_order_line_ids must not contain duplicates")

    normalized_from = _strict_datetime(date_from, "date_from")
    normalized_to = _strict_datetime(date_to, "date_to")
    if normalized_from >= normalized_to:
        raise ProjectionPolicyError("date_from must be earlier than date_to")
    if normalized_to - normalized_from > MAX_WINDOW:
        raise ProjectionPolicyError("the requested history window must not exceed 366 days")
    if normalized_to > now.replace(microsecond=0):
        raise ProjectionPolicyError("date_to must not be in the future")

    return ProjectionRequest(
        company_id=normalized_company_id,
        date_from=normalized_from,
        date_to=normalized_to,
        purchase_order_line_ids=normalized_line_ids,
        limit=normalized_limit,
    )


def build_projection_records(
    request: ProjectionRequest,
    *,
    lines: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    partners: list[dict[str, Any]],
    moves: list[dict[str, Any]],
    pickings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate joined evidence and emit only the fixed sanitized schema."""

    line_by_id = _unique_by_id(lines, "purchase order line")
    if set(line_by_id) != set(request.purchase_order_line_ids):
        raise ProjectionPolicyError("requested purchase order lines are unavailable or ambiguous")
    order_by_id = _unique_by_id(orders, "purchase order")
    partner_by_id = _unique_by_id(partners, "supplier")
    move_by_id = _unique_by_id(moves, "stock move")
    picking_by_id = _unique_by_id(pickings, "stock picking")
    if len(move_by_id) > request.limit:
        raise ProjectionPolicyError("the bounded result exceeds the requested limit")

    for line in line_by_id.values():
        _require_company(line, request.company_id, "purchase order line")
        if line.get("qty_received_method") != "stock_moves":
            raise ProjectionPolicyError("purchase order line is not stock-move-backed")
        _positive_decimal(line.get("ordered_quantity"), "ordered_quantity")
        _required_datetime(line.get("expected_arrival_at"), "expected_arrival_at")
        order = order_by_id.get(line.get("purchase_order_id"))
        if order is None:
            raise ProjectionPolicyError("purchase order relationship is incomplete")
        _require_company(order, request.company_id, "purchase order")
        if order.get("state") not in {"purchase", "done"}:
            raise ProjectionPolicyError("purchase order state is unsupported")
        if order.get("supplier_id") not in partner_by_id:
            raise ProjectionPolicyError("supplier relationship is incomplete")

    moves_by_picking: dict[int, list[dict[str, Any]]] = {}
    for move in move_by_id.values():
        _validate_move(request, move, line_by_id)
        picking_id = _positive_integer(move.get("stock_picking_id"), "stock_picking_id")
        if picking_id not in picking_by_id:
            raise ProjectionPolicyError("stock picking relationship is incomplete")
        moves_by_picking.setdefault(picking_id, []).append(move)

    for picking in picking_by_id.values():
        _validate_picking(request, picking)
        if picking["id"] not in moves_by_picking:
            raise ProjectionPolicyError("unrelated stock picking was included")
        backorder_id = picking.get("backorder_of_picking_id")
        if backorder_id:
            if backorder_id == picking["id"] or backorder_id not in picking_by_id:
                raise ProjectionPolicyError("backorder relationship leaves the bounded result")
            current_lines = {
                move["purchase_order_line_id"] for move in moves_by_picking[picking["id"]]
            }
            prior_lines = {
                move["purchase_order_line_id"] for move in moves_by_picking[backorder_id]
            }
            if current_lines.isdisjoint(prior_lines):
                raise ProjectionPolicyError(
                    "backorder relationship does not preserve a purchase line"
                )

    output: list[dict[str, Any]] = []
    for move in move_by_id.values():
        line = line_by_id[move["purchase_order_line_id"]]
        order = order_by_id[line["purchase_order_id"]]
        partner = partner_by_id[order["supplier_id"]]
        picking = picking_by_id[move["stock_picking_id"]]
        _validate_move_picking_relationship(move, picking, move_by_id)
        record = {
            "company_id": request.company_id,
            "commercial_partner_id": _positive_integer(
                partner.get("commercial_partner_id"), "commercial_partner_id"
            ),
            "purchase_order_id": order["id"],
            "purchase_order_line_id": line["id"],
            "product_id": line["product_id"],
            "product_uom_id": line["product_uom_id"],
            "expected_arrival_at": line["expected_arrival_at"],
            "stock_move_id": move["id"],
            "stock_picking_id": picking["id"],
            "move_processed_at": move["move_processed_at"],
            "ordered_quantity": _decimal_string(line["ordered_quantity"]),
            "completed_quantity": _decimal_string(move["completed_quantity"]),
            "state": move["state"],
            "source_location_usage": move["source_location_usage"],
            "destination_location_usage": move["destination_location_usage"],
            "backorder_of_picking_id": picking.get("backorder_of_picking_id") or None,
            "return_of_move_id": move.get("return_of_move_id") or None,
            "return_of_picking_id": picking.get("return_of_picking_id") or None,
        }
        if tuple(record) != RECORD_FIELDS:
            raise ProjectionPolicyError("projection schema changed unexpectedly")
        output.append(record)

    return sorted(output, key=lambda row: (row["move_processed_at"], row["stock_move_id"]))


def _validate_move(
    request: ProjectionRequest,
    move: dict[str, Any],
    line_by_id: dict[int, dict[str, Any]],
) -> None:
    _require_company(move, request.company_id, "stock move")
    if move.get("state") != "done":
        raise ProjectionPolicyError("stock move state is unsupported")
    processed_at = _required_datetime(move.get("move_processed_at"), "move_processed_at")
    if not request.date_from <= processed_at < request.date_to:
        raise ProjectionPolicyError("stock move leaves the bounded history window")
    _positive_decimal(move.get("completed_quantity"), "completed_quantity")
    line = line_by_id.get(move.get("purchase_order_line_id"))
    if line is None:
        raise ProjectionPolicyError("stock move purchase-line relationship is incomplete")
    if move.get("product_id") != line.get("product_id"):
        raise ProjectionPolicyError("stock move product relationship is ambiguous")
    if move.get("product_uom_id") != line.get("product_uom_id"):
        raise ProjectionPolicyError("stock move unit relationship is ambiguous")

    direction = (
        move.get("source_location_usage"),
        move.get("destination_location_usage"),
    )
    return_of_move_id = move.get("return_of_move_id")
    if direction == ("supplier", "internal"):
        if return_of_move_id:
            raise ProjectionPolicyError("inbound receipt unexpectedly identifies a returned move")
    elif direction == ("internal", "supplier"):
        if not return_of_move_id:
            raise ProjectionPolicyError(
                "supplier return lacks an explicit returned-move relationship"
            )
    else:
        raise ProjectionPolicyError("stock move direction is outside the supported subset")


def _validate_picking(request: ProjectionRequest, picking: dict[str, Any]) -> None:
    _require_company(picking, request.company_id, "stock picking")
    if picking.get("state") != "done":
        raise ProjectionPolicyError("stock picking state is unsupported")
    if picking.get("picking_type_code") != "incoming":
        raise ProjectionPolicyError("stock picking type is outside the supported subset")
    processed_at = _required_datetime(picking.get("transfer_processed_at"), "transfer_processed_at")
    if not request.date_from <= processed_at < request.date_to:
        raise ProjectionPolicyError("stock picking leaves the bounded history window")


def _validate_move_picking_relationship(
    move: dict[str, Any],
    picking: dict[str, Any],
    move_by_id: dict[int, dict[str, Any]],
) -> None:
    if move["move_processed_at"] != picking["transfer_processed_at"]:
        raise ProjectionPolicyError("move and picking completion timestamps disagree")
    return_move_id = move.get("return_of_move_id")
    return_picking_id = picking.get("return_of_picking_id")
    if not return_move_id:
        if return_picking_id:
            raise ProjectionPolicyError("ordinary receipt uses a return picking")
        return
    origin = move_by_id.get(return_move_id)
    if origin is None:
        raise ProjectionPolicyError("return relationship leaves the bounded result")
    if (
        origin.get("purchase_order_line_id") != move.get("purchase_order_line_id")
        or origin.get("product_id") != move.get("product_id")
        or origin.get("product_uom_id") != move.get("product_uom_id")
        or origin.get("source_location_usage") != "supplier"
        or origin.get("destination_location_usage") != "internal"
    ):
        raise ProjectionPolicyError("return relationship is ambiguous")
    if not return_picking_id or return_picking_id != origin.get("stock_picking_id"):
        raise ProjectionPolicyError("move and picking return relationships disagree")


def _unique_by_id(rows: list[dict[str, Any]], label: str) -> dict[int, dict[str, Any]]:
    output: dict[int, dict[str, Any]] = {}
    for row in rows:
        record_id = _positive_integer(row.get("id"), f"{label} id")
        if record_id in output:
            raise ProjectionPolicyError(f"duplicate {label} identity")
        output[record_id] = row
    return output


def _require_company(row: dict[str, Any], company_id: int, label: str) -> None:
    if row.get("company_id") != company_id:
        raise ProjectionPolicyError(f"{label} crosses the authorized company boundary")


def _strict_datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ProjectionPolicyError(f"{label} must use {DATETIME_FORMAT}")
    try:
        parsed = datetime.strptime(value, DATETIME_FORMAT)
    except ValueError as error:
        raise ProjectionPolicyError(f"{label} must use {DATETIME_FORMAT}") from error
    if parsed.strftime(DATETIME_FORMAT) != value:
        raise ProjectionPolicyError(f"{label} must use {DATETIME_FORMAT}")
    return parsed


def _required_datetime(value: Any, label: str) -> datetime:
    return _strict_datetime(value, label)


def _positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ProjectionPolicyError(f"{label} must be a positive integer")
    return value


def _positive_decimal(value: Any, label: str) -> Decimal:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ProjectionPolicyError(f"{label} must be numeric") from error
    if not decimal_value.is_finite() or decimal_value <= 0:
        raise ProjectionPolicyError(f"{label} must be greater than zero")
    return decimal_value


def _decimal_string(value: Any) -> str:
    decimal_value = _positive_decimal(value, "quantity")
    return format(decimal_value, "f")
