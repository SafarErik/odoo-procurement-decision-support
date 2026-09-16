"""Fast tests for the frontend-to-backend boundary."""

import asyncio

import httpx

from frontend.config import FrontendSettings
from frontend.health_client import fetch_health_display
from frontend.rxconfig import config as reflex_config


def test_health_url_uses_configured_backend_base_url() -> None:
    """The frontend consumes the documented API endpoint through configuration."""

    settings = FrontendSettings(_env_file=None, backend_base_url="http://api.example.test/")

    assert settings.health_url == "http://api.example.test/api/v1/health"


def test_reflex_runtime_does_not_conflict_with_fastapi() -> None:
    """Reflex uses a separate state-backend port and imports the flat app module."""

    assert reflex_config.backend_port == 8001
    assert reflex_config.module == "app"


def test_health_response_is_mapped_for_display() -> None:
    """A valid backend response becomes the expected presentation state."""

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url == "http://api.example.test/api/v1/health"
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "service": "procurement-decision-support-api",
                "api_version": "v1",
            },
        )

    display = asyncio.run(
        fetch_health_display(
            "http://api.example.test/api/v1/health",
            transport=httpx.MockTransport(respond),
        )
    )

    assert display.backend_status == "ok"
    assert display.detail == "procurement-decision-support-api (v1)"
    assert display.error_message == ""


def test_connection_failure_is_mapped_to_unavailable() -> None:
    """A connection error becomes an actionable unavailable state."""

    def refuse_connection(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    display = asyncio.run(
        fetch_health_display(
            "http://api.example.test/api/v1/health",
            transport=httpx.MockTransport(refuse_connection),
        )
    )

    assert display.backend_status == "Unavailable"
    assert display.detail == ""
    assert display.error_message == "Could not reach the backend: connection refused"


def test_invalid_health_response_is_mapped_to_unavailable() -> None:
    """An incomplete health payload does not escape into the Reflex event."""

    display = asyncio.run(
        fetch_health_display(
            "http://api.example.test/api/v1/health",
            transport=httpx.MockTransport(
                lambda _request: httpx.Response(200, json={"status": "ok"})
            ),
        )
    )

    assert display.backend_status == "Unavailable"
    assert display.detail == ""
    assert display.error_message.startswith("Could not reach the backend:")
