"""Scenario API over stored bases, actual CBC, strict boundaries and stored-only replay.

Bases are Odoo-history cases over a fake read-only Odoo (``tests.helpers.planning_api``).
"""

import json
from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from application.errors import RepositoryError
from application.planning_serialization import read_request
from backend.app.config import settings
from backend.app.main import app
from tests.helpers.in_memory_uow import MemoryPlanningUnitOfWork
from tests.helpers.milp_requests import exhaustive
from tests.helpers.planning_api import BASE, controlled_terms, forbidden, headers, odoo_case_api

client = TestClient(app)


@pytest.fixture
def controlled_api(odoo_history, monkeypatch):
    uow = MemoryPlanningUnitOfWork()
    with odoo_case_api(odoo_history, uow, monkeypatch) as api:
        yield uow, controlled_terms(api)


def create(payload, key=None, solver_factory=None):
    """Store an Odoo-history base through the HTTP route, optionally with a test solver."""
    with pytest.MonkeyPatch.context() as patch:
        if solver_factory is not None:
            route = "backend.app.routes.planning_cases.planning_solver_factory"
            patch.setattr(route, solver_factory)
        response = client.post(
            f"{BASE}/from-odoo-history",
            json={"purchase_group_id": 501, "terms": payload},
            headers=headers(key),
        )
    assert response.status_code in (200, 201), response.text
    return response.json()


def test_stored_base_reads_without_model_or_solver(controlled_api, monkeypatch):
    uow, payload = controlled_api
    monkeypatch.setattr("sklearn.tree.DecisionTreeClassifier.fit", forbidden)
    created = create(payload)
    snapshot = created["snapshot"]
    assert snapshot["result"]["status"] == "optimal"
    assert snapshot["result"]["minimum_cost_plan"]["total_cost"] == "94"
    assert snapshot["result"]["alternatives"][0]["total_cost"] == "98"
    assert {
        a["supplier_id"]: a["quantity"]
        for a in snapshot["result"]["minimum_cost_plan"]["allocations"]
    } == {s["supplier_id"]: q for s, q in zip(payload["suppliers"], (6, 0, 4), strict=True)}
    assert all(a["path"] and sum(a["leaf_counts"]) >= 10 for a in snapshot["assessments"])
    for name in ("infer_odoo_history_features", "planning_solver_factory"):
        monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
    monkeypatch.setattr("application.planning_cases.assemble_planning_input", forbidden)
    monkeypatch.setattr("application.planning_cases.create_procurement_plans", forbidden)
    retrieved = client.get(f"{BASE}/{created['case_id']}", headers=headers())
    assert retrieved.status_code == 200 and retrieved.json()["snapshot"] == snapshot
    # Only the Odoo-history route creates bases; posting bare terms creates nothing.
    for path in (BASE, f"{BASE}/from-odoo"):
        assert client.post(path, json=payload, headers=headers()).status_code in (404, 405)
    assert len(uow.rows) == 1


@pytest.mark.parametrize(
    "kind",
    ["supplier_outage", "capacity_change", "demand_change", "price_change", "combined"],
)
def test_five_actual_scenarios_preserve_parent_and_scores(controlled_api, monkeypatch, kind):
    uow, payload = controlled_api
    base = create(payload)
    monkeypatch.setattr("backend.app.routes.planning_cases.infer_odoo_history_features", forbidden)
    monkeypatch.setattr("supplier_evaluation.history_model.load_model", forbidden)
    delta = {"kind": kind, "source": payload["requirement_source"]}
    supplier = payload["suppliers"][0]["supplier_id"]
    change = {"supplier_id": supplier}
    if kind in ("supplier_outage", "combined"):
        change["available"] = False
    if kind == "capacity_change":
        change["capacity"] = 2
    if kind == "price_change":
        change["unit_price"] = "12"
    if kind in ("demand_change", "combined"):
        delta["approved_quantity"] = 12
    if len(change) > 1:
        delta["suppliers"] = [change]
    key = str(uuid4())
    result = client.post(f"{BASE}/{base['case_id']}/scenarios", json=delta, headers=headers(key))
    assert result.status_code == 201, result.text
    child = result.json()
    assert child["parent_id"] == base["case_id"]
    assert child["snapshot"]["assessments"] == base["snapshot"]["assessments"]
    assert child["snapshot"]["result"]["status"] == "optimal"
    request = read_request(child["snapshot"]["request"])
    minimum = child["snapshot"]["result"]["minimum_cost_plan"]
    assert tuple(a["quantity"] for a in minimum["allocations"]) == exhaustive(request)
    for run in child["snapshot"]["result"]["runs"]:
        plan = (
            minimum
            if run["plan_index"] == 0
            else child["snapshot"]["result"]["alternatives"][run["plan_index"] - 1]
        )
        from decimal import Decimal
        from fractions import Fraction

        assert tuple(a["quantity"] for a in plan["allocations"]) == exhaustive(
            request, Decimal(run["epsilon"]), Fraction(Decimal(minimum["total_cost"]))
        )
    assert child["snapshot"]["comparison"]["minimum_cost"] is not None
    assert uow.rows[base["case_id"]].snapshot_hash == base["snapshot_hash"]
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    repeat = client.post(f"{BASE}/{base['case_id']}/scenarios", json=delta, headers=headers(key))
    assert repeat.status_code == 200 and repeat.json()["snapshot"] == child["snapshot"]
    other = {**delta, "approved_quantity": 13} if "approved_quantity" in delta else None
    if other is not None:
        conflict = client.post(
            f"{BASE}/{base['case_id']}/scenarios", json=other, headers=headers(key)
        )
        assert conflict.status_code == 409


