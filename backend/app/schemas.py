"""Stable HTTP response schemas owned by the API boundary."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Status response for service discovery and lightweight integration checks."""

    status: Literal["ok"]
    service: str
    api_version: str
