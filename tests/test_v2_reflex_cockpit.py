"""Focused state/client checks use the existing pytest and asyncio conventions."""

import asyncio
import json
from decimal import Decimal, localcontext

import pytest
from pydantic import ValidationError

pytest.importorskip("reflex")

from frontend.v2_spike import state as state_module  # noqa: E402
from frontend.v2_spike.contracts import ServiceError  # noqa: E402
from frontend.v2_spike.presentation import allocation_series, plan_view  # noqa: E402
from frontend.v2_spike.service import FIXTURE, MockCockpitClient  # noqa: E402
from frontend.v2_spike.state import CockpitState  # noqa: E402


async def drain(events):
    return [event async for event in events]


@pytest.fixture
def api(monkeypatch):
    client = MockCockpitClient(latency=0)
    monkeypatch.setattr(state_module, "client", client)
    return client


async def loaded():
    state = CockpitState(_reflex_internal_init=True)
    await drain(state.load_case())
    return state


def test_loading_clears_stale_choices_and_publishes_complete_result(api):
    async def check():
        state = await loaded()
        assert len(state.plans) == 3 and len(state.suppliers) == 4
        assert not state.has_selection and not state.can_approve
        state.select_plan("balanced")
        generator = state.load_case()
        await anext(generator)
        assert state.loading and not state.plans and not state.has_selection
        await drain(generator)
        assert not state.busy and state.case.case_id == "V2-DEMO-001"

    asyncio.run(check())


def test_selection_formats_only_supplied_plan_values(api):
    async def check():
        state = await loaded()
        state.select_plan("balanced")
        assert state.selected.total_cost == "1040" and state.can_approve
        view = plan_view(state.selected)
        assert view.cost_display == "€1,040.00" and view.risk_display == "0.1753"
        assert allocation_series(state.selected) == [
            {"name": "Allocation", "A": 60, "B": 0, "C": 40}
        ]
        state.select_plan("unknown")
        assert state.selected_id == "balanced"

    asyncio.run(check())


@pytest.mark.parametrize(
    "operation",
    [
        "Supplier unavailable",
        "Capacity reduced to 30",
        "Demand increased to 120",
        "Unit price increased by 20%",
    ],
)
def test_scenario_replaces_plans_preserves_policy_and_exposes_deltas(api, operation):
    async def check():
        state = await loaded()
        state.select_plan("balanced")
        before = state.selected.model_dump()
        state.set_operation(operation)
        generator = state.run_scenario()
        await anext(generator)
        assert state.running and not state.can_approve and not state.plans
        await drain(generator)
        assert state.selected_id == "balanced" and state.selected.model_dump() != before
        assert len(state.scenario_delta) == 4
        assert not state.busy
        assert sum(a.quantity for a in state.selected.allocations) == state.result.quantity

    asyncio.run(check())


def test_infeasible_scenario_returns_no_allocation_or_approvable_selection(api):
    async def check():
        state = await loaded()
        state.select_plan("lower")
        state.set_operation("Combined supply disruption")
        await drain(state.run_scenario())
        assert state.infeasible and state.reasons
        assert not state.plans and not state.has_selection and not state.can_approve
        assert state.allocation_data == []
        assert await drain(state.approve_plan()) == []

    asyncio.run(check())


@pytest.mark.parametrize("mode", ["Service unavailable", "No plans", "Risk unavailable"])
def test_error_and_empty_modes_remove_stale_plan_data(api, mode):
    async def check():
        state = await loaded()
        state.select_plan("balanced")
        state.set_preview_mode(mode)
        await drain(state.load_case())
        assert not state.plans and not state.has_selection and not state.can_approve
        if mode == "Service unavailable":
            assert state.case is None and "unavailable" in state.error
        elif mode == "Risk unavailable":
            assert all(s.risk_score is None for s in state.suppliers)

    asyncio.run(check())


def test_scenario_service_error_cannot_leave_old_allocation_approvable(api):
    async def check():
        state = await loaded()
        state.select_plan("balanced")
        state.set_preview_mode("Service unavailable")
        await drain(state.run_scenario())
        assert state.error and not state.plans and not state.can_approve
        assert not state.busy

    asyncio.run(check())


def test_approval_failure_keeps_review_open(api):
    async def check():
        state = await loaded()
        state.select_plan("balanced")
        state.set_preview_mode("Approval unavailable")
        await drain(state.approve_plan())
        assert "could not be recorded" in state.approval_error
        assert not state.locked and not state.approving

    asyncio.run(check())


