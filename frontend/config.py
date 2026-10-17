"""Frontend runtime configuration kept outside Reflex components."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FrontendSettings(BaseSettings):
    """Settings for HTTP communication with the backend API."""

    backend_base_url: str = "http://127.0.0.1:8000"
    api_service_token: SecretStr = SecretStr("")

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

    @property
    def controlled_demo_file(self) -> Path:
        """Reuse the existing offline demo; browsers cannot choose files or models."""
        return PROJECT_ROOT / ".artifacts/t15-demo/create-request.json"

    @property
    def controlled_odoo_file(self) -> Path:
        # ponytail: one prepared comparison; add discovery with matched-model support.
        return PROJECT_ROOT / ".artifacts/t15-odoo-demo/create-request.json"


settings = FrontendSettings()
