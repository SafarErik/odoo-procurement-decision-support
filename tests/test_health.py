"""Tests for the stable API health boundary."""

from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app


def test_health_returns_stable_status() -> None:
    """The health route has no external runtime dependency."""

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": settings.service_name,
        "api_version": "v1",
    }
