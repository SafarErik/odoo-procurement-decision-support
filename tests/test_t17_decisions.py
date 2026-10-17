"""Human decision HTTP contracts over prepared stored evidence, without acquisition."""

import json
from dataclasses import replace
from datetime import UTC, datetime
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from pypdf import PdfReader

from application.errors import RepositoryError
from application.planning_serialization import snapshot_json
from backend.app.config import settings
from backend.app.main import app
from tests.t15_helpers import MemoryPlanningUnitOfWork
from tests.test_t15_planning_api import forbidden
from tests.test_t16_stored_planning import TOKEN
from tests.test_t16_stored_planning import stored_cases as _stored_cases

stored_cases = _stored_cases
BASE = "/api/v2/procurement/planning-cases"


def headers(key=None):
    return {"Authorization": f"Bearer {TOKEN}", "Idempotency-Key": key or str(uuid4())}


def intent(case, index=0, outcome="approve"):
    return {
        "snapshot_hash": case["snapshot_hash"],
        "outcome": outcome,
        "plan_index": index,
        "actor_reference": "  buyer audit reference  ",
        "rationale": "  prefer lower exposure  " if index != 0 else None,
        "demonstration_acknowledged": True,
    }


@pytest.fixture
def configured(stored_cases, monkeypatch):
    original, base, child, infeasible = stored_cases
    uow = MemoryPlanningUnitOfWork()
    uow.rows = original.rows.copy()
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    monkeypatch.setattr(settings, "api_service_token", SecretStr(TOKEN))
    monkeypatch.setattr(settings, "supplier_model_directory", None)
    for name in (
        "infer_planning_features",
        "planning_solver_factory",
        "resolve_odoo_planning_input",
    ):
        monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
    for name in ("assemble_planning_input", "create_procurement_plans"):
        monkeypatch.setattr(f"application.planning_cases.{name}", forbidden)
    with TestClient(app) as client:
        yield client, uow, base, child, infeasible


@pytest.mark.parametrize("index", [0, 1])
def test_approval_atomic_content_stored_reload_and_semantic_replay(configured, index):
    client, uow, base, *_ = configured
    before = uow.rows.copy()
    key = str(uuid4())
    command = intent(base, index)
    now = datetime.now(UTC)
    url = f"{BASE}/{base['case_id']}/final-decision"
    response = client.post(url, json=command, headers=headers(key))
    assert response.status_code == 201, response.text
    decision = response.json()["final_decision"]
    audit, content = decision["audit"], decision["approved_content"]
    assert datetime.fromisoformat(audit["recorded_at"]) >= now
    assert audit["planning_reference_time"] == base["snapshot"]["facts"]["as_of"]
    assert audit["recorded_at"] != audit["planning_reference_time"]
    assert "demonstration" in audit["demonstration"]
    assert "not authenticated" in audit["actor_attribution"]
    plans = [
        base["snapshot"]["result"]["minimum_cost_plan"],
        *base["snapshot"]["result"]["alternatives"],
    ]
    assert content["selected_plan"] == plans[index]
    assert content["planning_snapshot"] == base["snapshot"]
    assert content["human_decision"] == audit
    assert len(decision["approved_content_hash"]) == 64
    assert audit["actor_reference"] == "buyer audit reference"
    command["actor_reference"] = command["actor_reference"].strip()
    if command["rationale"]:
        command["rationale"] = command["rationale"].strip()
    replay = client.post(url, json=command, headers=headers(key))
    assert replay.status_code == 200 and replay.json()["idempotent_replay"]
    assert replay.json()["final_decision"] == decision
    loaded = client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()
    assert loaded["final_decision"] == decision and loaded["snapshot"] == base["snapshot"]
    assert uow.rows == before and len(uow.decisions.rows) == 1
    assert client.post(url, json=command, headers=headers()).status_code == 409
    command["actor_reference"] = "different actor"
    assert client.post(url, json=command, headers=headers(key)).status_code == 409


