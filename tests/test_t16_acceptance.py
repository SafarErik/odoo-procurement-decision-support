"""Saved-result presentation gates for the controlled T16 cockpit."""

from copy import deepcopy
from decimal import Decimal

import pytest

from frontend.app import PlanningState, planning_page
from frontend.planning_client import _map_case
from tests.test_t16_stored_planning import stored_cases as stored_cases


def test_chart_uses_saved_exact_costs_and_fixed_exposure_scale(stored_cases):
    payload = deepcopy(stored_cases[1])
    result = payload["snapshot"]["result"]
    result["minimum_cost_plan"]["total_cost"] = "102.000000000000000001"
    result["alternatives"][0]["total_cost"] = "102.000000000000000002"
    display = _map_case(payload, payload["case_id"])
    # The chart receives the stored decimals; the table keeps the exact text.
    assert [p["cost_number"] for p in display.plans] == [
        "102.000000000000000001",
        "102.000000000000000002",
    ]
    assert display.plans[0]["cost"] == "€102.000000000000000001"
    assert Decimal(display.plans[0]["exposure_number"]) > Decimal(
        display.plans[1]["exposure_number"]
    )
    assert not display.details["alternative_notice"]


def test_equal_cost_and_endpoint_exposures_stay_on_the_fixed_0_100_scale(stored_cases):
    payload = deepcopy(stored_cases[1])
    result = payload["snapshot"]["result"]
    for plan, score in zip([result["minimum_cost_plan"], *result["alternatives"]], (0, 1)):
        plan["total_cost"] = "102"
        plan["risk_exposure"] = {"numerator": score, "denominator": 1}
    display = _map_case(payload, payload["case_id"])
    assert [p["exposure_number"] for p in display.plans] == ["0.0", "100.0"]
    state = PlanningState(_reflex_internal_init=True)
    state._show(display)
    assert state.chart_minimum == [{"name": "Minimum cost", "cost": 102.0, "exposure": 0.0}]
    assert [p["exposure"] for p in state.chart_alternatives] == [100.0]


def test_single_saved_plan_has_honest_alternative_message_and_no_fabricated_point(stored_cases):
    payload = deepcopy(stored_cases[1])
    payload["snapshot"]["result"]["alternatives"] = []
    display = _map_case(payload, payload["case_id"])
    assert len(display.plans) == 1 and display.plans[0]["cost_number"]
    assert "No distinct alternative" in display.details["alternative_notice"]
    payload["snapshot"]["result"]["status"] = "solver_error"
    display = _map_case(payload, payload["case_id"])
    assert "did not finish" in display.details["alternative_notice"]
    assert "does not establish" in display.details["alternative_notice"]
    payload["snapshot"]["result"]["status"] = "optimal"
    payload["snapshot"]["request"]["policy"]["epsilons"] = []
    display = _map_case(payload, payload["case_id"])
    assert display.details["alternative_notice"] == "No alternatives were requested for this case."


def test_infeasible_case_has_no_cost_chart_values_and_replaces_previous_display(stored_cases):
    state = PlanningState(_reflex_internal_init=True)
    state.lang = "en"  # the assertions below read English texts
    base, infeasible = stored_cases[1], stored_cases[3]
    state._show(_map_case(base, base["case_id"]))
    assert state.plans
    state._show(_map_case(infeasible, infeasible["case_id"]))
    assert state.plans == [] and state.chart_minimum == [] and state.chart_alternatives == []
    assert state.details["min_cost_display"] == "" and state.details["alternative_notice"] == ""
    assert state.details["status_label"] == "No feasible plan"
    assert planning_page() is not None


@pytest.mark.parametrize("score", [-1, 2])
def test_invalid_saved_exposure_is_rejected_instead_of_clipped(stored_cases, score):
    payload = deepcopy(stored_cases[1])
    payload["snapshot"]["result"]["minimum_cost_plan"]["risk_exposure"] = {
        "numerator": score,
        "denominator": 1,
    }
    with pytest.raises(ValueError, match="exposure"):
        _map_case(payload, payload["case_id"])


def test_saved_input_terms_show_scenario_values_without_changing_base_controls(stored_cases):
    child = stored_cases[2]
    display = _map_case(child, child["case_id"])
    unavailable = next(
        s for s in display.scenario_suppliers if s["saved_available"] == "Not available"
    )
    assert unavailable["capacity"] == unavailable["saved_capacity"]
    assert unavailable["saved_price"] and unavailable["saved_date"]
    assert unavailable["saved_ranges"] == "1–1000 / 1–1000"
    assert display.assessments[0]["quantity_range"] == "1–1000 pcs"
    assert "At most 2 suppliers" in display.details["policy"]
    assert "80%" in display.details["policy"]
    malformed = deepcopy(child)
    malformed["snapshot"]["request"]["suppliers"].pop()
    with pytest.raises(ValueError, match="supplier join"):
        _map_case(malformed, child["case_id"])
