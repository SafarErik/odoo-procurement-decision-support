"""Fast contract tests for the read-only Odoo RFQ adapter."""

import asyncio
import json
from decimal import Decimal

import httpx
import pytest

from application.rfqs import ProcurementDataResponseError, ProcurementDataUnavailable
from odoo_adapter.rfq_reader import OdooRfqReader


def test_odoo_reader_requests_and_maps_open_rfqs() -> None:
    """The adapter uses the validated JSON-2 contract and neutral mapping."""

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url == "http://odoo.example.test/json/2/purchase.order/search_read"
        assert request.headers["authorization"] == "Bearer test-api-key"
        assert request.headers["x-odoo-database"] == "procurement_poc"
        payload = json.loads(request.content)
        assert payload == {
            "domain": [["state", "in", ["draft", "sent", "to approve"]]],
            "fields": [
                "id",
                "name",
                "partner_id",
                "date_order",
                "state",
                "amount_total",
                "currency_id",
            ],
            "limit": 20,
            "order": "date_order desc, id desc",
        }
        return httpx.Response(
            200,
            json=[
                {
                    "id": 42,
                    "name": "P00042",
                    "partner_id": [7, "Danube Industrial Supplies"],
                    "date_order": "2026-09-16 10:30:00",
                    "state": "to approve",
                    "amount_total": 125000.50,
                    "currency_id": [1, "HUF"],
                }
            ],
        )

    reader = OdooRfqReader(
        base_url="http://odoo.example.test/",
        database="procurement_poc",
        api_key="test-api-key",
        transport=httpx.MockTransport(respond),
    )

    items = asyncio.run(reader.list_open_rfqs(20))

    assert len(items) == 1
    assert items[0].source_id == "42"
    assert items[0].reference == "P00042"
    assert items[0].vendor_name == "Danube Industrial Supplies"
    assert items[0].order_date.isoformat() == "2026-09-16T10:30:00+00:00"
    assert items[0].status == "awaiting_approval"
    assert items[0].total.amount == Decimal("125000.5")
    assert items[0].total.currency == "HUF"


def test_odoo_reader_rejects_missing_configuration() -> None:
    """An absent API key is reported as source unavailability."""

    reader = OdooRfqReader(
        base_url="http://odoo.example.test",
        database="procurement_poc",
        api_key="",
    )

    with pytest.raises(ProcurementDataUnavailable):
        asyncio.run(reader.list_open_rfqs(20))


def test_odoo_reader_translates_upstream_http_errors() -> None:
    """Authentication and permission failures do not leak Odoo payloads."""

    reader = OdooRfqReader(
        base_url="http://odoo.example.test",
        database="procurement_poc",
        api_key="invalid-key",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(401, json={"debug": "sensitive traceback"})
        ),
    )

    with pytest.raises(ProcurementDataResponseError, match="HTTP 401") as raised:
        asyncio.run(reader.list_open_rfqs(20))

    assert "sensitive traceback" not in str(raised.value)


def test_odoo_reader_rejects_invalid_many2one_payload() -> None:
    """Malformed upstream relationships fail instead of producing misleading rows."""

    reader = OdooRfqReader(
        base_url="http://odoo.example.test",
        database="procurement_poc",
        api_key="test-key",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "name": "P00001",
                        "partner_id": False,
                        "date_order": "2026-09-16 10:30:00",
                        "state": "draft",
                        "amount_total": 1,
                        "currency_id": [1, "HUF"],
                    }
                ],
            )
        ),
    )

    with pytest.raises(ProcurementDataResponseError, match="invalid RFQ payload"):
        asyncio.run(reader.list_open_rfqs(20))
