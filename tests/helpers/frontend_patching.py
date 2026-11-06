"""Drive frontend state in tests: patch HTTP clients where the state mixins resolve them,
and run Reflex event handlers."""

import asyncio

MODULES = {
    "submit_planning_request": ("frontend.planning.state_base",),
    "fetch_planning_case": ("frontend.planning.state_case", "frontend.planning.state_decision"),
    "fetch_planning_pdf": ("frontend.planning.state_decision",),
    "fetch_quotation_groups": ("frontend.planning.state_creation",),
    "fetch_odoo_history": ("frontend.planning.state_creation",),
    "fetch_supplier_overview": ("frontend.planning.state_case",),
    "fetch_library": ("frontend.planning.state_library",),
}


def patch_client(monkeypatch, name, replacement):
    for module in MODULES[name]:
        monkeypatch.setattr(f"{module}.{name}", replacement)


def consume(state, handler, *args):
    """Run a Reflex event handler to completion; returns every update it yielded."""

    async def run():
        return [event async for event in handler.fn(state, *args)]

    return asyncio.run(run())


async def event(state, handler, *args):
    """Await a Reflex event handler, checking it shows loading until it finishes."""
    async for update in handler.fn(state, *args):
        if update is None:
            assert state.is_loading
    assert not state.is_loading
