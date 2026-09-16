"""Tests for the frontend-to-backend configuration boundary."""

from frontend.config import FrontendSettings


def test_health_url_uses_configured_backend_base_url() -> None:
    """The frontend consumes the documented API endpoint through configuration."""

    settings = FrontendSettings(_env_file=None, backend_base_url="http://api.example.test/")

    assert settings.health_url == "http://api.example.test/api/v1/health"
