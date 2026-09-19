"""Guarded JSON-2 projection for the T7 historical-receipt evidence subset."""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from ..projection_policy import (
    SCHEMA_VERSION,
    ProjectionPolicyError,
    build_projection_records,
    validate_request,
)

_READER_GROUP = "t7s_inventory_history_projection.group_inventory_history_projection_reader"
_LINE_FIELDS = (
    "order_id",
    "product_id",
    "product_uom_id",
    "product_qty",
    "date_planned",
    "company_id",
    "qty_received_method",
)
_ORDER_FIELDS = ("partner_id", "company_id", "state")
_PARTNER_FIELDS = ("commercial_partner_id",)
_MOVE_FIELDS = (
    "purchase_line_id",
    "picking_id",
    "product_id",
    "product_uom",
    "quantity",
    "state",
    "date",
    "company_id",
    "location_usage",
    "location_dest_usage",
    "origin_returned_move_id",
)
_PICKING_FIELDS = (
    "state",
    "date_done",
    "picking_type_code",
    "backorder_id",
    "return_id",
    "company_id",
)


class InventoryHistoryProjection(models.AbstractModel):
    """Method-only projection; no table, generic CRUD surface, menu, or view."""

    _name = "procurement.inventory.history.projection"
    _description = "Bounded read-only procurement inventory history projection"

    @api.model
    @api.readonly
    def read_bounded_history(
        self,
        company_id=None,
        date_from=None,
        date_to=None,
        purchase_order_line_ids=None,
        limit=None,
    ):
        """Return fixed receipt evidence after validating all caller-controlled bounds."""

        if not self.env.user.has_group(_READER_GROUP):
            raise AccessError(_("The T7-S projection-reader group is required."))
        try:
            request = validate_request(
                company_id=company_id,
                date_from=date_from,
                date_to=date_to,
                purchase_order_line_ids=purchase_order_line_ids,
                limit=limit,
                now=fields.Datetime.to_datetime(fields.Datetime.now()),
            )
        except ProjectionPolicyError as error:
            raise ValidationError(_("Invalid bounded history request: %s", error)) from error

        authorized_company_ids = set(self.env.user.company_ids.ids)
        if (
            request.company_id != self.env.company.id
            or request.company_id not in authorized_company_ids
        ):
            raise AccessError(_("The requested company is not the active authorized company."))

        try:
            lines = self._read_lines(request)
            orders = self._read_orders(request, lines)
            partners = self._read_partners(orders)
            moves = self._read_moves(request)
            pickings = self._read_pickings(request, moves)
            records = build_projection_records(
                request,
                lines=lines,
                orders=orders,
                partners=partners,
                moves=moves,
                pickings=pickings,
            )
        except ProjectionPolicyError as error:
            raise ValidationError(
                _("Unsupported or ambiguous receipt history: %s", error)
            ) from error

        return {
            "schema_version": SCHEMA_VERSION,
            "company_id": request.company_id,
            "date_from": request.date_from_string,
            "date_to": request.date_to_string,
            "result_count": len(records),
            "records": records,
        }

    def _read_lines(self, request):
        domain = [
            ("id", "in", list(request.purchase_order_line_ids)),
            ("company_id", "=", request.company_id),
        ]
        records = (
            self.env["purchase.order.line"]
            .sudo()
            .search_fetch(
                domain,
                _LINE_FIELDS,
                limit=len(request.purchase_order_line_ids) + 1,
                order="id asc",
            )
        )
        if len(records) != len(request.purchase_order_line_ids):
            raise ProjectionPolicyError("requested purchase order lines are unavailable")
        return [
            {
                "id": line.id,
                "purchase_order_id": line.order_id.id,
                "product_id": line.product_id.id,
                "product_uom_id": line.product_uom_id.id,
                "ordered_quantity": str(line.product_qty),
                "expected_arrival_at": fields.Datetime.to_string(line.date_planned),
                "company_id": line.company_id.id,
                "qty_received_method": line.qty_received_method,
            }
            for line in records
        ]

    def _read_orders(self, request, lines):
        order_ids = sorted({line["purchase_order_id"] for line in lines})
        domain = [("id", "in", order_ids), ("company_id", "=", request.company_id)]
        records = (
            self.env["purchase.order"]
            .sudo()
            .search_fetch(domain, _ORDER_FIELDS, limit=len(order_ids) + 1, order="id asc")
        )
        if len(records) != len(order_ids):
            raise ProjectionPolicyError("purchase order relationship is incomplete")
        return [
            {
                "id": order.id,
                "supplier_id": order.partner_id.id,
                "company_id": order.company_id.id,
                "state": order.state,
            }
            for order in records
        ]

    def _read_partners(self, orders):
        partner_ids = sorted({order["supplier_id"] for order in orders})
        domain = [("id", "in", partner_ids)]
        records = (
            self.env["res.partner"]
            .sudo()
            .search_fetch(domain, _PARTNER_FIELDS, limit=len(partner_ids) + 1, order="id asc")
        )
        if len(records) != len(partner_ids):
            raise ProjectionPolicyError("supplier relationship is incomplete")
        return [
            {
                "id": partner.id,
                "commercial_partner_id": partner.commercial_partner_id.id,
            }
            for partner in records
        ]

    def _read_moves(self, request):
        domain = [
            ("purchase_line_id", "in", list(request.purchase_order_line_ids)),
            ("company_id", "=", request.company_id),
            ("date", ">=", request.date_from_string),
            ("date", "<", request.date_to_string),
        ]
        records = (
            self.env["stock.move"]
            .sudo()
            .search_fetch(domain, _MOVE_FIELDS, limit=request.limit + 1, order="date asc, id asc")
        )
        if len(records) > request.limit:
            raise ProjectionPolicyError("the bounded result exceeds the requested limit")
        return [
            {
                "id": move.id,
                "purchase_order_line_id": move.purchase_line_id.id,
                "stock_picking_id": move.picking_id.id,
                "product_id": move.product_id.id,
                "product_uom_id": move.product_uom.id,
                "completed_quantity": str(move.quantity),
                "state": move.state,
                "move_processed_at": fields.Datetime.to_string(move.date),
                "company_id": move.company_id.id,
                "source_location_usage": move.location_usage,
                "destination_location_usage": move.location_dest_usage,
                "return_of_move_id": move.origin_returned_move_id.id or None,
            }
            for move in records
        ]

    def _read_pickings(self, request, moves):
        picking_ids = sorted({move["stock_picking_id"] for move in moves})
        if not picking_ids:
            return []
        domain = [
            ("id", "in", picking_ids),
            ("company_id", "=", request.company_id),
            ("date_done", ">=", request.date_from_string),
            ("date_done", "<", request.date_to_string),
        ]
        records = (
            self.env["stock.picking"]
            .sudo()
            .search_fetch(domain, _PICKING_FIELDS, limit=len(picking_ids) + 1, order="id asc")
        )
        if len(records) != len(picking_ids):
            raise ProjectionPolicyError("stock picking relationship is incomplete")
        return [
            {
                "id": picking.id,
                "state": picking.state,
                "transfer_processed_at": fields.Datetime.to_string(picking.date_done),
                "picking_type_code": picking.picking_type_code,
                "backorder_of_picking_id": picking.backorder_id.id or None,
                "return_of_picking_id": picking.return_id.id or None,
                "company_id": picking.company_id.id,
            }
            for picking in records
        ]
