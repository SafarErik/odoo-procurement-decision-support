"""HTTP health client and presentation mapping for the Reflex frontend."""

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class HealthDisplay:
    """Frontend-ready representation of the backend health result."""

    backend_status: str
    detail: str
    error_message: str


async def fetch_health_display(
    health_url: str,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> HealthDisplay:
    """Fetch the health endpoint and map success or failure for display."""

    try:
        async with httpx.AsyncClient(timeout=5.0, transport=transport) as client:
            response = await client.get(health_url)
            response.raise_for_status()
        payload = response.json()
        return HealthDisplay(
            backend_status=payload["status"],
            detail=f"{payload['service']} ({payload['api_version']})",
            error_message="",
        )
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
        return HealthDisplay(
            backend_status="Unavailable",
            detail="",
            error_message=f"Could not reach the backend: {error}",
        )
