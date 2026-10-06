"""Actual saved inference/CBC, strict API boundaries and stored-only replay checks."""

import json
from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from application.decision_cases import RepositoryError
from application.planning_serialization import read_request
from backend.app.config import settings
from backend.app.main import app
from tests.t15_helpers import MemoryPlanningUnitOfWork, controlled_assets, copy_payload
from tests.test_t13_planning import exhaustive

BASE = "/api/v2/procurement/planning-cases"
client = TestClient(app)


@pytest.fixture(scope="module")
def assets(tmp_path_factory):
    directory = tmp_path_factory.mktemp("t15-model")
    return directory, controlled_assets(directory)


@pytest.fixture
def configured(assets, monkeypatch):
    directory, payload = assets
    from backend.app.routes import planning_cases as routes

    uow = MemoryPlanningUnitOfWork()
    monkeypatch.setattr(routes, "get_planning_unit_of_work", lambda: uow)
    monkeypatch.setattr(settings, "t15_trusted_model_directory", directory)
    monkeypatch.setattr(settings, "t12_trusted_caller_token", SecretStr("t15-test-secret"))
    return uow, copy_payload(payload)


def headers(key=None):
    return {"Authorization": "Bearer t15-test-secret", "Idempotency-Key": key or str(uuid4())}


def forbidden(*args, **kwargs):
    raise AssertionError("Stored or commercial-only flow invoked a prohibited dependency")


def create(payload, key=None):
    response = client.post(BASE, json=payload, headers=headers(key))
    assert response.status_code == 201, response.text
    return response.json()


def test_actual_create_paths_and_stored_get_replay_without_model_solver(configured, monkeypatch):
    uow, payload = configured
    monkeypatch.setattr("sklearn.tree.DecisionTreeClassifier.fit", forbidden)
    key = str(uuid4())
    created = create(payload, key)
    snapshot = created["snapshot"]
    assert snapshot["result"]["status"] == "optimal"
    assert snapshot["result"]["minimum_cost_plan"]["total_cost"] == "102"
    assert snapshot["result"]["alternatives"][0]["total_cost"] == "109"
    assert {
        a["supplier_id"]: a["quantity"]
        for a in snapshot["result"]["minimum_cost_plan"]["allocations"]
    } == {s["supplier_id"]: q for s, q in zip(payload["suppliers"], (6, 4, 0), strict=True)}
    assert all(a["path"] and sum(a["leaf_counts"]) >= 10 for a in snapshot["assessments"])
    assert snapshot["model_manifest"]["artifact_sha256"]
    assert snapshot["solver"]["runtime"]["cbc"]
    assert snapshot["facts"]["suppliers"][0]["source"]["field_name"] == "commercial_terms"
    monkeypatch.setattr("backend.app.routes.planning_cases.infer_planning_features", forbidden)
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    monkeypatch.setattr("application.planning_cases.assemble_planning_input", forbidden)
    monkeypatch.setattr("application.planning_cases.create_procurement_plans", forbidden)
    monkeypatch.setattr(settings, "t15_trusted_model_directory", None)
    retrieved = client.get(f"{BASE}/{created['case_id']}", headers=headers())
    assert retrieved.status_code == 200 and retrieved.json()["snapshot"] == snapshot
    reordered = copy_payload(payload)
    reordered["suppliers"].reverse()
    reordered["suppliers"][0]["receipts"].reverse()
    reordered["suppliers"][0]["unit_price"] += (
        "0" if "." in reordered["suppliers"][0]["unit_price"] else ".0"
    )
    replay = client.post(BASE, json=reordered, headers=headers(key))
    assert replay.status_code == 200, replay.text
    assert (
        replay.json()["idempotent_replay"]
        and replay.json()["snapshot_hash"] == created["snapshot_hash"]
    )
    assert len(uow.rows) == 1
    conflict = copy_payload(payload)
    conflict["requirement"]["approved_quantity"] = 11
    assert client.post(BASE, json=conflict, headers=headers(key)).status_code == 409


