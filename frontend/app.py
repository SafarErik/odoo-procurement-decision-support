"""Minimal Reflex UI proving presentation-to-API communication."""

import reflex as rx
from config import settings
from health_client import fetch_health_display


class HealthState(rx.State):
    """Presentation state for the backend status check only."""

    backend_status: str = "Not checked"
    detail: str = ""
    error_message: str = ""

    @rx.event
    async def refresh_health(self) -> None:
        """Request the documented health endpoint and render a concise result."""

        display = await fetch_health_display(settings.health_url)
        self.backend_status = display.backend_status
        self.detail = display.detail
        self.error_message = display.error_message


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