def test_approved_snapshot_is_locked_and_not_shared_between_users(api):
    async def check():
        state = await loaded()
        state.select_plan("lower")
        state.set_note("Accepted premium after review.")
        await drain(state.approve_plan())
        assert state.locked and not state.can_approve
        snapshot = state.approved.model_dump_json()
        state.select_plan("minimum")
        state.set_note("Changed")
        state.set_operation("Supplier unavailable")
        state.set_supplier_choice("B · Danube Supply")
        await drain(state.load_case())
        await drain(state.run_scenario())
        await drain(state.approve_plan())
        assert state.approved.model_dump_json() == snapshot
        assert state.selected_id == "lower"
        other = await loaded()
        assert not other.locked
        with pytest.raises(ValidationError):
            state.approved.plan.total_cost = "1"
        with pytest.raises(ValidationError):
            state.approved.plan.allocations[0].quantity = 0

    asyncio.run(check())


def test_stale_plan_cannot_be_approved(api):
    async def check():
        _, _, result = await api.load()
        modified = result.plans[0].model_copy(update={"total_cost": "1"})
        with pytest.raises(ServiceError, match="changed"):
            await api.approve("baseline", "minimum", "", expected_plan=modified)
        with pytest.raises(ServiceError, match="feasible"):
            await api.approve("shortfall_A", "minimum", "", expected_plan=result.plans[0])

    asyncio.run(check())


def test_pdf_requires_approval_and_preserves_approved_snapshot(api):
    async def check():
        state = await loaded()
        assert await drain(state.export_pdf()) == []
        state.select_plan("balanced")
        await drain(state.approve_plan())
        snapshot = state.approved.model_dump_json()
        await drain(state.export_pdf())
        assert "PDF not yet available" in state.pdf_message
        assert state.approved.model_dump_json() == snapshot
        assert not state.exporting

    asyncio.run(check())


@pytest.mark.parametrize("valid", [True, False])
def test_ready_pdf_download_event_requires_matching_approval_hash(monkeypatch, valid):
    class PdfClient(MockCockpitClient):
        async def pdf(self, approved, mode="Ready"):
            result = await super().pdf(approved, mode)
            return result.model_copy(
                update={
                    "status": "ready",
                    "download_url": "/mock-plan.pdf",
                    "snapshot_hash": approved.snapshot_hash if valid else "wrong",
                }
            )

    monkeypatch.setattr(state_module, "client", PdfClient(latency=0))

    async def check():
        state = await loaded()
        state.select_plan("balanced")
        await drain(state.approve_plan())
        events = await drain(state.export_pdf())
        assert (len(events) == 2) == valid
        if not valid:
            assert "does not match" in state.pdf_message
        else:
            assert "download" in str(events[-1]).lower()

    asyncio.run(check())


def test_fixture_plan_totals_hard_bounds_and_score_exposures_are_consistent():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    scores = {
        s["supplier_id"]: Decimal(s["risk_score"])
        for s in data["suppliers"]
        if s["risk_score"] is not None
    }
    for key, result in data["scenarios"].items():
        if key.startswith("shortfall"):
            assert not result["plans"] and result["reasons"]
        prices = {s["supplier_id"]: Decimal(s["unit_price"]) for s in data["suppliers"]}
        capacities = {s["supplier_id"]: s["capacity"] for s in data["suppliers"]}
        if key.startswith("price"):
            prices[key[-1]] *= Decimal("1.2")
        if key.startswith("capacity"):
            capacities[key[-1]] = 30
        minimum_cost = Decimal(result["plans"][0]["total_cost"]) if result["plans"] else None
        for plan in result["plans"]:
            allocations = plan["allocations"]
            assert sum(a["quantity"] for a in allocations) == result["quantity"]
            assert sum(a["quantity"] > 0 for a in allocations) <= 2
            assert all(
                Decimal(a["quantity"]) / result["quantity"] <= Decimal("0.8") for a in allocations
            )
            assert all(a["quantity"] <= capacities[a["supplier_id"]] for a in allocations)
            assert sum(a["quantity"] * prices[a["supplier_id"]] for a in allocations) == Decimal(
                plan["total_cost"]
            )
            premium_limit = {"minimum": "0", "balanced": "0.02", "lower": "0.05"}
            assert Decimal(plan["total_cost"]) <= minimum_cost * (
                1 + Decimal(premium_limit[plan["plan_id"]])
            )
            exposure = sum(a["quantity"] * scores[a["supplier_id"]] for a in allocations)
            with localcontext() as context:
                context.prec = 40
                assert exposure / result["quantity"] == Decimal(plan["risk_exposure"])
            if key.startswith("outage"):
                assert next(a["quantity"] for a in allocations if a["supplier_id"] == key[-1]) == 0
            if key.startswith("capacity"):
                assert next(a["quantity"] for a in allocations if a["supplier_id"] == key[-1]) <= 30


def test_fixture_read_failure_is_safe_client_error(monkeypatch, tmp_path):
    from frontend.v2_spike import service

    monkeypatch.setattr(service, "FIXTURE", tmp_path / "missing.json")
    with pytest.raises(ServiceError, match="Case data is unavailable"):
        asyncio.run(MockCockpitClient(latency=0).load())
