"""Opt-in live check of the bounded purchase-history export and its access boundary."""

import asyncio
import os
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from application.purchase_history import PurchaseHistoryQuery
from backend.app.config import settings
from odoo_adapter.product_history_reader import OdooProductHistoryReader

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_ODOO_HISTORY_LIVE") != "true",
        reason="Set RUN_ODOO_HISTORY_LIVE=true with a seeded pdss_history_gen database.",
    ),
]


def _post(key, model, method, body):
    return httpx.post(
        f"{settings.odoo_base_url.rstrip('/')}/json/2/{model}/{method}",
        headers={"Authorization": f"Bearer {key}", "X-Odoo-Database": settings.odoo_database},
        json=body,
        timeout=30,
    )


def test_live_export_reads_generated_history_through_the_restricted_user():
    end = datetime.now(UTC).replace(microsecond=0)
    reader = OdooProductHistoryReader(
        base_url=settings.odoo_base_url,
        database=settings.odoo_database,
        api_key=settings.odoo_t7s_api_key.get_secret_value(),
    )
    query = PurchaseHistoryQuery(
        "odoo:res.company:1", "odoo:product.product:1", end - timedelta(days=180), end
    )
    snapshot = asyncio.run(reader.read_purchase_history(query))
    assert len(snapshot.lines) >= 100
    assert any(len(x.receipts) > 1 for x in snapshot.lines)
    assert all(x.confirmed_at <= x.expected_at for x in snapshot.lines)


def test_live_history_user_cannot_read_stock_or_write_and_quotation_user_cannot_export():
    history_key = settings.odoo_t7s_api_key.get_secret_value()
    for model in ("stock.move", "stock.picking", "stock.move.line"):
        response = _post(history_key, model, "search_read", {"domain": [], "limit": 1})
        assert response.status_code == 403, model
    rights = {"operation": "write", "raise_exception": False}
    write = _post(history_key, "purchase.order", "check_access_rights", rights)
    assert write.json() is False
    too_wide = _post(
        history_key,
        "procurement.product.history.export",
        "read_product_history",
        {"company_id": 1, "product_id": 1, "date_from": "2025-01-01 00:00:00",
         "date_to": "2026-02-01 00:00:00", "limit": 10},
    )  # fmt: skip
    assert too_wide.status_code == 422
    quotation = _post(
        settings.odoo_api_key.get_secret_value(),
        "procurement.product.history.export",
        "read_product_history",
        {"company_id": 1, "product_id": 1, "date_from": "2026-01-01 00:00:00",
         "date_to": "2026-02-01 00:00:00", "limit": 10},
    )  # fmt: skip
    assert quotation.status_code == 403
