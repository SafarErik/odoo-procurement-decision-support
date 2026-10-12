"""Draft navigation and uncertain intent are distinct frontend trust boundaries."""

import asyncio
from copy import deepcopy
from uuid import uuid4

import pytest
import reflex as rx
from reflex.istate.data import RouterData

from frontend.planning.state import PlanningState


def state_at(path="/planning"):
    root = rx.State(_reflex_internal_init=True)
    state = root.get_substate(PlanningState.get_full_name().split("."))
    root.router = RouterData.from_router_data({"asPath": path})
    return root, state


@pytest.mark.parametrize("dirty", ["creation_dirty", "scenario_dirty"])
def test_stay_preserves_draft_discard_clears_and_navigates(dirty):
    _, state = state_at()
    setattr(state, dirty, True)
    state.demo_ready = True
    state._demo_payload = {"quantity": 10}
    state.stress_quantity = "25"
    assert state.open_library() is None
    assert state.navigation_open
    state.stay_navigation()
    assert not state.navigation_open and getattr(state, dirty)
    assert state._demo_payload == {"quantity": 10} and state.stress_quantity == "25"
    state.open_library()
    event = state.discard_navigation()
    assert event.args[0][1]._js_expr == '"/cases"'
    assert not state.creation_dirty and not state.scenario_dirty
    assert not state.demo_ready and not state._demo_payload and not state.stress_quantity


def test_dirty_view_stays_controlled_and_is_bookmarkable_after_discard():
    _, state = state_at()
    identity = str(uuid4())
    state.has_case = True
    state.details = {"case_id": identity}
    state.view = "whatif"
    state.scenario_dirty = True
    state.change_view("audit")
    assert state.view == "whatif" and state.navigation_open
    state.stay_navigation()
    state.change_view("audit")
    event = state.discard_navigation()
    assert state.view == "audit"
    assert state.navigation_focus == "view-audit"
    assert identity in event.args[0][1]._js_expr and "view=audit" in event.args[0][1]._js_expr


def test_pending_all_route_and_view_entries_preserve_original_context():
    async def run():
        root, state = state_at()
        state.has_pending = True
        state._pending_route = "/practice"
        state._pending = {"key": "exact", "payload": {"quantity": 10}, "url": "http://test"}
        state.recovery_json = "exact recovery"
        state.input_mode = "create"
        state.view = "whatif"
        pending = deepcopy(state._pending)
        for path in ("/", "/cases", "/planning?case_id=bad&view=audit", "/practice"):
            root.router = RouterData.from_router_data({"asPath": path})
            handler = (
                state.rfq_on_load
                if path == "/"
                else (
                    state.library_on_load
                    if path == "/cases"
                    else (state.practice_on_load if path == "/practice" else state.load_bookmark)
                )
            )
            events = [event async for event in handler()]
            if path != "/practice":
                assert events[0].args[0][1]._js_expr == '"/practice"'
            state.change_view("audit")
            state.change_input_mode("odoo")
            state.choose_practice_task("compare-plans")
            state.navigate_global("rfqs")
            state.navigation_open = True
            assert state.discard_navigation() is None
            assert state._pending == pending and state.recovery_json == "exact recovery"
            assert state.view == "whatif" and state.input_mode == "create"

    asyncio.run(run())


def test_invalid_route_clears_previous_case_without_http(monkeypatch):
    async def run():
        root, state = state_at("/planning?case_id=bad&view=invalid")
        state.has_case = True
        state.details = {"case_id": str(uuid4())}
        async for _ in state.load_bookmark():
            pass
        assert not state.has_case and not state.details and state.error_message
        assert state.open_saved_case("bad&view=audit") is None
        assert state.navigate_global("https://invalid") is None

    asyncio.run(run())
