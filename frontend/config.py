"""Frontend runtime configuration kept outside Reflex components."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FrontendSettings(BaseSettings):
    """Settings for HTTP communication with the backend API."""

    backend_base_url: str = "http://127.0.0.1:8000"
    t12_trusted_caller_token: SecretStr = SecretStr("")

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def rfqs_url(self) -> str:
        """Return the documented open-RFQ endpoint."""

        return f"{self.backend_base_url.rstrip('/')}/api/v1/procurement/rfqs"

    @property
    def planning_cases_url(self) -> str:
        return f"{self.backend_base_url.rstrip('/')}/api/v2/procurement/planning-cases"


settings = FrontendSettings()
