"""Shared strict request models and the PoC trusted-caller gate."""

from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict

from backend.app.config import settings

_bearer = HTTPBearer(auto_error=False)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def explicit_utc_text(value: object) -> object:
    if not isinstance(value, str) or not value.endswith(("Z", "+00:00")):
        raise ValueError("An explicit UTC timestamp string is required.")
    return value


def require_trusted_caller(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    """A shared PoC service secret proves possession only, never buyer identity."""
    configured = settings.api_service_token.get_secret_value()
    if not configured or not configured.isascii():
        raise HTTPException(
            503,
            detail={
                "code": "trusted_caller_unconfigured",
                "message": "The trusted-caller gate is unavailable.",
            },
        )
    if (
        credentials is None
        or not credentials.credentials.isascii()
        or not compare_digest(credentials.credentials, configured)
    ):
        raise HTTPException(
            401,
            detail={"code": "unauthorized", "message": "A valid bearer token is required."},
            headers={"WWW-Authenticate": "Bearer"},
        )
