"""Optional live contract verification for an initialized local Odoo database."""

import asyncio
from typing import Any

import httpx
import pytest

from backend.app.config import settings
from odoo_adapter.rfq_reader import OdooRfqReader

pytestmark = pytest.mark.integration


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


@pytest.mark.parametrize(
    ("model", "expected_read"),
    [
        ("purchase.order", True),
        ("purchase.order.line", False),
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


def test_live_odoo_decision_input_schema_has_no_validated_grouping_field() -> None:
    """T4 candidate fields exist, but the probed explicit grouping fields do not."""

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
    assert {
        "alternative_po_ids",
        "source_po_id",
        "requisition_id",
    }.isdisjoint(purchase_order_fields)

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
        ("stock", "installed"),
    ]
