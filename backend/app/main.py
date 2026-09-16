"""Minimal FastAPI application used to prove the backend boundary in T0."""

from fastapi import FastAPI

from backend.app.config import settings
from backend.app.schemas import HealthResponse

app = FastAPI(title="Procurement Decision Support API", version="v1")


@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
def get_health() -> HealthResponse:
    """Return a stable status response without business or infrastructure access."""

    return HealthResponse(
        status="ok",
        service=settings.service_name,
        api_version="v1",
    )
