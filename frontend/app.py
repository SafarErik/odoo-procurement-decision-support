"""Reflex composition root; page components and HTTP state live in focused modules."""

import reflex as rx

from frontend.planning.home import home_page
from frontend.planning.library import library_page
from frontend.planning.page import planning_page
from frontend.planning.rfqs import rfqs_page
from frontend.planning.state import PlanningState

app = rx.App()
app.add_page(
    home_page, route="/", title="Procurement workspace", on_load=PlanningState.home_on_load
)
app.add_page(
    library_page, route="/cases", title="Procurement cases", on_load=PlanningState.library_on_load
)
app.add_page(rfqs_page, route="/rfqs", title="Open RFQs", on_load=PlanningState.rfqs_on_load)
app.add_page(
    planning_page, route="/planning", title="Procurement case", on_load=PlanningState.load_bookmark
)
