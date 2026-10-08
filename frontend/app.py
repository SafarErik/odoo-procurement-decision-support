"""Reflex composition root; page components and HTTP state live in focused modules."""

import reflex as rx

from frontend.planning.page import planning_page
from frontend.planning.state import PlanningState  # noqa: F401 - existing Python entry point
from frontend.rfq_page import RfqState, index

app = rx.App()
app.add_page(index, route="/", on_load=RfqState.refresh_rfqs, title="Open RFQs")
app.add_page(planning_page, route="/planning", title="Procurement cockpit")
