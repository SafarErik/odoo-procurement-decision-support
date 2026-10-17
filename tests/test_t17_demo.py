"""Complete hybrid demonstration with actual saved inference/CBC and IO-free reopening."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app
from tests.test_t15_odoo_planning import assets as _assets
from tests.test_t15_odoo_planning import configured as _configured
from tests.test_t15_odoo_planning import forbidden
from tools.t15_demo import write_json
from tools.t17_demo import run_flow, verify_stored

assets, configured = _assets, _configured


def test_complete_flow_and_reopen_without_upstream_model_solver(configured, monkeypatch, tmp_path):
    uow, payload, _, _, calls = configured
    write_json(tmp_path / "create-request.json", payload)
    monkeypatch.setattr("sklearn.tree.DecisionTreeClassifier.fit", forbidden)
    with TestClient(app, headers={"Authorization": "Bearer controlled-test-token"}) as client:
        path = run_flow(
            tmp_path,
            client,
            "Controlled buyer",
            "Prefer lower saved exposure.",
            "No purchase authorized in this separate demonstration.",
        )
        report = json.loads(path.read_text())
        assert (
            report["approved"]["final_decision"]["approved_content"]["selected_plan"]["total_cost"]
            == "2200"
        )
        assert report["no_award"]["final_decision"]["approved_content"] is None
        assert report["no_award"]["final_decision"]["audit"]["rationale"] == (
            "No purchase authorized in this separate demonstration."
        )
        assert {s["snapshot"]["scenario"]["kind"] for s in report["scenarios"]} == {
            "supplier_outage",
            "capacity_reduction",
            "demand_increase",
            "price_increase",
            "combined",
        }
        assert report["scenarios"][-1]["snapshot"]["result"]["status"] == "infeasible"
        assert len(uow.rows) == 8 and len(uow.decisions.rows) == 2 and len(uow.documents.rows) == 1
        before = (
            uow.rows.copy(),
            uow.decisions.rows.copy(),
            uow.documents.rows.copy(),
            calls.copy(),
        )
        for name in (
            "resolve_odoo_planning_input",
            "infer_planning_features",
            "planning_solver_factory",
            "render_approved_document",
        ):
            monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
        monkeypatch.setattr(settings, "supplier_model_directory", None)
        verify_stored(path, client)
        assert (uow.rows, uow.decisions.rows, uow.documents.rows, calls) == before
        assert "controlled-test-token" not in path.read_text()
        path.with_suffix(".pdf").write_bytes(b"different local bytes")
        with pytest.raises(ValueError, match="differs from the saved"):
            verify_stored(path, client)
        original_post = client.post

        def changed_replay(*args, **kwargs):
            response = original_post(*args, **kwargs)
            value = response.json()
            value["snapshot_hash"] = "0" * 64
            return httpx.Response(200, json=value)

        monkeypatch.setattr(client, "post", changed_replay)
        with pytest.raises(ValueError, match="Exact retry changed"):
            verify_stored(path, client)


def test_uncertain_post_preserves_exact_intent_without_automatic_retry(configured, tmp_path):
    _, payload, *_ = configured
    write_json(tmp_path / "create-request.json", payload)
    calls = []

    def uncertain(request):
        calls.append(request)
        raise httpx.ReadTimeout("controlled lost response")

    with httpx.Client(
        transport=httpx.MockTransport(uncertain), base_url="http://localhost"
    ) as client:
        with pytest.raises(httpx.ReadTimeout):
            run_flow(
                tmp_path,
                client,
                "Controlled buyer",
                "Prefer lower saved exposure.",
                "No purchase authorized in this separate demonstration.",
            )
    report = json.loads(next(tmp_path.glob("t17-run-*.json")).read_text())
    assert len(calls) == len(report["operations"]) == 1
    intent = report["operations"][0]
    assert intent["payload"] == payload and intent["key"] == calls[0].headers["Idempotency-Key"]
    assert "status" not in intent and intent["path"].endswith("/from-odoo")
