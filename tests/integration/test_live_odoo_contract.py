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