@pytest.mark.parametrize("has_plans", [True, False])
def test_no_award_with_or_without_valid_plans(configured, has_plans):
    client, uow, base, _, infeasible = configured
    if not has_plans:
        # Reuse the saved infeasible computation as a separate original base fixture.
        row = uow.rows[infeasible["case_id"]]
        snapshot = json.loads(row.snapshot)
        snapshot["scenario"] = snapshot["comparison"] = None
        snapshot["risk_context"] = base["snapshot"]["risk_context"]
        snapshot["facts"]["suppliers"] = [
            {
                **s,
                "terms": next(
                    t
                    for t in snapshot["request"]["suppliers"]
                    if t["supplier_id"] == s["terms"]["supplier_id"]
                ),
            }
            for s in snapshot["facts"]["suppliers"]
        ]
        row = replace(row, parent_id=None, snapshot=snapshot_json(snapshot))
        uow.rows[row.case_id] = row
        base = {"case_id": row.case_id, "snapshot_hash": row.snapshot_hash}
        assert (
            client.post(
                f"{BASE}/{base['case_id']}/final-decision", json=intent(base), headers=headers()
            ).status_code
            == 422
        )
    response = client.post(
        f"{BASE}/{base['case_id']}/final-decision",
        json=intent(base, None, "no_award"),
        headers=headers(),
    )
    assert response.status_code == 201, response.text
    decision = response.json()["final_decision"]
    assert decision["audit"]["outcome"] == "no_award"
    assert decision["approved_content"] is decision["approved_content_hash"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"actor_reference": " "},
        {"actor_reference": "x" * 256},
        {"actor_reference": "bad\nactor"},
        {"plan_index": True},
        {"plan_index": -1},
        {"plan_index": "0"},
        {"plan_index": 3},
        {"plan_index": None},
        {"plan_index": 1, "rationale": " "},
        {"outcome": "no_award", "plan_index": None, "rationale": " "},
        {"outcome": "no_award", "rationale": "no purchase"},
        {"snapshot_hash": "0" * 64},
        {"demonstration_acknowledged": False},
        {"demonstration_acknowledged": "true"},
        {"rationale": "x" * 2001},
        {"recorded_at": "2020-01-01T00:00:00Z"},
    ],
)
def test_invalid_intent_leaves_no_decision(configured, changes):
    client, uow, base, *_ = configured
    response = client.post(
        f"{BASE}/{base['case_id']}/final-decision", json=intent(base) | changes, headers=headers()
    )
    assert response.status_code == 422, response.text
    assert not uow.decisions.rows


