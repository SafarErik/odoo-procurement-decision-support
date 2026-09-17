"""Integration tests for services started by the runtime workflow."""

import os

import httpx
import pytest

pytestmark = pytest.mark.integration


def test_running_fastapi_health_contract() -> None:
    """The separately running FastAPI process exposes its stable contract."""

    base_url = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
    response = httpx.get(f"{base_url.rstrip('/')}/api/v1/health", timeout=10.0)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "procurement-decision-support-api",
        "api_version": "v1",
    }


def test_running_fastapi_decision_contract() -> None:
    """The served API evaluates canonical input and safely rejects invalid input."""

    base_url = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
    endpoint = f"{base_url.rstrip('/')}/api/v1/procurement/decisions/evaluate"
    payload = {
        "requirement": {
            "requirement_id": "REQ-100",
            "requested_quantity": "100",
        },
        "offers": [
            {
                "offer_id": "Offer A",
                "supplier_id": "Supplier A",
                "unit_price": "10",
                "lead_time_days": "10",
                "minimum_order_quantity": "50",
            },
            {
                "offer_id": "Offer B",
                "supplier_id": "Supplier B",
                "unit_price": "12",
                "lead_time_days": "5",
                "minimum_order_quantity": "100",
            },
            {
                "offer_id": "Offer C",
                "supplier_id": "Supplier C",
                "unit_price": "9",
                "lead_time_days": "8",
                "minimum_order_quantity": "150",
            },
        ],
        "profile": {
            "name": "cost-focused",
            "unit_price_weight": "0.7",
            "lead_time_weight": "0.3",
        },
    }

    response = httpx.post(endpoint, json=payload, timeout=10.0)

    assert response.status_code == 200
    assert response.json()["recommended_offer"]["offer_id"] == "Offer A"
    assert [item["offer_id"] for item in response.json()["ranked_offers"]] == [
        "Offer A",
        "Offer B",
    ]
    assert [item["offer_id"] for item in response.json()["excluded_offers"]] == ["Offer C"]

    payload["requirement"]["requested_quantity"] = "0"
    invalid_response = httpx.post(endpoint, json=payload, timeout=10.0)
    assert invalid_response.status_code == 422
    assert invalid_response.json()["detail"]["code"] == "invalid_decision_input"


def test_running_odoo_http_service() -> None:
    """The Compose-managed Odoo service responds through its HTTP boundary."""

    base_url = os.getenv("ODOO_BASE_URL", "http://127.0.0.1:8069")
    response = httpx.get(
        f"{base_url.rstrip('/')}/web/database/selector",
        follow_redirects=True,
        timeout=20.0,
    )

    assert response.status_code == 200
    assert "odoo" in response.text.lower()
