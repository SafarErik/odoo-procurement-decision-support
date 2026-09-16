"""Minimal Reflex UI proving presentation-to-API communication."""

import httpx
import reflex as rx
from config import settings


class HealthState(rx.State):
    """Presentation state for the backend status check only."""

    backend_status: str = "Not checked"
    detail: str = ""
    error_message: str = ""

    @rx.event
    async def refresh_health(self) -> None:
        """Request the documented health endpoint and render a concise result."""

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(settings.health_url)
                response.raise_for_status()
            payload = response.json()
            self.backend_status = payload["status"]
            self.detail = f"{payload['service']} ({payload['api_version']})"
            self.error_message = ""
        except (httpx.HTTPError, KeyError, TypeError) as error:
            self.backend_status = "Unavailable"
            self.detail = ""
            self.error_message = f"Could not reach the backend: {error}"


def index() -> rx.Component:
    """Render the intentionally minimal presentation boundary check."""

    return rx.container(
        rx.vstack(
            rx.heading("Procurement Decision Support", size="7"),
            rx.text("T0 frontend-to-backend connectivity check."),
            rx.text("Backend status: ", HealthState.backend_status),
            rx.cond(HealthState.detail != "", rx.text(HealthState.detail)),
            rx.cond(
                HealthState.error_message != "",
                rx.text(HealthState.error_message, color="crimson"),
            ),
            rx.button("Check backend", on_click=HealthState.refresh_health),
            spacing="4",
        ),
        padding_top="5em",
    )


app = rx.App()
app.add_page(index, route="/", on_load=HealthState.refresh_health)
