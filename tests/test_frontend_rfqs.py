"""Fast tests for the frontend RFQ presentation boundary."""

import asyncio

import httpx

from frontend.config import FrontendSettings
from frontend.rfq_client import fetch_rfq_dashboard


def test_rfq_url_uses_configured_backend_base_url() -> None:
    """The frontend constructs the documented procurement endpoint."""

    settings = FrontendSettings(_env_file=None, backend_base_url="http://api.example.test/")

    assert settings.rfqs_url == "http://api.example.test/api/v1/procurement/rfqs"


def test_rfq_response_is_mapped_for_display() -> None:
    """A valid neutral API response becomes frontend-ready ledger data."""

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url == "http://api.example.test/api/v1/procurement/rfqs?limit=20"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "source_id": "42",
                        "reference": "P00042",
                        "vendor_name": "Danube Industrial Supplies",
                        "order_date": "2026-09-16T10:30:00Z",
                        "status": "awaiting_approval",
                        "total": {"amount": "125000.50", "currency": "HUF"},
                    }
                ],
                "count": 1,
                "retrieved_at": "2026-09-16T11:45:00Z",
            },
        )

    result = asyncio.run(
        fetch_rfq_dashboard(
            "http://api.example.test/api/v1/procurement/rfqs",
            transport=httpx.MockTransport(respond),
        )
    )

    assert result.connected is True
    assert result.last_refreshed == "11:45 UTC"
    assert result.error_message == ""
    assert result.items[0].reference == "P00042"
    assert result.items[0].order_date == "16 Sep 2026"
    assert result.items[0].status_label == "Awaiting approval"
    assert result.items[0].total == "125,000.50 HUF"


def test_empty_rfq_response_is_a_successful_empty_ledger() -> None:
    """No open records is distinct from an unavailable Odoo connection."""

    result = asyncio.run(
        fetch_rfq_dashboard(
            "http://api.example.test/api/v1/procurement/rfqs",
            transport=httpx.MockTransport(
                lambda _request: httpx.Response(
                    200,
                    json={
                        "items": [],
                        "count": 0,
                        "retrieved_at": "2026-09-16T11:45:00Z",
                    },
                )
            ),
        )
    )

    assert result.connected is True
    assert result.items == ()
    assert result.error_message == ""


def test_invalid_or_unavailable_rfq_response_is_actionable() -> None:
    """Upstream failures produce a stable unavailable presentation state."""

    result = asyncio.run(
        fetch_rfq_dashboard(
            "http://api.example.test/api/v1/procurement/rfqs",
            transport=httpx.MockTransport(
                lambda _request: httpx.Response(200, json={"items": "invalid"})
            ),
        )
    )

    assert result.connected is False
    assert result.items == ()
    assert result.last_refreshed == "Not available"
    assert "Odoo data is unavailable" in result.error_message