def test_infeasible_and_beyond_score_range_are_distinct(controlled_api):
    uow, payload = controlled_api
    for s in payload["suppliers"]:
        s["capacity"] = 2000
        s["price_quantities"]["maximum"] = s["delivery_quantities"]["maximum"] = 2000
    # Scores are valid for 1-1000 units. Base ceiling 8 is covered; growing Q must not
    # narrow physical bounds to fit scores.
    base = create(payload)
    delta = {
        "kind": "demand_change",
        "source": payload["requirement_source"],
        "approved_quantity": 1500,
    }
    assert (
        client.post(
            f"{BASE}/{base['case_id']}/scenarios", json=delta, headers=headers()
        ).status_code
        == 422
    )
    assert len(uow.rows) == 1
    delta = {
        "kind": "supplier_outage",
        "source": payload["requirement_source"],
        "suppliers": [
            {"supplier_id": s["supplier_id"], "available": False} for s in payload["suppliers"]
        ],
    }
    child = client.post(f"{BASE}/{base['case_id']}/scenarios", json=delta, headers=headers())
    assert child.status_code == 201, child.text
    assert child.json()["snapshot"]["result"]["status"] == "infeasible"
    assert child.json()["snapshot"]["result"]["minimum_cost_plan"] is None
    assert child.json()["snapshot"]["comparison"]["minimum_cost"] is None


def test_guard_missing_ids_request_limit_and_sanitized_dependencies(controlled_api, monkeypatch):
    from backend.app.config import Settings

    assert (
        Settings(
            _env_file=None, supplier_history_model_directory=""
        ).supplier_history_model_directory
        is None
    )
    _, payload = controlled_api
    base = create(payload)
    url = f"{BASE}/{base['case_id']}/scenarios"
    delta = {
        "kind": "demand_change",
        "source": payload["requirement_source"],
        "approved_quantity": 12,
    }
    assert client.post(url, json=delta).status_code == 401
    assert client.get(f"{BASE}/{uuid4()}", headers=headers()).status_code == 404
    assert client.get(f"{BASE}/invalid", headers=headers()).status_code == 422
    assert client.post(url, json=delta, headers=headers("invalid")).status_code == 422
    oversized = json.dumps(delta) + " " * (256 * 1024)
    assert (
        client.post(
            url, content=oversized, headers={**headers(), "Content-Type": "application/json"}
        ).status_code
        == 413
    )

    def broken():
        raise RepositoryError("raw", "postgresql://private-password@example.com")

    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", broken)
    response = client.post(url, json=delta, headers=headers())
    assert response.status_code == 503 and "private-password" not in response.text
    monkeypatch.setattr(settings, "api_service_token", SecretStr(""))
    assert client.get(f"{BASE}/{uuid4()}", headers=headers()).status_code == 503


