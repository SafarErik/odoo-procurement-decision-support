"""Configuration for the minimal API service."""

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or the local .env file."""

    service_name: str = "procurement-decision-support-api"
    odoo_base_url: str = ""
    odoo_database: str = ""
    odoo_api_key: SecretStr = SecretStr("")
    odoo_t7s_api_key: SecretStr = SecretStr("")
    decision_database_url: SecretStr = SecretStr("")
    t12_trusted_caller_token: SecretStr = SecretStr("")
    t15_trusted_model_directory: Path | None = None
    planning_library_company_id: str = ""
    odoo_request_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    run_t6_live_contracts: bool = False
    run_t7s_live_contracts: bool = False
    run_t7_live_contracts: bool = False

    @field_validator("t15_trusted_model_directory", mode="before")
    @classmethod
    def optional_model_directory(cls, value):
        return None if value == "" else value

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
