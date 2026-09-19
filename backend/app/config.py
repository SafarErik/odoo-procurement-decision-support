"""Configuration for the minimal API service."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or the local .env file."""

    service_name: str = "procurement-decision-support-api"
    odoo_base_url: str = ""
    odoo_database: str = ""
    odoo_api_key: SecretStr = SecretStr("")
    odoo_request_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    run_t6_live_contracts: bool = False
    run_t7_live_contracts: bool = False

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
