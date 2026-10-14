"""What-if UI -> existing scenario API/CBC -> immutable comparison and stored replay."""

import asyncio
import json
from copy import deepcopy
from decimal import Decimal

import httpx
import pytest
from pydantic import SecretStr

from backend.app.config import settings as backend_settings
from backend.app.main import app
from frontend.app import PlanningState, planning_page
from frontend.config import settings as frontend_settings
from frontend.planning_client import _map_case, fetch_planning_case, submit_planning_request
from tests.t15_helpers import MemoryPlanningUnitOfWork
from tests.test_t15_planning_api import forbidden
from tests.test_t16_stored_planning import TOKEN
from tests.test_t16_stored_planning import stored_cases as stored_cases


@pytest.fixture
def configured(stored_cases, monkeypatch):
    existing, base, _, _ = stored_cases
    uow = MemoryPlanningUnitOfWork()
    uow.rows = dict(existing.rows)
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    for name in ("infer_planning_features", "resolve_odoo_planning_input"):
        monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
    monkeypatch.setattr("application.planning_cases.assemble_planning_input", forbidden)
    monkeypatch.setattr(backend_settings, "t12_trusted_caller_token", SecretStr(TOKEN))
    monkeypatch.setattr(frontend_settings, "t12_trusted_caller_token", SecretStr(TOKEN))
    transport, calls = httpx.ASGITransport(app=app), []

    async def post(url, body, key, token):
        calls.append((url, deepcopy(body), key))
        return await submit_planning_request(url, body, key, token, transport=transport)

    monkeypatch.setattr("frontend.planning.state.submit_planning_request", post)
    state = PlanningState(_reflex_internal_init=True)
    state._show(_map_case(base, base["case_id"]))
    return state, uow, base, calls, transport


async def event(state, handler, *args):
    async for update in handler.fn(state, *args):
        if update is None:
            assert state.is_loading
    assert not state.is_loading


@pytest.mark.parametrize(
    "form",
    [
        {"kind": "capacity_reduction", "supplier": "synthetic-S226", "capacity": "4"},
        {"kind": "demand_increase", "quantity": "12"},
        {"kind": "price_increase", "supplier": "synthetic-S226", "price": "12.00"},
        {"kind": "combined", "supplier": "synthetic-S226", "capacity": "4", "quantity": "12"},
        {"kind": "combined", "supplier": "synthetic-S226", "capacity": "4", "price": "12.00"},
    ],
)
def test_all_scenarios_use_base_and_stored_evidence(configured, monkeypatch, form):
    state, uow, base, calls, transport = configured
    before = uow.rows[base["case_id"]].snapshot
    original_terms = deepcopy(state.scenario_suppliers)
    asyncio.run(event(state, PlanningState.run_scenario, {**form, "token": "ignored"}))
    assert not state.error_message and state.has_case and not state.has_pending
    child_id = state.details["case_id"]
    child_terms = deepcopy(state.scenario_suppliers)
    child = json.loads(uow.rows[child_id].snapshot)
    assert state.details["parent_id"] == base["case_id"]
    assert child["assessments"] == base["snapshot"]["assessments"]
    assert [
        {key: row[key] for key in ("supplier", "name", "capacity", "price")}
        for row in state.scenario_suppliers
    ] == [
        {key: row[key] for key in ("supplier", "name", "capacity", "price")}
        for row in original_terms
    ]
    for row in state.scenario_suppliers:
        saved = next(
            s for s in child["request"]["suppliers"] if s["supplier_id"] == row["supplier"]
        )
        assert row["saved_capacity"] == str(saved["capacity"])
        assert Decimal(row["saved_price"]) == Decimal(saved["unit_price"])
    assert child["scenario"]["kind"] == form["kind"]
    assert child["scenario"]["source"]["source_reference"] == "t16-ui-what-if-v1"
    assert state.details["base_cost"] == "102 EUR"
    assert state.details["base_exposure"] == "98.6 / 100"
    assert sum(int(row["scenario"]) for row in state.comparison_rows) == int(
        state.details["quantity"]
    )
    assert sum(int(row["base"]) for row in state.comparison_rows) == 10
    if "quantity" in form:
        assert "not a like-for-like saving" in state.details["comparison_display"]
    if "price" in form:
        assert calls[0][1]["suppliers"][0]["unit_price"] == "12.00"
    # Changing a scenario again still compares with the original base, not the child.
    asyncio.run(
        event(state, PlanningState.run_scenario, {"kind": "demand_increase", "quantity": "11"})
    )
    assert not state.error_message and state.details["parent_id"] == base["case_id"]
    assert calls[0][0] == calls[1][0] and calls[0][2] != calls[1][2]
    assert uow.rows[base["case_id"]].snapshot == before
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    display, error = asyncio.run(
        fetch_planning_case(
            frontend_settings.planning_cases_url,
            child_id,
            TOKEN,
            transport=transport,
        )
    )
    assert not error and display.comparison_rows and display.scenario_suppliers == child_terms
    assert TOKEN not in str(state.dict()) and TOKEN not in state.recovery_json
    assert planning_page() is not None


