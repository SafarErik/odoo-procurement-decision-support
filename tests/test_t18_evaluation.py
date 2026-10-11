"""Evaluation accounting and real inference/CBC/API/PDF; persistence is memory here."""

import hashlib
import json
from copy import deepcopy

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.app.config import settings
from backend.app.main import app
from tests.t15_helpers import MemoryPlanningUnitOfWork
from tools import t18_evaluation as evaluation


def test_summary_includes_failures_missing_timings_and_nearest_rank():
    attempts = []
    for index in range(30):
        operations = {
            name: {"outcome": "success", "seconds": (index + 1) / 10} for name in evaluation.TARGETS
        }
        attempts.append({"phase": "measured", "operations": operations})
    attempts[-1]["operations"]["create"] = {"outcome": "transport_error", "seconds": 9.0}
    attempts[-1]["operations"]["stored_get"] = {"outcome": "pending", "seconds": None}
    attempts[-1]["operations"]["first_pdf"] = {"outcome": "not_attempted", "seconds": None}
    warmup = {"phase": "warmup", "operations": deepcopy(attempts[-1]["operations"])}
    warmup["operations"]["create"]["seconds"] = 999
    summary = evaluation.summarize([warmup, *attempts])
    created = summary["create"]
    assert created["p95_seconds"] == 2.9 and created["maximum_seconds"] == 9
    assert created["median_seconds"] == pytest.approx(1.55)
    assert created["successful"] == 29 and created["failed"] == 1
    assert created["latency_target_met"] and created["gate"] == "FAIL"
    assert summary["stored_get"]["pending"] == summary["stored_get"]["unmeasured"] == 1
    assert summary["first_pdf"]["not_attempted"] == 1
    assert summary["supplier_outage"]["gate"] == "PASS"
    assert summary["approval"]["gate"] == "FAIL"  # Successes can still miss latency.


@pytest.fixture
def prepared(tmp_path):
    directory = tmp_path / "evaluation"
    evaluation.prepare(directory)
    return directory


def test_preparation_preserves_existing_owner_artifacts(prepared):
    before = (prepared / "model/tree.joblib").read_bytes()
    with pytest.raises(ValueError, match="existing owner artifacts"):
        evaluation.prepare(prepared)
    assert (prepared / "model/tree.joblib").read_bytes() == before


def test_one_complete_evaluation_validates_saved_flow_and_pdf(prepared, monkeypatch):
    uow = MemoryPlanningUnitOfWork()
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    monkeypatch.setattr(settings, "t15_trusted_model_directory", prepared / "model")
    monkeypatch.setattr(settings, "t12_trusted_caller_token", SecretStr("t18-test-token"))
    monkeypatch.setitem(evaluation.CONTRACT, "warmups", 0)
    monkeypatch.setitem(evaluation.CONTRACT, "measured_runs", 1)

    def forbidden(*args, **kwargs):
        raise AssertionError("Evaluation HTTP flow must not train or read Odoo.")

    monkeypatch.setattr("sklearn.tree.DecisionTreeClassifier.fit", forbidden)
    monkeypatch.setattr("backend.app.routes.planning_cases.resolve_odoo_planning_input", forbidden)
    with TestClient(app, headers={"Authorization": "Bearer t18-test-token"}) as client:
        path, report = evaluation.evaluate(prepared, client)
    rows = report["attempts"][0]["operations"]
    assert {r["outcome"] for r in rows.values()} == {"success"}
    minimum = rows["create"]["response"]["result"]["minimum_cost_plan"]
    outage = rows["supplier_outage"]["response"]["result"]["minimum_cost_plan"]
    assert minimum["total_cost"] == "102" and outage["total_cost"] == "106"
    assert rows["exact_replay"]["key"] == rows["create"]["key"]
    assert (
        rows["exact_replay"]["response"]["final_decision"]
        == (rows["approval"]["response"]["final_decision"])
    )
    assert rows["first_pdf"]["document"] == rows["cached_pdf"]["document"]
    assert len(uow.rows) == 2 and len(uow.decisions.rows) == len(uow.documents.rows) == 1
    assert len(list(prepared.glob("evaluation-*.pdf"))) == 1
    assert "t18-test-token" not in path.read_text()
    assert json.loads(path.read_text()) == report


def test_uncertain_write_is_recorded_without_retry_and_blocks_dependents(prepared):
    requests = []

    def unavailable(request):
        requests.append(request)
        raise httpx.ReadTimeout("lost response")

    with httpx.Client(
        transport=httpx.MockTransport(unavailable), base_url="http://localhost"
    ) as client:
        path, report = evaluation.evaluate(prepared, client)
    assert len(requests) == 1
    row = report["attempts"][0]["operations"]["create"]
    assert row["outcome"] == "transport_error" and row["seconds"] >= 0 and row["uncertain"]
    assert row["key"] == requests[0].headers["Idempotency-Key"]
    assert row["payload"] == json.loads(requests[0].content)
    assert report["summary"]["create"]["not_attempted"] == 30
    assert report["summary"]["approval"]["unmeasured"] == 30
    assert {r["gate"] for r in report["summary"].values()} == {"FAIL"}
    assert "Uncertain" in report["stopped"]
    assert json.loads(path.read_text()) == report


@pytest.mark.parametrize("status", [401, 503])
def test_definitive_or_uncertain_http_failure_is_not_a_warmup_success(prepared, status):
    def failed(request):
        return httpx.Response(status, json={"detail": {"code": "controlled_failure"}})

    with httpx.Client(transport=httpx.MockTransport(failed), base_url="http://localhost") as client:
        _, report = evaluation.evaluate(prepared, client)
    row = report["attempts"][0]["operations"]["create"]
    assert row["outcome"] == "http_error" and row["error_code"] == "controlled_failure"
    assert row["http_status"] == status and row["uncertain"] is (status == 503)
    assert report["summary"]["create"]["attempted"] == 0
    assert all(r["gate"] == "FAIL" for r in report["summary"].values())
    assert report["stopped"].startswith("Uncertain" if status == 503 else "Warm-up failed")


def test_pdf_rejects_missing_reference_and_changed_cached_bytes():
    data = b"%PDF-controlled"
    headers = {
        "content-type": "application/pdf",
        "x-approved-content-hash": "approved",
        "x-pdf-sha256": hashlib.sha256(data).hexdigest(),
    }
    response = httpx.Response(200, headers=headers, content=data)
    with pytest.raises(ValueError, match="PDF binding"):
        evaluation.verify_pdf(response, "approved")
    headers["x-pdf-reference"] = "stable-document"
    first = httpx.Response(200, headers=headers, content=data)
    evaluation.verify_pdf(first, "approved")
    changed = b"%PDF-different"
    headers["x-pdf-sha256"] = hashlib.sha256(changed).hexdigest()
    with pytest.raises(ValueError, match="PDF binding"):
        evaluation.verify_pdf(
            httpx.Response(200, headers=headers, content=changed), "approved", first
        )
