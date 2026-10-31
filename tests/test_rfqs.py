"""Fast API tests for the RFQ listing use case."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from application.rfqs import (
    Money,
    ProcurementDataResponseError,
    ProcurementDataUnavailable,
    RfqSummary,
)
from backend.app.config import settings
from backend.app.dependencies import get_rfq_reader
from backend.app.main import app

TOKEN = "rfq-route-test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture(autouse=True)
def service_token(monkeypatch):
    monkeypatch.setattr(settings, "api_service_token", SecretStr(TOKEN))


class FakeRfqReader:
    """Controllable application-port implementation for route tests."""

    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.requested_limit: int | None = None

    async def list_open_rfqs(self, limit: int) -> list[RfqSummary]:
        self.requested_limit = limit
        if self.error is not None:
            raise self.error
        return [
            RfqSummary(
                source_id="42",
                reference="P00042",
                vendor_name="Danube Industrial Supplies",
                order_date=datetime(2026, 9, 16, 10, 30, tzinfo=UTC),
                status="draft",
                total=Money(amount=Decimal("125000.50"), currency="HUF"),
            )
        ]


def test_rfq_route_returns_neutral_contract() -> None:
    """The route exposes the application DTO rather than a raw Odoo payload."""

    reader = FakeRfqReader()
    app.dependency_overrides[get_rfq_reader] = lambda: reader
    try:
        response = TestClient(app).get("/api/v1/procurement/rfqs?limit=10", headers=AUTH)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert reader.requested_limit == 10
    assert payload["count"] == 1
    assert payload["items"] == [
        {
            "source_id": "42",
            "reference": "P00042",
            "vendor_name": "Danube Industrial Supplies",
            "order_date": "2026-09-16T10:30:00Z",
            "status": "draft",
            "total": {"amount": "125000.50", "currency": "HUF"},
        }
    ]
    assert payload["retrieved_at"].endswith("Z")


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (ProcurementDataUnavailable("offline"), 503, "odoo_unavailable"),
        (ProcurementDataResponseError("denied"), 502, "odoo_response_error"),
    ],
)
def test_rfq_route_translates_source_errors(
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    """Stable API errors hide infrastructure details from the frontend."""

    app.dependency_overrides[get_rfq_reader] = lambda: FakeRfqReader(error=error)
    try:
        response = TestClient(app).get("/api/v1/procurement/rfqs", headers=AUTH)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == expected_status
    assert response.json()["detail"]["code"] == expected_code
    assert "offline" not in response.text
    assert "denied" not in response.text


def test_rfq_route_rejects_out_of_range_limit() -> None:
    """The public endpoint enforces the documented request bound."""

    app.dependency_overrides[get_rfq_reader] = lambda: FakeRfqReader()
    try:
        response = TestClient(app).get("/api/v1/procurement/rfqs?limit=51", headers=AUTH)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_rfq_route_requires_the_service_token() -> None:
    """Like every other data route, the RFQ list needs the trusted-caller bearer token."""

    reader = FakeRfqReader()
    app.dependency_overrides[get_rfq_reader] = lambda: reader
    try:
        response = TestClient(app).get("/api/v1/procurement/rfqs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert reader.requested_limit is None
