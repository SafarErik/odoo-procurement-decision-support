"""Optional live contract verification for an initialized local Odoo database."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
import pytest

from application.decision_input_assembly import (
    SourceAttribution,
    SupplementalOfferTerms,
    SupplementalValue,
    assemble_decision_input,
)
from application.decisions import evaluate_procurement_decision
from backend.app.config import settings
from decision_core import StrategicProfile
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from odoo_adapter.rfq_reader import OdooRfqReader

pytestmark = pytest.mark.integration

_T6_ORIGINS = ("T6-COMP-001-A", "T6-COMP-001-B", "T6-COMP-001-C")
_T7_ORIGINS = (
    "T7-HIST-001-ONTIME",
    "T7-HIST-002-LATE",
    "T7-HIST-003-BACKORDER",
    "T7-HIST-004-RETURN",
)


def _live_credentials() -> tuple[str, str, str] | None:
    api_key = settings.odoo_api_key.get_secret_value()
    if not settings.odoo_base_url or not settings.odoo_database or not api_key:
        return None
    return settings.odoo_base_url.rstrip("/"), settings.odoo_database, api_key


def _post_json2(model: str, method: str, payload: dict[str, Any]) -> Any:
    credentials = _live_credentials()
    if credentials is None:
        pytest.skip("Live Odoo credentials are not configured")
    base_url, database, api_key = credentials

    response = httpx.post(
        f"{base_url}/json/2/{model}/{method}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "X-Odoo-Database": database,
        },
        json=payload,
        timeout=settings.odoo_request_timeout_seconds,
    )
    assert response.status_code == 200, (
        f"Odoo {model}/{method} returned HTTP {response.status_code}"
    )
    return response.json()


def _t6_fixture_records() -> list[dict[str, Any]]:
    if not settings.run_t6_live_contracts:
        pytest.skip("Set RUN_T6_LIVE_CONTRACTS=true after creating the controlled T6 fixture")
    orders = _post_json2(
        "purchase.order",
        "search_read",
        {
            "domain": [["origin", "in", list(_T6_ORIGINS)]],
            "fields": ["id", "name", "origin", "purchase_group_id"],
            "limit": 4,
            "order": "origin asc",
        },
    )
    assert [order["origin"] for order in orders] == list(_T6_ORIGINS)
    return orders


def _t6_group_id() -> int:
    orders = _t6_fixture_records()
    group_ids = {
        order["purchase_group_id"][0]
        for order in orders
        if isinstance(order.get("purchase_group_id"), list)
    }
    assert len(group_ids) == 1
    return group_ids.pop()


def _require_t7_live_contracts() -> None:
    if not settings.run_t7_live_contracts:
        pytest.skip("Set RUN_T7_LIVE_CONTRACTS=true only after completing docs/T7_FIXTURE_SETUP.md")


def _t7_fixture_orders() -> list[dict[str, Any]]:
    _require_t7_live_contracts()
    orders = _post_json2(
        "purchase.order",
        "search_read",
        {
            "domain": [["origin", "in", list(_T7_ORIGINS)]],
            "fields": ["id", "origin", "partner_id", "company_id", "order_line"],
            "limit": len(_T7_ORIGINS) + 1,
            "order": "origin asc",
        },
    )
    assert [order["origin"] for order in orders] == list(_T7_ORIGINS)
    return orders


def _odoo_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace(" ", "T").replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def test_live_odoo_lists_open_rfqs_when_credentials_are_available() -> None:
    """The validated local database satisfies the adapter contract."""

    credentials = _live_credentials()
    if credentials is None:
        pytest.skip("Live Odoo credentials are not configured")
    base_url, database, api_key = credentials

    reader = OdooRfqReader(
        base_url=base_url,
        database=database,
        api_key=api_key,
        timeout_seconds=settings.odoo_request_timeout_seconds,
    )

    items = asyncio.run(reader.list_open_rfqs(5))

    assert items
    assert all(item.reference for item in items)
    assert all(item.vendor_name for item in items)
    assert all(item.total.currency for item in items)


def test_live_odoo_identity_has_read_only_purchase_order_access() -> None:
    """The durable integration identity is non-admin and cannot mutate RFQs."""

    context = _post_json2("res.users", "context_get", {})
    user_id = context.get("uid") if isinstance(context, dict) else None
    assert isinstance(user_id, int)

    is_settings_administrator = _post_json2(
        "res.users",
        "has_group",
        {"ids": [user_id], "group_ext_id": "base.group_system"},
    )
    assert is_settings_administrator is False

    user_records = _post_json2(
        "res.users",
        "read",
        {"ids": [user_id], "fields": ["group_ids"]},
    )
    direct_group_ids = user_records[0]["group_ids"]
    group_records = _post_json2(
        "res.groups",
        "read",
        {"ids": direct_group_ids, "fields": ["name"]},
    )
    assert {group["name"] for group in group_records} == {
        "Procurement RFQ API Reader",
        "Role / User",
    }

    access = {
        operation: _post_json2(
            "purchase.order",
            "check_access_rights",
            {"operation": operation, "raise_exception": False},
        )
        for operation in ("read", "create", "write", "unlink")
    }
    assert access == {
        "read": True,
        "create": False,
        "write": False,
        "unlink": False,
    }

    can_manage_alternatives = _post_json2(
        "res.users",
        "has_group",
        {
            "ids": [user_id],
            "group_ext_id": "purchase_requisition.group_purchase_alternatives",
        },
    )
    assert can_manage_alternatives is False


def test_live_odoo_t5_line_acl_allows_only_company_scoped_reads() -> None:
    """The integration identity can traverse permitted RFQ lines without mutation."""

    context = _post_json2("res.users", "context_get", {})
    user_id = context["uid"]
    user = _post_json2(
        "res.users",
        "read",
        {"ids": [user_id], "fields": ["company_id", "company_ids"]},
    )[0]
    allowed_company_ids = user["company_ids"]
    assert user["company_id"][0] == 1
    assert allowed_company_ids == [1]

    orders = _post_json2(
        "purchase.order",
        "search_read",
        {
            "domain": [["state", "in", ["draft", "sent", "to approve"]]],
            "fields": [
                "id",
                "company_id",
                "order_line",
                "purchase_group_id",
                "alternative_po_ids",
            ],
            "limit": 5,
            "order": "id asc",
        },
    )
    assert orders
    assert all(order["company_id"][0] in allowed_company_ids for order in orders)

    line_ids = [line_id for order in orders for line_id in order["order_line"]]
    assert line_ids
    lines = _post_json2(
        "purchase.order.line",
        "search_read",
        {
            "domain": [["id", "in", line_ids]],
            "fields": [
                "id",
                "order_id",
                "product_id",
                "product_uom_id",
                "product_qty",
                "price_unit",
                "discount",
                "tax_ids",
                "currency_id",
                "company_id",
                "date_planned",
                "selected_seller_id",
            ],
            "limit": len(line_ids),
            "order": "id asc",
        },
    )
    assert {line["id"] for line in lines} == set(line_ids)
    assert all(line["company_id"][0] in allowed_company_ids for line in lines)

    outside_company_lines = _post_json2(
        "purchase.order.line",
        "search_read",
        {
            "domain": [["company_id", "not in", allowed_company_ids]],
            "fields": ["id", "company_id"],
            "limit": 1,
        },
    )
    assert outside_company_lines == []


@pytest.mark.parametrize(
    ("model", "expected_read"),
    [
        ("purchase.order", True),
        ("purchase.order.line", True),
        ("purchase.order.group", False),
        ("purchase.requisition", False),
        ("product.product", True),
        ("product.template", True),
        ("product.supplierinfo", True),
        ("res.partner", True),
        ("res.currency", True),
        ("uom.uom", True),
    ],
)
def test_live_odoo_decision_input_models_are_read_only(model: str, expected_read: bool) -> None:
    """T4 records exact effective access without attempting a business-data write."""

    access = {
        operation: _post_json2(
            model,
            "check_access_rights",
            {"operation": operation, "raise_exception": False},
        )
        for operation in ("read", "create", "write", "unlink")
    }

    assert access == {
        "read": expected_read,
        "create": False,
        "write": False,
        "unlink": False,
    }


def test_live_odoo_t5_schema_exposes_standard_alternative_grouping() -> None:
    """The installed standard module exposes its persisted alternative-RFQ group."""

    purchase_order_fields = _post_json2(
        "purchase.order",
        "fields_get",
        {
            "allfields": [
                "id",
                "partner_id",
                "date_order",
                "date_planned",
                "state",
                "currency_id",
                "company_id",
                "order_line",
                "purchase_group_id",
                "alternative_po_ids",
                "source_po_id",
                "requisition_id",
                "origin",
            ],
            "attributes": ["type", "relation"],
        },
    )
    assert purchase_order_fields["order_line"] == {
        "type": "one2many",
        "relation": "purchase.order.line",
    }
    assert purchase_order_fields["partner_id"] == {
        "type": "many2one",
        "relation": "res.partner",
    }
    assert purchase_order_fields["purchase_group_id"] == {
        "type": "many2one",
        "relation": "purchase.order.group",
    }
    assert purchase_order_fields["alternative_po_ids"] == {
        "type": "one2many",
        "relation": "purchase.order",
    }
    assert purchase_order_fields["requisition_id"] == {
        "type": "many2one",
        "relation": "purchase.requisition",
    }
    assert "source_po_id" not in purchase_order_fields

    line_fields = _post_json2(
        "purchase.order.line",
        "fields_get",
        {
            "allfields": [
                "order_id",
                "product_id",
                "product_uom_id",
                "product_qty",
                "price_unit",
                "discount",
                "currency_id",
                "date_planned",
            ],
            "attributes": ["type", "relation"],
        },
    )
    assert line_fields["order_id"] == {
        "type": "many2one",
        "relation": "purchase.order",
    }
    assert line_fields["product_id"] == {
        "type": "many2one",
        "relation": "product.product",
    }
    assert line_fields["product_uom_id"] == {
        "type": "many2one",
        "relation": "uom.uom",
    }
    assert line_fields["product_qty"]["type"] == "float"
    assert line_fields["price_unit"]["type"] == "float"
    assert line_fields["date_planned"]["type"] == "datetime"

    supplier_fields = _post_json2(
        "product.supplierinfo",
        "fields_get",
        {
            "allfields": [
                "partner_id",
                "product_id",
                "product_tmpl_id",
                "product_uom_id",
                "min_qty",
                "price",
                "currency_id",
                "delay",
                "date_start",
                "date_end",
                "company_id",
            ],
            "attributes": ["type", "relation", "required"],
        },
    )
    assert supplier_fields["min_qty"]["type"] == "float"
    assert supplier_fields["delay"] == {"type": "integer", "required": True}
    assert supplier_fields["product_uom_id"] == {
        "type": "many2one",
        "relation": "uom.uom",
        "required": True,
    }

    modules = _post_json2(
        "ir.module.module",
        "search_read",
        {
            "domain": [
                ["name", "in", ["purchase", "stock", "purchase_requisition"]],
                ["state", "=", "installed"],
            ],
            "fields": ["name", "state"],
            "limit": 3,
            "order": "name asc",
        },
    )
    assert [(module["name"], module["state"]) for module in modules] == [
        ("purchase", "installed"),
        ("purchase_requisition", "installed"),
        ("stock", "installed"),
    ]


def test_live_odoo_t5_purchase_agreements_are_installed() -> None:
    """Phase B enabled the standard Community Purchase Agreements capability."""

    modules = _post_json2(
        "ir.module.module",
        "search_read",
        {
            "domain": [["name", "=", "purchase_requisition"]],
            "fields": [
                "name",
                "shortdesc",
                "state",
                "license",
                "application",
            ],
            "limit": 2,
        },
    )
    assert [
        {key: module[key] for key in ("name", "shortdesc", "state", "license", "application")}
        for module in modules
    ] == [
        {
            "name": "purchase_requisition",
            "shortdesc": "Purchase Agreements",
            "state": "installed",
            "license": "LGPL-3",
            "application": False,
        }
    ]

    settings_fields = _post_json2(
        "res.config.settings",
        "fields_get",
        {
            "allfields": ["module_purchase_requisition"],
            "attributes": ["string", "type"],
        },
    )
    assert settings_fields == {
        "module_purchase_requisition": {
            "string": "Purchase Agreements",
            "type": "boolean",
        }
    }


def test_live_odoo_t5_line_schema_preserves_semantic_blockers() -> None:
    """Phase B confirms that line access does not repair MOQ or lead-time meaning."""

    line_fields = _post_json2(
        "purchase.order.line",
        "fields_get",
        {
            "allfields": [
                "date_planned",
                "discount",
                "price_unit",
                "price_unit_discounted",
                "selected_seller_id",
                "tax_ids",
            ],
            "attributes": ["string", "type", "relation", "store", "help"],
        },
    )
    assert line_fields["selected_seller_id"] == {
        "help": "Technical field to get the vendor pricelist used to generate this line",
        "relation": "product.supplierinfo",
        "store": False,
        "string": "Selected Seller",
        "type": "many2one",
    }
    assert line_fields["tax_ids"] == {
        "relation": "account.tax",
        "store": True,
        "string": "Taxes",
        "type": "many2many",
    }
    assert line_fields["price_unit"] == {
        "store": True,
        "string": "Unit Price",
        "type": "float",
    }
    assert line_fields["price_unit_discounted"] == {
        "store": False,
        "string": "Unit Price (Discounted)",
        "type": "float",
    }
    assert line_fields["date_planned"] == {
        "help": (
            "Delivery date expected from vendor. This date respectively defaults to "
            "vendor pricelist lead time then today's date."
        ),
        "store": True,
        "string": "Expected Arrival",
        "type": "datetime",
    }

    supplier_fields = _post_json2(
        "product.supplierinfo",
        "fields_get",
        {
            "allfields": ["delay", "min_qty"],
            "attributes": ["string", "type", "required", "store", "help"],
        },
    )
    assert supplier_fields["min_qty"] == {
        "help": (
            "The quantity to purchase from this vendor to benefit from the unit price. "
            "If a vendor unit is set, quantity should be specified in this unit, "
            "otherwise it should be specified in the default unit of the product."
        ),
        "required": True,
        "store": True,
        "string": "Quantity",
        "type": "float",
    }
    assert supplier_fields["delay"] == {
        "help": (
            "Lead time in days between the confirmation of the purchase order and the "
            "receipt of the products in your warehouse. Used by the scheduler for "
            "automatic computation of the purchase order planning."
        ),
        "required": True,
        "store": True,
        "string": "Lead Time",
        "type": "integer",
    }


def test_live_odoo_t6_reads_controlled_group_with_read_only_identity() -> None:
    """The opt-in fixture exposes exactly the supported three-offer fact set."""

    credentials = _live_credentials()
    if credentials is None:
        pytest.skip("Live Odoo credentials are not configured")
    base_url, database, api_key = credentials
    reader = OdooComparisonCaseReader(
        base_url=base_url,
        database=database,
        api_key=api_key,
        timeout_seconds=settings.odoo_request_timeout_seconds,
    )

    facts = asyncio.run(reader.read_comparison_case(_t6_group_id()))

    origin_by_offer_id = {
        f"odoo:purchase.order:{order['id']}": order["origin"] for order in _t6_fixture_records()
    }
    assert {offer.offer_id for offer in facts.offers} == set(origin_by_offer_id)
    assert len({offer.comparison_case_id for offer in facts.offers}) == 1
    assert len({offer.supplier_id for offer in facts.offers}) == 3
    assert len({offer.company_id for offer in facts.offers}) == 1
    assert len({offer.currency_id for offer in facts.offers}) == 1
    assert all(len(offer.lines) == 1 for offer in facts.offers)
    assert {offer.lines[0].quantity for offer in facts.offers} == {Decimal("100")}
    assert len({offer.lines[0].product_id for offer in facts.offers}) == 1
    assert len({offer.lines[0].uom_id for offer in facts.offers}) == 1
    assert all(offer.lines[0].discount == 0 for offer in facts.offers)
    assert all(not offer.lines[0].tax_ids for offer in facts.offers)
    assert {
        origin_by_offer_id[offer.offer_id]: offer.lines[0].unit_price for offer in facts.offers
    } == {
        "T6-COMP-001-A": Decimal("10"),
        "T6-COMP-001-B": Decimal("12"),
        "T6-COMP-001-C": Decimal("9"),
    }


def test_live_odoo_t6_full_hybrid_chain_is_deterministic() -> None:
    """Odoo facts plus attributed terms evaluate through the unchanged use case."""

    credentials = _live_credentials()
    if credentials is None:
        pytest.skip("Live Odoo credentials are not configured")
    base_url, database, api_key = credentials
    reader = OdooComparisonCaseReader(
        base_url=base_url,
        database=database,
        api_key=api_key,
        timeout_seconds=settings.odoo_request_timeout_seconds,
    )
    facts = asyncio.run(reader.read_comparison_case(_t6_group_id()))
    origin_by_offer_id = {
        f"odoo:purchase.order:{order['id']}": order["origin"] for order in _t6_fixture_records()
    }
    values = {
        "T6-COMP-001-A": (Decimal("50"), Decimal("10")),
        "T6-COMP-001-B": (Decimal("100"), Decimal("5")),
        "T6-COMP-001-C": (Decimal("150"), Decimal("8")),
    }
    terms = tuple(
        SupplementalOfferTerms(
            offer_id=offer.offer_id,
            hard_minimum_order_quantity=SupplementalValue(
                values[origin_by_offer_id[offer.offer_id]][0],
                SourceAttribution(
                    "minimum_order_quantity",
                    "controlled_fixture_statement",
                    f"{origin_by_offer_id[offer.offer_id]}:hard-moq",
                    offer.observed_at,
                ),
            ),
            supplier_promised_lead_time_days=SupplementalValue(
                values[origin_by_offer_id[offer.offer_id]][1],
                SourceAttribution(
                    "lead_time_days",
                    "controlled_fixture_statement",
                    f"{origin_by_offer_id[offer.offer_id]}:promised-lead-time",
                    offer.observed_at,
                ),
            ),
        )
        for offer in facts.offers
    )
    assembled = assemble_decision_input(
        facts,
        terms,
        StrategicProfile.cost_focused(),
        SourceAttribution(
            "strategic_profile",
            "application_configuration",
            "profile:cost-focused:v1",
            facts.observed_at,
        ),
    )

    result = evaluate_procurement_decision(
        assembled.canonical.requirement,
        assembled.canonical.offers,
        assembled.canonical.profile,
    )
    assert [origin_by_offer_id[item.offer.offer_id] for item in result.ranked_offers] == [
        "T6-COMP-001-A",
        "T6-COMP-001-B",
    ]
    assert [origin_by_offer_id[item.offer.offer_id] for item in result.excluded_offers] == [
        "T6-COMP-001-C"
    ]
    assert result.excluded_offers[0].explanation
    expected_provenance_paths = {
        "requirement.requirement_id",
        "requirement.requested_quantity",
        "profile.name",
        "profile.unit_price_weight",
        "profile.lead_time_weight",
    }
    for offer in facts.offers:
        expected_provenance_paths.update(
            {
                f"offers[{offer.offer_id}].offer_id",
                f"offers[{offer.offer_id}].supplier_id",
                f"offers[{offer.offer_id}].unit_price",
                f"offers[{offer.offer_id}].lead_time_days",
                f"offers[{offer.offer_id}].minimum_order_quantity",
            }
        )
    provenance_paths = {entry.canonical_path for entry in assembled.provenance.entries}
    assert provenance_paths == expected_provenance_paths
    assert sum(
        entry.canonical_path == "requirement.requested_quantity"
        for entry in assembled.provenance.entries
    ) == len(facts.offers)


def test_live_odoo_t7_inventory_history_is_read_only() -> None:
    """Require the approved post-remediation inventory-history access boundary."""

    _require_t7_live_contracts()

    access = {
        model: {
            operation: _post_json2(
                model,
                "check_access_rights",
                {"operation": operation, "raise_exception": False},
            )
            for operation in ("read", "create", "write", "unlink")
        }
        for model in ("stock.picking", "stock.move", "stock.move.line")
    }
    assert access == {
        "stock.picking": {
            "read": True,
            "create": False,
            "write": False,
            "unlink": False,
        },
        "stock.move": {
            "read": True,
            "create": False,
            "write": False,
            "unlink": False,
        },
        "stock.move.line": {
            "read": True,
            "create": False,
            "write": False,
            "unlink": False,
        },
    }

    line_fields = _post_json2(
        "purchase.order.line",
        "fields_get",
        {
            "allfields": [
                "date_planned",
                "move_ids",
                "qty_received",
                "qty_received_method",
            ],
            "attributes": ["string", "type", "relation", "store", "help"],
        },
    )
    assert line_fields["date_planned"] == {
        "help": (
            "Delivery date expected from vendor. This date respectively defaults to "
            "vendor pricelist lead time then today's date."
        ),
        "store": True,
        "string": "Expected Arrival",
        "type": "datetime",
    }
    assert line_fields["move_ids"] == {
        "relation": "stock.move",
        "store": True,
        "string": "Reservation",
        "type": "one2many",
    }
    assert line_fields["qty_received"]["type"] == "float"
    assert line_fields["qty_received_method"]["type"] == "selection"

    move_fields = _post_json2(
        "stock.move",
        "fields_get",
        {
            "allfields": [
                "purchase_line_id",
                "picking_id",
                "state",
                "quantity",
                "date",
                "location_usage",
                "location_dest_usage",
                "origin_returned_move_id",
                "company_id",
            ],
            "attributes": ["string", "type", "relation", "store", "help"],
        },
    )
    assert move_fields["purchase_line_id"]["relation"] == "purchase.order.line"
    assert move_fields["picking_id"]["relation"] == "stock.picking"
    assert move_fields["date"]["help"] == (
        "Scheduled date until move is done, then date of actual move processing"
    )
    assert move_fields["origin_returned_move_id"]["relation"] == "stock.move"

    picking_fields = _post_json2(
        "stock.picking",
        "fields_get",
        {
            "allfields": [
                "state",
                "date_done",
                "picking_type_code",
                "backorder_id",
                "return_id",
                "company_id",
            ],
            "attributes": ["string", "type", "relation", "store", "help"],
        },
    )
    assert picking_fields["date_done"]["help"] == (
        "Date at which the transfer has been processed or cancelled."
    )
    assert picking_fields["backorder_id"]["relation"] == "stock.picking"
    assert picking_fields["return_id"]["relation"] == "stock.picking"

    outside_company_lines = _post_json2(
        "stock.move.line",
        "search_read",
        {
            "domain": [["company_id", "not in", [1]]],
            "fields": ["id", "company_id"],
            "limit": 1,
        },
    )
    assert outside_company_lines == []


def test_live_odoo_t7_controlled_history_supports_candidate_kpi() -> None:
    """Validate the exact controlled receipt history before any production adapter exists."""

    orders = _t7_fixture_orders()
    assert len({order["company_id"][0] for order in orders}) == 1
    assert all(len(order["order_line"]) == 1 for order in orders)

    partner_ids = [order["partner_id"][0] for order in orders]
    partners = _post_json2(
        "res.partner",
        "search_read",
        {
            "domain": [["id", "in", partner_ids]],
            "fields": ["id", "commercial_partner_id"],
            "limit": len(partner_ids),
            "order": "id asc",
        },
    )
    commercial_by_partner = {
        partner["id"]: partner["commercial_partner_id"][0] for partner in partners
    }
    assert len({commercial_by_partner[partner_id] for partner_id in partner_ids}) == 1

    line_ids = [order["order_line"][0] for order in orders]
    lines = _post_json2(
        "purchase.order.line",
        "search_read",
        {
            "domain": [["id", "in", line_ids]],
            "fields": [
                "id",
                "order_id",
                "product_id",
                "product_uom_id",
                "product_qty",
                "qty_received",
                "qty_received_method",
                "date_planned",
                "company_id",
            ],
            "limit": len(line_ids),
            "order": "id asc",
        },
    )
    assert {line["id"] for line in lines} == set(line_ids)
    assert all(line["product_qty"] == 100 for line in lines)
    assert all(line["qty_received_method"] == "stock_moves" for line in lines)
    assert len({line["product_id"][0] for line in lines}) == 1
    assert len({line["product_uom_id"][0] for line in lines}) == 1

    moves = _post_json2(
        "stock.move",
        "search_read",
        {
            "domain": [["purchase_line_id", "in", line_ids]],
            "fields": [
                "id",
                "purchase_line_id",
                "picking_id",
                "product_id",
                "product_uom",
                "product_uom_qty",
                "quantity",
                "state",
                "date",
                "company_id",
                "location_usage",
                "location_dest_usage",
                "origin_returned_move_id",
                "returned_move_ids",
            ],
            "limit": 40,
            "order": "date asc, id asc",
        },
    )
    assert moves
    picking_ids = sorted({move["picking_id"][0] for move in moves if move["picking_id"]})
    pickings = _post_json2(
        "stock.picking",
        "search_read",
        {
            "domain": [["id", "in", picking_ids]],
            "fields": [
                "id",
                "state",
                "date_done",
                "picking_type_code",
                "backorder_id",
                "return_id",
                "company_id",
            ],
            "limit": 20,
            "order": "id asc",
        },
    )
    assert {picking["id"] for picking in pickings} == set(picking_ids)
    picking_by_id = {picking["id"]: picking for picking in pickings}
    assert all(move["state"] == "done" for move in moves)
    assert all(picking["state"] == "done" for picking in pickings)
    assert all(
        _odoo_datetime(move["date"])
        == _odoo_datetime(picking_by_id[move["picking_id"][0]]["date_done"])
        for move in moves
    )

    order_by_id = {order["id"]: order for order in orders}
    line_by_id = {line["id"]: line for line in lines}
    marker_by_line_id = {line["id"]: order_by_id[line["order_id"][0]]["origin"] for line in lines}
    moves_by_marker = {
        marker: [move for move in moves if marker_by_line_id[move["purchase_line_id"][0]] == marker]
        for marker in _T7_ORIGINS
    }
    inbound_by_marker = {
        marker: [
            move
            for move in marker_moves
            if move["location_usage"] == "supplier"
            and move["location_dest_usage"] == "internal"
            and not move["origin_returned_move_id"]
        ]
        for marker, marker_moves in moves_by_marker.items()
    }
    for marker, inbound_moves in inbound_by_marker.items():
        line = line_by_id[
            next(
                line_id
                for line_id, line_marker in marker_by_line_id.items()
                if line_marker == marker
            )
        ]
        assert sum(move["quantity"] for move in inbound_moves) >= line["product_qty"]

    def completion(marker: str) -> datetime:
        return max(_odoo_datetime(move["date"]) for move in inbound_by_marker[marker])

    def expected(marker: str) -> datetime:
        line_id = next(
            line_id for line_id, line_marker in marker_by_line_id.items() if line_marker == marker
        )
        return _odoo_datetime(line_by_id[line_id]["date_planned"])

    assert completion("T7-HIST-001-ONTIME") <= expected("T7-HIST-001-ONTIME")
    assert completion("T7-HIST-002-LATE") > expected("T7-HIST-002-LATE")
    assert completion("T7-HIST-003-BACKORDER") > expected("T7-HIST-003-BACKORDER")
    backorder_pickings = {
        move["picking_id"][0] for move in inbound_by_marker["T7-HIST-003-BACKORDER"]
    }
    assert len(backorder_pickings) == 2
    assert (
        sum(bool(picking_by_id[picking_id]["backorder_id"]) for picking_id in backorder_pickings)
        == 1
    )

    return_moves = [
        move
        for move in moves_by_marker["T7-HIST-004-RETURN"]
        if move["origin_returned_move_id"] and move["location_dest_usage"] == "supplier"
    ]
    assert return_moves

    eligible_markers = _T7_ORIGINS[:3]
    adhered = sum(completion(marker) <= expected(marker) for marker in eligible_markers)
    assert (adhered, len(eligible_markers)) == (1, 3)
    assert (Decimal(adhered) / Decimal(len(eligible_markers)) * 100).quantize(
        Decimal("0.01")
    ) == Decimal("33.33")
