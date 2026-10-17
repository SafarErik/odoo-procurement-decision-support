"""Complete Odoo-history demonstration with actual saved inference/CBC and IO-free reopening."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from tests.test_odoo_purchase_history import configured as _configured
from tests.test_odoo_purchase_history import forbidden
from tests.test_odoo_purchase_history import history as _history
from tools.t17_demo import run_flow, verify_stored

configured, history = _configured, _history
TOKEN = {"Authorization": "Bearer history-test-token"}


def test_complete_flow_and_reopen_without_upstream_model_solver(configured, monkeypatch, tmp_path):
    calls, uow = configured
    with TestClient(app, headers=TOKEN) as client:
        path = run_flow(
            tmp_path,
            client,
            "Controlled buyer",
            "Prefer lower saved exposure.",
            "No purchase authorized in this separate demonstration.",
            odoo_history=501,
        )
        report = json.loads(path.read_text())
        alternatives = report["base"]["snapshot"]["result"]["alternatives"]
        approved = report["approved"]["final_decision"]["approved_content"]
        assert approved["plan_index"] == (1 if alternatives else 0)
        assert report["no_award"]["final_decision"]["approved_content"] is None
        assert report["no_award"]["final_decision"]["audit"]["rationale"] == (
            "No purchase authorized in this separate demonstration."
        )
        kinds = [s["snapshot"]["scenario"]["kind"] for s in report["scenarios"]]
        assert set(kinds) == {
            "supplier_outage",
            "capacity_change",
            "demand_change",
            "price_change",
            "combined",
        }
        assert report["scenarios"][-1]["snapshot"]["result"]["status"] == "infeasible"
        assert len(uow.rows) == 11 and len(uow.decisions.rows) == 2
        assert len(uow.documents.rows) == 1
        before = (
            uow.rows.copy(),
            uow.decisions.rows.copy(),
            uow.documents.rows.copy(),
            calls.copy(),
        )
        for name in (
            "resolve_odoo_history_input",
            "infer_odoo_history_features",
            "planning_solver_factory",
            "render_approved_document",
        ):
            monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
        verify_stored(path, client)
        assert (uow.rows, uow.decisions.rows, uow.documents.rows, calls) == before
        assert "history-test-token" not in path.read_text()
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
    with TestClient(app, headers=TOKEN) as api:
        preview = api.get(
            "/api/v2/procurement/planning-cases/odoo-history/preview?purchase_group_id=501"
        ).json()
    calls = []

    def uncertain(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json=preview)
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
                odoo_history=501,
            )
    report = json.loads(next(tmp_path.glob("t17-run-*.json")).read_text())
    posts = [c for c in calls if c.method == "POST"]
    assert len(posts) == len(report["operations"]) == 1
    intent = report["operations"][0]
    assert intent["payload"] == {"purchase_group_id": 501, "terms": preview["terms"]}
    assert intent["key"] == posts[0].headers["Idempotency-Key"]
    assert "status" not in intent and intent["path"].endswith("/from-odoo-history")
