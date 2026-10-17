"""Original saved evidence stays available when a child has no proven plan."""

import asyncio
from copy import deepcopy
from fractions import Fraction

import pytest

from frontend.planning.state import PlanningState
from frontend.planning_client import _map_case, fetch_planning_case
from tests.test_t16_scenarios import configured as configured
from tests.test_t16_stored_planning import stored_cases as stored_cases


def consume(state, handler, *args):
    async def run():
        return [event async for event in handler.fn(state, *args)]

    return asyncio.run(run())


def test_fresh_infeasible_child_load_reads_original_only_and_retry_preserves_draft(
    configured, stored_cases, monkeypatch
):
    _, uow, base, posts, transport = configured
    child = stored_cases[3]
    reads = []
    reject_original = [True]

    async def read(url, identity, token):
        reads.append(identity)
        if identity == base["case_id"] and reject_original[0]:
            return None, "Stored original unavailable."
        return await fetch_planning_case(url, identity, token, transport=transport)

    monkeypatch.setattr("frontend.planning.state.fetch_planning_case", read)
    state = PlanningState(_reflex_internal_init=True)
    before = {key: row.snapshot for key, row in uow.rows.items()}
    consume(state, PlanningState.load_case, {"case_id": child["case_id"]})
    assert reads == [child["case_id"], base["case_id"]] and not posts
    assert state.has_case and state.details["case_id"] == child["case_id"]
    assert state.original_error and not state.original_plan
    assert state.scenario_metrics[2]["scenario"] == "Unavailable"
    state.stress_quantity = "25"
    state.scenario_dirty = True
    reject_original[0] = False
    consume(state, PlanningState.retry_original)
    assert reads[-1] == base["case_id"] and not posts
    assert state.original_plan["cost"] == "102 EUR" and not state.original_error
    assert state.scenario_metrics[2] == {
        "metric": "Minimum total cost",
        "base": "102 EUR",
        "scenario": "Unavailable",
        "change": "Unavailable",
    }
    assert sum(int(r["base"]) for r in state.scenario_allocation_rows) == 10
    assert all(r["scenario"] == "Unavailable" for r in state.scenario_allocation_rows)
    assert state.stress_quantity == "25" and state.scenario_dirty
    assert {key: row.snapshot for key, row in uow.rows.items()} == before


@pytest.mark.parametrize(
    "key", ["case_id", "company", "product", "unit", "currency", "quantity", "origin"]
)
def test_unrelated_original_cannot_replace_retained_evidence(stored_cases, key):
    base, child = stored_cases[1:3]
    state = PlanningState(_reflex_internal_init=True)
    original = _map_case(base, base["case_id"])
    state._show(original)
    state._show(_map_case(child, child["case_id"]))
    bad = deepcopy(original)
    bad.details[key] = "unrelated"
    before = deepcopy(state.original_plan)
    with pytest.raises(ValueError, match="context"):
        state._set_original(bad)
    assert state.original_plan == before


def test_saved_comparison_has_exact_differences_and_cache_survives_child(stored_cases):
    base, child = stored_cases[1:3]
    state = PlanningState(_reflex_internal_init=True)
    state._show(_map_case(base, base["case_id"]))
    before = deepcopy(state.original_allocations)
    state._show(_map_case(child, child["case_id"]))
    assert state.original_allocations == before
    left = base["snapshot"]["result"]["minimum_cost_plan"]["risk_exposure"]
    right = child["snapshot"]["result"]["minimum_cost_plan"]["risk_exposure"]
    delta = Fraction(**right) - Fraction(**left)
    assert state.scenario_metrics[3]["change"] == f"{delta.numerator}/{delta.denominator}"
    assert state.original_plan["cost"] == "102 EUR"
    assert state.scenario_metrics[2]["change"] == "+4 EUR"
    assert state.scenario_metrics[2]["scenario"] == state.plans[0]["cost"]
    state.has_case = False
    assert state.scenario_metrics == [] and state.scenario_allocation_rows == []


def test_definitive_scenario_failure_keeps_original_without_success_navigation(
    configured, monkeypatch
):
    state, _, _, _, _ = configured
    before = deepcopy(state.original_plan)

    async def reject(*args):
        return None, "Rejected scenario.", False

    monkeypatch.setattr("frontend.planning.state.submit_planning_request", reject)
    events = consume(
        state, PlanningState.run_scenario, {"kind": "demand_increase", "quantity": "12"}
    )
    assert events == [None] and state.original_plan == before
    assert state.details["parent_id"] == "Base case" and not state.has_pending
