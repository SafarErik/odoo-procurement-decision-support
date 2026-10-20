"""Behavioral checks for guided preparation, bounded home lists and stored-plan presentation."""

import asyncio
from copy import deepcopy

import pytest

from frontend.i18n import tr
from frontend.odoo_history_client import quotation_rows
from frontend.planning.state import PlanningState
from frontend.planning_client import _map_case
from tests.frontend_patching import patch_client
from tests.test_creation_review import prepared_state as prepared_state
from tests.test_odoo_purchase_history import configured as configured
from tests.test_odoo_purchase_history import history as history
from tests.test_t16_stored_planning import stored_cases as stored_cases


def test_draft_survives_steps_language_and_reopened_supplier(prepared_state):
    state, form = prepared_state
    state.lang = "hu"
    name = next(k for k in form if k.endswith("_capacity"))
    PlanningState.update_creation_field.fn(state, name, "137")
    PlanningState.go_creation_step.fn(state, 2)
    assert state.creation_step == 2
    PlanningState.go_creation_step.fn(state, 1)
    PlanningState.set_language.fn(state, "en")
    assert state.creation_values[name] == "137"
    assert state.creation_suggestions[name] != "137"
    PlanningState.go_creation_step.fn(state, 2)
    supplier = state.odoo_offers[0]["supplier"]
    PlanningState.toggle_supplier_terms.fn(state, supplier)
    PlanningState.toggle_supplier_terms.fn(state, supplier)
    assert state.creation_values[name] == "137" and supplier not in state.expanded_suppliers


def test_invalid_demand_keeps_user_at_the_demand_step(prepared_state):
    state, _ = prepared_state
    PlanningState.update_creation_field.fn(state, "odoo_quantity", "0")
    PlanningState.go_creation_step.fn(state, 2)
    assert state.creation_step == 1 and "odoo-quantity" in state.creation_errors
    assert not state._review_payload and not state.has_pending


def test_supplier_error_expands_its_section_without_creating_a_request(prepared_state):
    state, form = prepared_state
    supplier = state.odoo_offers[-1]["supplier"]
    form[supplier + "_price_min"] = "99"
    form[supplier + "_price_max"] = "1"
    PlanningState.review_odoo.fn(state, form)
    assert state.creation_step == 2 and supplier in state.expanded_suppliers
    assert supplier + "_price_max" in state.creation_errors
    assert not state._review_payload and not state._pending


def test_review_and_edit_keep_the_values_used_for_the_review(prepared_state):
    state, form = prepared_state
    state.creation_step = 2
    name = next(k for k in form if k.endswith("_capacity"))
    form[name] = "117"
    PlanningState.advance_creation.fn(state, form)
    assert state.creation_step == 3 and state.creation_values[name] == "117"
    frozen = deepcopy(state._review_payload)
    PlanningState.update_creation_field.fn(state, name, "18")
    assert state._review_payload == frozen and state.creation_values[name] == "117"
    PlanningState.set_language.fn(state, "hu")
    assert state._review_payload == frozen and state.creation_step == 3
    PlanningState.edit_creation_terms.fn(state)
    assert state.creation_step == 1 and state.creation_values[name] == "117"
    assert not state._review_payload


def test_group_change_stay_preserves_draft_then_discard_clears_it(prepared_state):
    state, _ = prepared_state
    state.quotation_groups.append({"value": "502", "selectable": "yes"})
    values = deepcopy(state.creation_values)
    PlanningState.select_quotation_group.fn(state, "502")
    assert state.navigation_open and state.selected_group == "501"
    PlanningState.stay_navigation.fn(state)
    assert state.creation_values == values and state.odoo_ready
    PlanningState.prepare_odoo_history.fn(state, "502")
    assert state.navigation_open and state.selected_group == "501"
    PlanningState.discard_navigation.fn(state)
    assert state.selected_group == "502" and not state.creation_values
    assert not state.odoo_ready and not state._review_payload


def test_steps_cannot_bypass_review_or_pending_request(prepared_state):
    state, _ = prepared_state
    PlanningState.go_creation_step.fn(state, 3)
    assert state.creation_step == 1
    original = deepcopy(state.creation_values)
    state.has_pending = True
    PlanningState.go_creation_step.fn(state, 0)
    PlanningState.update_creation_field.fn(state, "odoo_quantity", "3")
    assert state.creation_step == 1 and state.creation_values == original


def test_home_queries_are_bounded_independent_and_do_not_change_library_filters(monkeypatch):
    state = PlanningState(_reflex_internal_init=True)
    state.library_status, state.library_search = "approved", "keep me"
    calls = []

    async def fetch(url, token, params, **kwargs):
        calls.append(dict(params))
        if params["status"] == "draft":
            return None, "Unavailable"
        return {"raw": [], "items": [], "next_cursor": "more"}, ""

    patch_client(monkeypatch, "fetch_library", fetch)

    async def run():
        return [event async for event in PlanningState.home_on_load.fn(state)]

    asyncio.run(run())
    assert calls == [
        {"origin": "all", "status": "draft", "limit": 5},
        {"origin": "all", "status": "all", "limit": 5},
    ]
    assert state.home_pending_error == "Unavailable" and state.home_recent_error == ""
    assert not state.home_loading
    assert state.library_status == "approved" and state.library_search == "keep me"


def test_home_does_not_issue_reads_while_a_save_is_pending(monkeypatch):
    state = PlanningState(_reflex_internal_init=True)
    state.has_pending = True
    state._pending_route = "/rfqs"

    async def forbidden(*args, **kwargs):
        pytest.fail("Pending save must be resolved before home reads.")

    patch_client(monkeypatch, "fetch_library", forbidden)

    async def run():
        return [event async for event in PlanningState.home_on_load.fn(state)]

    events = asyncio.run(run())
    assert '"/rfqs"' in str(events[0])


def test_quote_details_preserve_individual_source_references_and_quantities():
    group = {
        "currency": "HUF",
        "quotations": [
            {
                "reference": "P00042",
                "supplier_name": "Long supplier",
                "state": "sent",
                "lines": [{"quantity": "12", "unit_price": "42.50", "uom_name": "Units"}],
            },
            {
                "reference": "P00043",
                "supplier_name": "Second",
                "state": "draft",
                "lines": [{"quantity": "99", "unit_price": "50", "uom_name": "Units"}],
            },
        ],
    }
    rows = quotation_rows(group, "hu")
    assert [r["reference"] for r in rows] == ["P00042", "P00043"]
    assert rows[0]["quantity"] != rows[1]["quantity"]
    assert rows[0]["status"] == "Elküldve"


def test_selected_chart_only_highlights_an_explicit_stored_selection(stored_cases):
    base = stored_cases[1]
    state = PlanningState(_reflex_internal_init=True)
    state._show(_map_case(base, base["case_id"], "hu"))
    assert not state.chart_selected
    PlanningState.choose_final_plan.fn(state, "Alternative 1")
    point = state.chart_selected[0]
    assert point["cost"] == float(state.selected_plan["cost_number"])
    assert point["exposure"] == float(state.selected_plan["exposure_number"])
    assert not state.has_pending and not state.details["final_outcome"]


def test_closed_case_next_action_does_not_request_a_new_selection():
    state = PlanningState(_reflex_internal_init=True)
    state.lang = "hu"
    state.details = {"parent_id": "Base case", "final_outcome": "No-award"}
    assert state.next_action_text == tr("case_next_closed", "hu")
    state.details = {"parent_id": "parent", "final_outcome": ""}
    assert state.next_action_text == tr("case_next_scenario", "hu")
