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


def test_running_fastapi_planning_routes_require_service_token() -> None:
    """The served planning API is mounted and refuses callers without the service token."""

    base_url = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
    response = httpx.get(f"{base_url.rstrip('/')}/api/v2/procurement/planning-cases", timeout=10.0)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "unauthorized"


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
