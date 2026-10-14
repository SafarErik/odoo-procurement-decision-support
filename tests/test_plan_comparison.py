"""Saved-value comparison and explicit selection; no duplicated optimization rules."""

from copy import deepcopy
from decimal import Decimal

import pytest

from frontend.planning.state import PlanningState
from frontend.planning_client import _map_case
from tests.test_t16_stored_planning import stored_cases as stored_cases


def test_selection_mirrors_saved_values_and_never_preselects_or_creates_intent(stored_cases):
    base = stored_cases[1]
    display = _map_case(base, base["case_id"])
    state = PlanningState(_reflex_internal_init=True)
    state._show(display)
    assert state.final_choice == "" and state.selected_plan == {} and not state._pending
    PlanningState.choose_final_plan.fn(state, "Alternative 1")
    assert state.selected_plan == display.plans[1]
    selected = base["snapshot"]["result"]["alternatives"][0]
    assert state.selected_plan["index"] == "1"
    assert state.selected_plan["cost"] == f"{Decimal(selected['total_cost']):,f} EUR"
    assert state.selected_plan["premium_exact"] == (
        f"{selected['cost_premium']['numerator']}/{selected['cost_premium']['denominator']}"
    )
    mapped = [row for row in state.allocations if row["plan"] == "Alternative 1"]
    assert {r["supplier"]: int(r["quantity"]) for r in mapped} == {
        a["supplier_id"]: a["quantity"] for a in selected["allocations"]
    }
    assert all(row["promised"] in state.selected_plan["allocation_summary"] for row in mapped)
    assert not state._pending and not state.request_key and not state.details["final_outcome"]
    PlanningState.choose_final_plan.fn(state, "forged")
    assert state.final_choice == "Alternative 1"
    state.has_pending = True
    PlanningState.choose_final_plan.fn(state, "Minimum cost")
    assert state.final_choice == "Alternative 1"
    state.has_pending = False
    state._show(display)
    assert state.selected_plan == {}  # Reopening does not invent a saved draft selection.


@pytest.mark.parametrize("bad", ["duplicate", "missing", "unknown", "negative", "wrong-total"])
def test_bad_saved_allocation_cannot_reach_comparison_or_review(stored_cases, bad):
    payload = deepcopy(stored_cases[1])
    rows = payload["snapshot"]["result"]["minimum_cost_plan"]["allocations"]
    if bad == "duplicate":
        rows.append(deepcopy(rows[0]))
    elif bad == "missing":
        rows.pop()
    elif bad == "unknown":
        rows[0]["supplier_id"] = "unrecorded-supplier"
    elif bad == "negative":
        rows[0]["quantity"] = -1
    else:
        rows[0]["quantity"] += 1
    with pytest.raises(ValueError, match="allocation"):
        _map_case(payload, payload["case_id"])


def test_exact_absolute_premium_is_not_rounded_by_decimal_context(stored_cases):
    payload = deepcopy(stored_cases[1])
    result = payload["snapshot"]["result"]
    result["minimum_cost_plan"]["total_cost"] = "123456789012345678901234567890.000000000000000001"
    result["alternatives"][0]["total_cost"] = "123456789012345678901234567890.000000000000000002"
    display = _map_case(payload, payload["case_id"])
    assert display.plans[1]["premium_absolute"] == "+0.000000000000000001 EUR"


def test_child_selection_is_analytical_and_empty_results_clear_review(stored_cases):
    state = PlanningState(_reflex_internal_init=True)
    child, infeasible = stored_cases[2:]
    state._show(_map_case(child, child["case_id"]))
    PlanningState.choose_final_plan.fn(state, "Minimum cost")
    assert state.selected_plan["label"] == "Minimum cost" and not state._pending
    PlanningState.choose_final_plan.fn(state, "No-award")
    assert state.final_choice == "Minimum cost"
    state._show(_map_case(infeasible, infeasible["case_id"]))
    assert state.selected_plan == {} and state.plans == []


@pytest.mark.parametrize("status", ["no_proven_optimum", "solver_error", "invalid_input"])
@pytest.mark.parametrize("retained", [True, False])
def test_incomplete_outcomes_show_only_retained_saved_plans(stored_cases, status, retained):
    payload = deepcopy(stored_cases[1])
    result = payload["snapshot"]["result"]
    result["status"] = status
    if not retained:
        result["minimum_cost_plan"] = None
        result["alternatives"] = []
    display = _map_case(payload, payload["case_id"])
    state = PlanningState(_reflex_internal_init=True)
    state._show(display)
    assert state.selected_plan == {} and not state._pending
    if retained:
        assert len(state.plans) == 2 and state.details["status"] == status.replace("_", " ")
    else:
        assert state.plans == [] and state.details["chart_min_cost"] == ""
