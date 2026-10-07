"""Fast tests for the frontend-to-backend boundary."""

from frontend.rxconfig import config as reflex_config


def test_reflex_runtime_does_not_conflict_with_fastapi() -> None:
    """Reflex uses a separate state-backend port and imports the flat app module."""

    assert reflex_config.backend_port == 8001
    assert reflex_config.module == "app"
