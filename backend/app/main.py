"""FastAPI composition of the procurement planning HTTP API."""

from fastapi import FastAPI

from backend.app.config import settings
from backend.app.routes.planning_cases import router as planning_cases_router
from backend.app.routes.quotation_groups import router as quotation_groups_router
from backend.app.routes.rfqs import router as rfqs_router
from backend.app.schemas import HealthResponse

app = FastAPI(title="Procurement Decision Support API", version="v1")
app.include_router(rfqs_router)
app.include_router(planning_cases_router)
app.include_router(quotation_groups_router)


@app.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
def get_health() -> HealthResponse:
    """Return a stable status response without business or infrastructure access."""

    return HealthResponse(
        status="ok",
        service=settings.service_name,
        api_version="v1",
    )
