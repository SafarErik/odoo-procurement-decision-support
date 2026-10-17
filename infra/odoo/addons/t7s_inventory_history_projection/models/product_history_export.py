"""Guarded JSON-2 export of one product's purchase obligations and receipts."""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from ..product_history_policy import (
    MAX_MOVES_PER_LINE,
    SCHEMA_VERSION,
    ProductHistoryPolicyError,
    build_product_history,
    validate_product_request,
)

_READER_GROUP = "t7s_inventory_history_projection.group_inventory_history_projection_reader"


class ProductHistoryExport(models.AbstractModel):
    """Method-only export; no table, generic CRUD surface, menu, or view."""

    _name = "procurement.product.history.export"
    _description = "Bounded read-only purchase history export for one product"

    @api.model
    @api.readonly
    def read_product_history(
        self, company_id=None, product_id=None, date_from=None, date_to=None, limit=None
    ):
        """Return confirmed lines with Expected Arrival in [date_from, date_to)."""

        if not self.env.user.has_group(_READER_GROUP):
            raise AccessError(_("The history projection-reader group is required."))
        try:
            request = validate_product_request(
                company_id=company_id,
                product_id=product_id,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                now=fields.Datetime.to_datetime(fields.Datetime.now()),
            )
        except ProductHistoryPolicyError as error:
            raise ValidationError(_("Invalid bounded history request: %s", error)) from error
        if request.company_id != self.env.company.id or request.company_id not in set(
            self.env.user.company_ids.ids
        ):
            raise AccessError(_("The requested company is not the active authorized company."))

        lines = (
            self.env["purchase.order.line"]
            .sudo()
            .search_fetch(
                [
                    ("company_id", "=", request.company_id),
                    ("product_id", "=", request.product_id),
                    ("order_id.state", "in", ["purchase", "done"]),
                    ("date_planned", ">=", request.date_from_string),
                    ("date_planned", "<", request.date_to_string),
                ],
                (
                    "order_id",
                    "product_id",
                    "product_uom_id",
                    "product_qty",
                    "date_planned",
                    "company_id",
                    "qty_received_method",
                ),
                limit=request.limit + 1,
                order="date_planned asc, id asc",
            )
        )
        orders = lines.order_id
        moves = (
            self.env["stock.move"]
            .sudo()
            .search_fetch(
                [
                    ("purchase_line_id", "in", lines.ids),
                    ("company_id", "=", request.company_id),
                    ("state", "=", "done"),
                ],
                (
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
                ),
                limit=len(lines) * MAX_MOVES_PER_LINE + 1,
                order="date asc, id asc",
            )
        )
        if len(moves) > len(lines) * MAX_MOVES_PER_LINE:
            raise ValidationError(_("The bounded receipt result exceeds its limit."))
        pickings = moves.picking_id
        try:
            records = build_product_history(
                request,
                lines=[
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
                    for line in lines
                ],
                orders=[
                    {
                        "id": order.id,
                        "supplier_id": order.partner_id.id,
                        "company_id": order.company_id.id,
                        "state": order.state,
                        "confirmed_at": fields.Datetime.to_string(order.date_approve),
                    }
                    for order in orders.sudo()
                ],
                partners=[
                    {"id": partner.id, "commercial_partner_id": partner.commercial_partner_id.id}
                    for partner in orders.sudo().partner_id
                ],
                moves=[
                    {
                        "id": move.id,
                        "purchase_order_line_id": move.purchase_line_id.id,
                        "stock_picking_id": move.picking_id.id,
                        "product_id": move.product_id.id,
                        "product_uom_id": move.product_uom.id,
                        "quantity": str(move.quantity),
                        "state": move.state,
                        "processed_at": fields.Datetime.to_string(move.date),
                        "company_id": move.company_id.id,
                        "source_location_usage": move.location_usage,
                        "destination_location_usage": move.location_dest_usage,
                        "return_of_move_id": move.origin_returned_move_id.id or None,
                    }
                    for move in moves
                ],
                pickings=[
                    {
                        "id": picking.id,
                        "state": picking.state,
                        "processed_at": fields.Datetime.to_string(picking.date_done),
                        "picking_type_code": picking.picking_type_code,
                        "backorder_of_picking_id": picking.backorder_id.id or None,
                        "company_id": picking.company_id.id,
                    }
                    for picking in pickings.sudo()
                ],
            )
        except ProductHistoryPolicyError as error:
            raise ValidationError(
                _("Unsupported or ambiguous purchase history: %s", error)
            ) from error

        return {
            "schema_version": SCHEMA_VERSION,
            "company_id": request.company_id,
            "product_id": request.product_id,
            "date_from": request.date_from_string,
            "date_to": request.date_to_string,
            "result_count": len(records),
            "lines": records,
        }