@pytest.mark.parametrize("phase", ["minimum", "alternative"])
@pytest.mark.parametrize("status", ["no_proven_optimum", "solver_error"])
def test_unproven_incumbents_never_become_plans_and_failure_replay_is_stored(
    controlled_api, monkeypatch, phase, status
):
    from backend.app.dependencies import planning_solver_factory
    from decision_core.planning.models import Allocation, PlanningStatus
    from decision_core.planning.planner import SolveOutcome

    _, payload = controlled_api

    def solver_factory():
        solver, evidence = planning_solver_factory()
        outcome = SolveOutcome(
            PlanningStatus(status),
            (Allocation(payload["suppliers"][0]["supplier_id"], 10),),
            "controlled_failure",
        )
        setattr(
            solver,
            "minimum_cost" if phase == "minimum" else "risk_alternative",
            lambda *args: outcome,
        )
        return solver, evidence

    key = str(uuid4())
    case = create(payload, key, solver_factory)
    result = case["snapshot"]["result"]
    assert result["status"] == status and result["alternatives"] == []
    assert (result["minimum_cost_plan"] is None) == (phase == "minimum")
    replay = create(payload, key, forbidden)  # exact retry: stored result, no solver
    assert replay["snapshot"]["result"] == result


def test_capacity_demand_and_price_change_in_both_directions(controlled_api):
    """P2: the task says "change", so increases and decreases both rerun the same MILP."""
    uow, payload = controlled_api
    base = create(payload)
    first = payload["suppliers"][0]
    source = payload["requirement_source"]
    demand = payload["requirement"]["approved_quantity"]
    deltas = [
        {
            "kind": "capacity_change",
            "suppliers": [{"supplier_id": first["supplier_id"], "capacity": first["capacity"] + 4}],
        },
        {
            "kind": "capacity_change",
            "suppliers": [{"supplier_id": first["supplier_id"], "capacity": first["capacity"] - 2}],
        },
        {
            "kind": "price_change",
            "suppliers": [{"supplier_id": first["supplier_id"], "unit_price": "8.5"}],
        },
        {
            "kind": "price_change",
            "suppliers": [{"supplier_id": first["supplier_id"], "unit_price": "12"}],
        },
        {"kind": "demand_change", "approved_quantity": demand - 2},
        {"kind": "demand_change", "approved_quantity": demand + 2},
        {
            "kind": "combined",
            "approved_quantity": demand - 1,
            "suppliers": [{"supplier_id": first["supplier_id"], "unit_price": "8", "capacity": 1}],
        },
    ]
    for delta in deltas:
        response = client.post(
            f"{BASE}/{base['case_id']}/scenarios",
            json={**delta, "source": source},
            headers=headers(),
        )
        assert response.status_code == 201, (delta, response.text)
        child = response.json()["snapshot"]
        request = child["request"]
        changed = next(s for s in request["suppliers"] if s["supplier_id"] == first["supplier_id"])
        for change in delta.get("suppliers", []):
            for field in ("capacity", "unit_price"):
                if field in change:
                    assert str(changed[field]) == str(change[field])
        if "approved_quantity" in delta:
            assert request["requirement"]["approved_quantity"] == delta["approved_quantity"]
        assert child["scenario"]["kind"] == delta["kind"]
        assert child["assessments"] == base["snapshot"]["assessments"]
    stored = client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()
    assert stored["snapshot"] == base["snapshot"] and len(uow.rows) == 1 + len(deltas)


def test_invalid_scenarios_and_corrupt_stored_result_fail_closed(controlled_api, monkeypatch):
    uow, payload = controlled_api
    base = create(payload)
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    supplier = payload["suppliers"][0]["supplier_id"]
    original = payload["suppliers"][0]["capacity"]
    price = payload["suppliers"][0]["unit_price"]
    source = payload["requirement_source"]
    invalid = [
        {"kind": "supplier_outage", "suppliers": [{"supplier_id": "unknown", "available": False}]},
        {"kind": "capacity_change", "suppliers": [{"supplier_id": supplier, "capacity": original}]},
        {"kind": "price_change", "suppliers": [{"supplier_id": supplier, "unit_price": price}]},
        {"kind": "price_change", "suppliers": [{"supplier_id": supplier, "unit_price": "0"}]},
        {"kind": "demand_change", "approved_quantity": payload["requirement"]["approved_quantity"]},
        {"kind": "capacity_change", "approved_quantity": 12},
        {"kind": "combined", "approved_quantity": 12},
        {"kind": "supplier_outage", "model_id": "new-model"},
    ]
    for delta in invalid:
        assert (
            client.post(
                f"{BASE}/{base['case_id']}/scenarios",
                json={**delta, "source": source},
                headers=headers(),
            ).status_code
            == 422
        )
    assert len(uow.rows) == 1
    stored = uow.rows[base["case_id"]]
    corrupt = json.loads(stored.snapshot)
    del corrupt["result"]["minimum_cost_plan"]
    uow.rows[stored.case_id] = replace(stored, snapshot=json.dumps(corrupt))
    assert client.get(f"{BASE}/{stored.case_id}", headers=headers()).status_code == 503
