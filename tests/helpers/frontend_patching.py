"""Drive frontend state in tests: patch API client functions or the HTTP transport,
and run Reflex event handlers."""

import asyncio

# The state mixins call these as ``<module>.<name>``, so one patch per name covers them all.
MODULES = {
    "submit_planning_request": "frontend.api.cases",
    "fetch_planning_case": "frontend.api.cases",
    "fetch_planning_pdf": "frontend.api.documents",
    "fetch_quotation_groups": "frontend.api.odoo_history",
    "fetch_odoo_history": "frontend.api.odoo_history",
    "fetch_supplier_overview": "frontend.api.suppliers",
    "fetch_library": "frontend.api.library",
    "fetch_scenarios": "frontend.api.library",
}


def patch_client(monkeypatch, name, replacement):
    """Replace one API client function where the state mixins resolve it."""
    monkeypatch.setattr(f"{MODULES[name]}.{name}", replacement)


def use_transport(monkeypatch, transport):
    """Send every frontend API request through ``transport`` (ASGI app or mock)."""
    monkeypatch.setattr("frontend.api.http.transport", transport)


def consume(state, handler, *args):
    """Run a Reflex event handler to completion; returns every update it yielded."""

    async def run():
        """Collect every update the handler yields."""
        return [event async for event in handler.fn(state, *args)]

    return asyncio.run(run())


def open_case(state, case_id):
    """Updates of loading stored case ``case_id`` with the loader behind the
    ``/planning?case_id=…`` bookmark (``load_bookmark`` adds only routing around it)."""
    return state._load_case({"case_id": case_id})


async def event(state, handler, *args):
    """Await a Reflex event handler, checking it shows loading until it finishes."""
    async for update in handler.fn(state, *args):
        if update is None:
            assert state.is_loading
    assert not state.is_loading
