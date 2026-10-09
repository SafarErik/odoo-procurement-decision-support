"""Buyer explanations and scenario composer contracts, using existing API/CBC fixtures."""

import asyncio
from copy import deepcopy

from frontend.planning.state import PlanningState
from frontend.planning_client import _map_case, _supplier_label
from tests.test_t16_scenarios import configured as configured
from tests.test_t16_scenarios import event
from tests.test_t16_stored_planning import stored_cases as stored_cases


def test_tradeoff_summary_and_tree_explanation_keep_exact_records(stored_cases):
    _, base, _, _ = stored_cases
    mapped = _map_case(base, base["case_id"])
    assert "7 EUR more" in mapped.details["decision_summary"]
    assert "79.3 points" in mapped.details["decision_summary"]
    for row, assessment in zip(mapped.assessments, base["snapshot"]["assessments"], strict=True):
        assert row["readable_path"]
        for step in assessment["path"]:
            assert str(step["threshold"]) in row["path"]
            assert f"{step['threshold']:.2f}" in row["readable_path"]
    altered = deepcopy(base)
    altered["snapshot"]["result"]["alternatives"][0]["risk_exposure"] = {
        "numerator": 1,
        "denominator": 1,
    }
    assert "reduces" not in _map_case(altered, base["case_id"]).details["decision_summary"]


def test_labels_are_readable_without_inventing_odoo_business_names():
    assert _supplier_label("odoo:res.partner:51") == "Supplier 51"
    assert _supplier_label("synthetic-S226") == "Demo supplier S226"
    assert _supplier_label("other-id") == "other-id"


def test_unified_composer_outage_saves_against_original_base(configured):
    state, uow, base, calls, _ = configured
    original = uow.rows[base["case_id"]].snapshot
    asyncio.run(
        event(
            state,
            PlanningState.run_scenario,
            {
                "kind": "supplier_outage",
                "supplier": "synthetic-S226",
            },
        )
    )
    assert not state.error_message and state.view == "whatif"
    assert calls[0][1]["suppliers"] == [{"supplier_id": "synthetic-S226", "available": False}]
    assert state.details["base_id"] == base["case_id"]
    assert uow.rows[base["case_id"]].snapshot == original


def test_reduction_error_names_actual_original_bound_without_post(configured):
    state, _, _, calls, _ = configured
    asyncio.run(
        event(
            state,
            PlanningState.run_scenario,
            {
                "kind": "capacity_reduction",
                "supplier": "synthetic-S226",
                "capacity": "200",
            },
        )
    )
    assert "original 6 units" in state.error_message and not calls
    assert state.error_target == "scenario"


def test_draft_changes_clear_on_kind_and_supplier_switch_and_freeze_when_pending(configured):
    state, _, _, _, _ = configured
    PlanningState.select_stress_supplier.fn(state, "synthetic-S226")
    PlanningState.update_stress.fn(state, "capacity", "4")
    assert "6 → 4" in state.scenario_draft
    PlanningState.update_stress.fn(state, "capacity", 5)
    assert state.stress_capacity == "4"
    PlanningState.select_stress_supplier.fn(state, "synthetic-S184")
    assert state.stress_capacity == "" and state.selected_terms["capacity"] == "8"
    PlanningState.update_stress.fn(state, "price", "12.00")
    PlanningState.change_scenario_kind.fn(state, "combined")
    assert state.stress_price == ""
    state.has_pending = True
    PlanningState.update_stress.fn(state, "capacity", "3")
    PlanningState.select_stress_supplier.fn(state, "synthetic-S226")
    assert state.stress_capacity == "" and state.stress_supplier == "synthetic-S184"
    PlanningState.change_input_mode.fn(state, "odoo")
    assert state.input_mode == "stored"