def test_scenario_denial_authentication_missing_case_and_key_namespace(configured):
    client, uow, base, child, _ = configured
    url = f"{BASE}/{child['case_id']}/final-decision"
    assert client.post(url, json=intent(child), headers=headers()).status_code == 422
    assert client.post(url, json=intent(child)).status_code == 401
    assert (
        client.post(
            f"{BASE}/{uuid4()}/final-decision", json=intent(base), headers=headers()
        ).status_code
        == 404
    )
    # A creation key is valid in the separate finalization namespace.
    key = uow.rows[base["case_id"]].idempotency_key
    assert (
        client.post(
            f"{BASE}/{base['case_id']}/final-decision", json=intent(base), headers=headers(key)
        ).status_code
        == 201
    )
    row = uow.rows[base["case_id"]]
    other = replace(row, case_id=str(uuid4()), idempotency_key=str(uuid4()))
    uow.rows[other.case_id] = other
    assert (
        client.post(
            f"{BASE}/{other.case_id}/final-decision", json=intent(base), headers=headers(key)
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "corruption",
    [
        "cost",
        "capacity",
        "proof",
        "risk",
        "version",
        "provenance",
        "invalid_decimal",
        "missing_sources",
        "model_version",
    ],
)
def test_corrupt_evidence_fails_closed(configured, corruption):
    client, uow, base, *_ = configured
    row = uow.rows[base["case_id"]]
    value = json.loads(row.snapshot)
    if corruption == "cost":
        value["result"]["minimum_cost_plan"]["total_cost"] = "0.01"
    elif corruption == "capacity":
        value["request"]["suppliers"][0]["capacity"] = 0
    elif corruption == "proof":
        value["result"]["runs"] = []
    elif corruption == "risk":
        value["request"]["risk_coefficients"][0]["value"] = "0.1"
    elif corruption == "provenance":
        value["facts"]["source_type"] = "observed"
    elif corruption == "missing_sources":
        value["provenance"]["entries"] = []
    elif corruption == "model_version":
        value["model_manifest"]["metadata"]["feature_version"] = "unknown"
    elif corruption == "invalid_decimal":
        value["result"]["minimum_cost_plan"]["total_cost"] = "not a number"
    else:
        value["snapshot_version"] = "unknown"
    row = replace(row, snapshot=snapshot_json(value))
    uow.rows[row.case_id] = row
    response = client.post(
        f"{BASE}/{row.case_id}/final-decision",
        json=intent({"snapshot_hash": row.snapshot_hash}),
        headers=headers(),
    )
    assert response.status_code == 503, response.text
    assert not uow.decisions.rows


@pytest.mark.parametrize("index", [0, 1])
def test_retained_proven_plan_after_later_failure_is_approvable(configured, index):
    client, uow, base, *_ = configured
    row = uow.rows[base["case_id"]]
    snapshot = json.loads(row.snapshot)
    earlier_runs = snapshot["result"]["runs"] if index == 1 else []
    epsilon = "0.2" if index == 1 else snapshot["request"]["policy"]["epsilons"][0]
    if index == 1:
        for container in ("request", "facts"):
            snapshot[container]["policy"]["epsilons"].append(epsilon)
    snapshot["result"].update(
        status="solver_error",
        alternatives=snapshot["result"]["alternatives"] if index == 1 else [],
        runs=earlier_runs
        + [
            {
                "epsilon": epsilon,
                "status": "solver_error",
                "plan_index": None,
                "code": "alternative_verification_failed",
            }
        ],
    )
    row = replace(row, snapshot=snapshot_json(snapshot))
    uow.rows[row.case_id] = row
    response = client.post(
        f"{BASE}/{row.case_id}/final-decision",
        json=intent({"snapshot_hash": row.snapshot_hash}, index),
        headers=headers(),
    )
    assert response.status_code == 201, response.text
    decision = response.json()["final_decision"]
    assert decision["audit"]["incomplete_comparison"] is True
    assert decision["approved_content"]["planning_snapshot"]["result"]["status"] == "solver_error"
    pdf = client.get(
        f"{BASE}/{row.case_id}/approved-pdf/{decision['approved_content_hash']}",
        headers=headers(),
    )
    assert pdf.status_code == 200, pdf.text
    assert "INCOMPLETE COMPARISON" in PdfReader(BytesIO(pdf.content)).pages[0].extract_text()


def test_transaction_failure_leaves_no_partial_approval(configured, monkeypatch):
    client, uow, base, *_ = configured

    def fail():
        raise RepositoryError("repository_failure", "commit failure")

    monkeypatch.setattr(uow, "commit", fail)
    response = client.post(
        f"{BASE}/{base['case_id']}/final-decision", json=intent(base), headers=headers()
    )
    assert response.status_code == 503 and not uow.decisions.rows


def test_corrupt_approved_content_is_rejected_on_reload_and_retry(configured):
    client, uow, base, *_ = configured
    key = str(uuid4())
    url = f"{BASE}/{base['case_id']}/final-decision"
    assert client.post(url, json=intent(base), headers=headers(key)).status_code == 201
    decision = uow.decisions.rows[base["case_id"]]
    record = json.loads(decision.record)
    record["approved_content"]["selected_plan"]["total_cost"] = "999"
    uow.decisions.rows[base["case_id"]] = replace(decision, record=snapshot_json(record))
    assert client.get(f"{BASE}/{base['case_id']}", headers=headers()).status_code == 503
    assert client.post(url, json=intent(base), headers=headers(key)).status_code == 503
