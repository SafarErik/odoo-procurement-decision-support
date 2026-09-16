"""Tests for the frontend-to-backend configuration boundary."""

from frontend.config import FrontendSettings
from frontend.rxconfig import config as reflex_config


def test_health_url_uses_configured_backend_base_url() -> None:
    """The frontend consumes the documented API endpoint through configuration."""

    settings = FrontendSettings(_env_file=None, backend_base_url="http://api.example.test/")

    assert settings.health_url == "http://api.example.test/api/v1/health"


def test_reflex_runtime_does_not_conflict_with_fastapi() -> None:
    """Reflex uses a separate state-backend port and imports the flat app module."""

    assert reflex_config.backend_port == 8001
    assert reflex_config.module == "app"