def test_infeasibility_is_saved_without_fabricated_comparison(configured):
    state, uow, base, _, _ = configured
    asyncio.run(
        event(state, PlanningState.run_scenario, {"kind": "demand_increase", "quantity": "30"})
    )
    assert not state.error_message and state.details["status"] == "infeasible"
    assert (
        state.details["base_status"] == "optimal"
        and state.details["scenario_status"] == "infeasible"
    )
    assert state.comparison_rows == [] and state.plans == []
    assert state.details["base_cost"] == "Not comparable"
    assert state.details["base_status_label"] == "Plans ready"
    assert state.details["scenario_status_label"] == "No feasible plan"
    assert state.details["scenario_cost"] == "No proven minimum-cost plan"
    assert state.details["parent_id"] == base["case_id"]
    assert state.details["case_id"] in uow.rows


@pytest.mark.parametrize(
    "form",
    [
        {"kind": "demand_increase", "quantity": "10"},
        {"kind": "demand_increase", "quantity": "1001"},
        {"kind": "demand_increase", "quantity": "١٢"},
        {"kind": "demand_increase", "quantity": 12},
        {"kind": "capacity_reduction", "supplier": "synthetic-S226", "capacity": "6"},
        {"kind": "capacity_reduction", "supplier": "synthetic-S226", "capacity": "-1"},
        {"kind": "capacity_reduction", "supplier": "unknown", "capacity": "0"},
        {"kind": "price_increase", "supplier": "synthetic-S226", "price": "10"},
        {"kind": "price_increase", "supplier": "synthetic-S226", "price": "NaN"},
        {"kind": "price_increase", "supplier": "synthetic-S226", "price": "1e2"},
        {"kind": "price_increase", "supplier": "synthetic-S226", "price": "١٢"},
        {"kind": "price_increase", "supplier": "synthetic-S226", "price": "01.5"},
        {"kind": "price_increase", "supplier": "synthetic-S226", "price": 12.0},
        {"kind": "combined", "supplier": "synthetic-S226", "quantity": "12"},
        {"kind": "combined", "supplier": "synthetic-S226"},
        {"kind": "unsupported"},
        {"kind": []},
    ],
)
def test_invalid_or_empty_changes_never_post(configured, form):
    state, _, _, calls, _ = configured
    asyncio.run(event(state, PlanningState.run_scenario, form))
    assert state.error_message and not state.has_pending and not calls


def test_lost_response_recovers_exact_scenario_without_solving_again(configured, monkeypatch):
    state, uow, base, _, transport = configured
    count, requests = len(uow.rows), []

    async def lose_first(request):
        requests.append((request.url.path, request.content, request.headers["Idempotency-Key"]))
        response = await transport.handle_async_request(request)
        if len(requests) == 1:
            assert response.status_code == 201
            raise httpx.ReadTimeout("Lost after commit", request=request)
        return response

    async def post(url, payload, key, token):
        return await submit_planning_request(
            url, payload, key, token, transport=httpx.MockTransport(lose_first)
        )

    monkeypatch.setattr("frontend.planning.state.submit_planning_request", post)
    form = {"kind": "combined", "supplier": "synthetic-S226", "capacity": "4", "quantity": "12"}
    asyncio.run(event(state, PlanningState.run_scenario, form))
    assert state.has_pending and len(uow.rows) == count + 1
    pending = state.recovery_json
    PlanningState.change_scenario_kind.fn(state, "price_increase")
    assert state.scenario_kind == "capacity_reduction"
    asyncio.run(event(state, PlanningState.run_scenario, {**form, "quantity": "13"}))
    assert len(requests) == 1 and state.recovery_json == pending
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    asyncio.run(event(state, PlanningState.recover_request))
    assert not state.has_pending and not state.error_message
    assert requests[0] == requests[1] and len(uow.rows) == count + 1
    assert state.details["parent_id"] == base["case_id"]


@pytest.mark.parametrize("change", ["duplicate", "unknown", "quantity", "scenario_mismatch"])
def test_corrupt_comparison_fails_closed(stored_cases, change):
    _, _, child, _ = stored_cases
    payload = deepcopy(child)
    rows = payload["snapshot"]["comparison"]["minimum_cost"]["base_allocations"]
    if change == "duplicate":
        rows.append(deepcopy(rows[0]))
    elif change == "unknown":
        rows[0]["supplier_id"] = "unknown"
    elif change == "quantity":
        rows[0]["quantity"] += 1
    else:
        rows = payload["snapshot"]["comparison"]["minimum_cost"]["scenario_allocations"]
        rows[0]["quantity"], rows[1]["quantity"] = rows[1]["quantity"], rows[0]["quantity"]
    with pytest.raises(ValueError):
        _map_case(payload, payload["case_id"])


def test_hybrid_price_change_is_labelled_as_what_if(stored_cases):
    _, _, child, _ = stored_cases
    payload = deepcopy(child)
    payload["snapshot"]["facts"]["input_kind"] = "odoo_quotations_synthetic_history"
    payload["snapshot"]["scenario"]["suppliers"][0]["unit_price"] = "12.00"
    display = _map_case(payload, payload["case_id"])
    assert "Saved Odoo quotations with what-if changes" in display.details["input_kind"]
    assert "price 12.00 EUR per unit" in display.details["assumptions"]