@pytest.mark.parametrize(
    "kind",
    ["supplier_outage", "capacity_reduction", "demand_increase", "price_increase", "combined"],
)
def test_five_actual_scenarios_preserve_parent_and_scores(configured, monkeypatch, kind):
    uow, payload = configured
    base = create(payload)
    monkeypatch.setattr("backend.app.routes.planning_cases.infer_planning_features", forbidden)
    monkeypatch.setattr("supplier_evaluation.artifacts.load_model", forbidden)
    delta = {"kind": kind, "source": payload["requirement_source"]}
    supplier = payload["suppliers"][0]["supplier_id"]
    change = {"supplier_id": supplier}
    if kind in ("supplier_outage", "combined"):
        change["available"] = False
    if kind == "capacity_reduction":
        change["capacity"] = 2
    if kind == "price_increase":
        change["unit_price"] = "12"
    if kind in ("demand_increase", "combined"):
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
    assert client.post(BASE, json=payload, headers=headers(key)).status_code == 409


def test_infeasible_and_beyond_score_range_are_distinct(configured):
    uow, payload = configured
    for s in payload["suppliers"]:
        s["capacity"] = 100
        s["score_quantities"]["maximum"] = 20
    payload["policy"]["concentration_limit"] = "0.8"
    # Base ceiling 8 is covered; growing Q must not narrow physical bounds to fit scores.
    base = create(payload)
    delta = {
        "kind": "demand_increase",
        "source": payload["requirement_source"],
        "approved_quantity": 30,
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


@pytest.mark.parametrize(
    "mutation",
    [
        "observed",
        "extra",
        "bool_quantity",
        "float_price",
        "future_history",
        "duplicate",
        "context",
        "before_training",
        "missing_moq",
        "score_range",
    ],
)
def test_invalid_inputs_fail_before_solve_and_storage(configured, monkeypatch, mutation):
    uow, payload = configured
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    if mutation == "observed":
        payload["source_type"] = "odoo"
    if mutation == "extra":
        payload["artifact_path"] = "untrusted.joblib"
    if mutation == "bool_quantity":
        payload["requirement"]["approved_quantity"] = True
    if mutation == "float_price":
        payload["suppliers"][0]["unit_price"] = 10.0
    if mutation == "future_history":
        payload["suppliers"][0]["receipts"][0]["available_at"] = "2027-01-01T00:00:00Z"
    if mutation == "duplicate":
        payload["suppliers"].append(copy_payload(payload["suppliers"][0]))
    if mutation == "context":
        payload["company_id"] = "unsupported-company"
    if mutation == "before_training":
        payload["as_of"] = "2020-01-01T00:00:00Z"
    if mutation == "missing_moq":
        del payload["suppliers"][0]["minimum_order_quantity"]
    if mutation == "score_range":
        payload["suppliers"][0]["score_quantities"]["maximum"] = 1
    response = client.post(BASE, json=payload, headers=headers())
    assert response.status_code == 422, response.text
    assert not uow.rows


@pytest.mark.parametrize(
    ("cutoff", "receipt_time", "required_date"),
    [
        ("0001-01-02T00:00:00Z", "0001-01-01T00:00:00Z", "0001-01-03"),
        ("9999-12-20T00:00:00Z", "9999-11-01T00:00:00Z", "9999-12-25"),
    ],
)
def test_unrepresentable_history_or_validity_window_is_invalid_input(
    configured, monkeypatch, cutoff, receipt_time, required_date
):
    uow, payload = configured
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    payload["as_of"] = cutoff
    payload["requirement"]["required_date"] = required_date
    for source in (payload["requirement_source"], payload["policy_source"]):
        source["observed_at"] = receipt_time
    for supplier in payload["suppliers"]:
        supplier["source"]["observed_at"] = receipt_time
        supplier["promised_date"] = required_date
        for receipt in supplier["receipts"]:
            receipt.update(
                expected_arrival=receipt_time, completed_at=receipt_time, available_at=receipt_time
            )
    response = client.post(BASE, json=payload, headers=headers())
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_planning_input"
    assert not uow.rows


def test_guard_missing_ids_request_limit_and_sanitized_dependencies(configured, monkeypatch):
    from backend.app.config import Settings

    assert (
        Settings(_env_file=None, t15_trusted_model_directory="").t15_trusted_model_directory is None
    )
    _, payload = configured
    assert client.post(BASE, json=payload).status_code == 401
    assert client.get(f"{BASE}/{uuid4()}", headers=headers()).status_code == 404
    assert client.get(f"{BASE}/invalid", headers=headers()).status_code == 422
    assert client.post(BASE, json=payload, headers=headers("invalid")).status_code == 422
    oversized = json.dumps(payload) + " " * (256 * 1024)
    assert (
        client.post(
            BASE, content=oversized, headers={**headers(), "Content-Type": "application/json"}
        ).status_code
        == 413
    )
    monkeypatch.setattr(settings, "t15_trusted_model_directory", None)
    response = client.post(BASE, json=payload, headers=headers())
    assert response.status_code == 503
    assert "joblib" not in response.text and "No trusted" not in response.text

    def broken():
        raise RepositoryError("raw", "postgresql://private-password@example.com")

    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", broken)
    assert "private-password" not in client.post(BASE, json=payload, headers=headers()).text
    monkeypatch.setattr(settings, "t12_trusted_caller_token", SecretStr(""))
    assert client.get(f"{BASE}/{uuid4()}", headers=headers()).status_code == 503


@pytest.mark.parametrize("phase", ["minimum", "alternative"])
@pytest.mark.parametrize("status", ["no_proven_optimum", "solver_error"])
def test_unproven_incumbents_never_become_plans_and_failure_replay_is_stored(
    configured, monkeypatch, phase, status
):
    from backend.app.dependencies import planning_solver_factory
    from decision_core.planning.models import Allocation, PlanningStatus
    from decision_core.planning.planner import SolveOutcome

    _, payload = configured

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

    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", solver_factory)
    key = str(uuid4())
    case = create(payload, key)
    result = case["snapshot"]["result"]
    assert result["status"] == status and result["alternatives"] == []
    assert (result["minimum_cost_plan"] is None) == (phase == "minimum")
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    monkeypatch.setattr("backend.app.routes.planning_cases.infer_planning_features", forbidden)
    replay = client.post(BASE, json=payload, headers=headers(key))
    assert replay.status_code == 200 and replay.json()["snapshot"]["result"] == result


def test_invalid_scenarios_and_corrupt_stored_result_fail_closed(configured, monkeypatch):
    uow, payload = configured
    base = create(payload)
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    supplier = payload["suppliers"][0]["supplier_id"]
    source = payload["requirement_source"]
    invalid = [
        {"kind": "supplier_outage", "suppliers": [{"supplier_id": "unknown", "available": False}]},
        {"kind": "capacity_reduction", "suppliers": [{"supplier_id": supplier, "capacity": 100}]},
        {"kind": "price_increase", "suppliers": [{"supplier_id": supplier, "unit_price": "1"}]},
        {"kind": "demand_increase", "approved_quantity": 9},
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


def test_tampered_configured_artifact_is_unavailable_and_not_stored(
    configured, monkeypatch, tmp_path
):
    import shutil

    uow, payload = configured
    shutil.copytree(settings.t15_trusted_model_directory, tmp_path / "tampered")
    (tmp_path / "tampered/tree.joblib").write_bytes(b"not a trusted model")
    monkeypatch.setattr(settings, "t15_trusted_model_directory", tmp_path / "tampered")
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    assert client.post(BASE, json=payload, headers=headers()).status_code == 503
    assert not uow.rows
