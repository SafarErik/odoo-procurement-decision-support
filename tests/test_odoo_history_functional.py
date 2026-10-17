"""Complete the existing functional matrix with acquired Odoo history."""

import json
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from application.planning_cases import PlanningCaseError
from backend.app.config import settings
from backend.app.main import app
from tests.test_odoo_history_integration import configured as _configured
from tests.test_odoo_history_integration import forbidden
from tests.test_odoo_history_integration import qualified as _qualified
from tools.t17_demo import BASE, run_flow, verify_stored

configured, qualified = _configured, _qualified


def test_history_quotation_key_is_separate_and_never_falls_back(monkeypatch):
    from backend.app.dependencies import capture_local_history, local_profile
    from supplier_evaluation.contracts import digest

    calls = []

    class Reader:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        async def capture(self, revision):
            return revision

    monkeypatch.setattr("backend.app.dependencies.OdooPlanningHistoryReader", Reader)
    monkeypatch.setattr(settings, "odoo_history_database", "procurement_v2_history_test_v1")
    monkeypatch.setattr(settings, "odoo_api_key", SecretStr("original-database-key"))
    monkeypatch.setattr(settings, "odoo_history_api_key", SecretStr("clone-history-key"))
    monkeypatch.setattr(
        settings, "odoo_history_quotation_api_key", SecretStr("clone-quotation-key")
    )
    revision = digest(local_profile())
    assert capture_local_history(revision) == revision
    assert calls[0]["api_key"] == "clone-quotation-key"
    assert calls[0]["history_key"] == "clone-history-key"
    monkeypatch.setattr(settings, "odoo_history_quotation_api_key", SecretStr(""))
    with pytest.raises(PlanningCaseError) as error:
        capture_local_history(revision)
    assert error.value.code == "odoo_history_unavailable" and len(calls) == 1


def test_all_scenarios_alternative_no_award_and_stored_replay(configured, tmp_path, monkeypatch):
    _, calls, uow, _ = configured
    with TestClient(app, headers={"Authorization": "Bearer history-test-token"}) as client:
        report_path = run_flow(
            tmp_path,
            client,
            "Functional test owner",
            "Choose the saved lower exposure plan.",
            "No purchase authorized for this separate test.",
            odoo_history=True,
        )
        report = json.loads(report_path.read_text())
        assert len(uow.rows) == 8 and len(uow.decisions.rows) == 2
        expected = [2200, 2200, 2340, 2200, 2200, None]
        for child, cost in zip(report["scenarios"], expected, strict=True):
            result = child["snapshot"]["result"]
            if cost is None:
                assert result["status"] == "infeasible" and result["minimum_cost_plan"] is None
            else:
                assert Decimal(result["minimum_cost_plan"]["total_cost"]) == cost
            assert child["snapshot"]["assessments"] == report["base"]["snapshot"]["assessments"]
        assert report["approved"]["final_decision"]["intent"]["plan_index"] == 1
        before = (uow.rows.copy(), uow.decisions.rows.copy(), uow.documents.rows.copy(), len(calls))
        for name in (
            "resolve_odoo_history_input",
            "infer_odoo_history_features",
            "planning_solver_factory",
            "render_approved_document",
        ):
            monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
        verify_stored(report_path, client)
        assert (uow.rows, uow.decisions.rows, uow.documents.rows, len(calls)) == before
        assert "history-test-token" not in report_path.read_text()


def test_history_readiness_failure_creates_no_intent_or_case(tmp_path):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "model_readiness": "model_unavailable",
            },
        )
    )
    with httpx.Client(base_url="http://localhost", transport=transport) as client:
        with pytest.raises(ValueError, match="not ready"):
            run_flow(tmp_path, client, "Owner", "Alternative", "No award", odoo_history=True)
    assert not list(tmp_path.iterdir())


def test_uncertain_history_post_retains_exact_intent(configured, tmp_path):
    with TestClient(app, headers={"Authorization": "Bearer history-test-token"}) as client:
        preview = client.get(BASE + "/odoo-history/local-v1").json()
    calls = []

    def respond(request):
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, json=preview)
        raise httpx.ReadTimeout("Controlled uncertain save")

    with httpx.Client(
        base_url="http://localhost", transport=httpx.MockTransport(respond)
    ) as client:
        with pytest.raises(httpx.ReadTimeout):
            run_flow(tmp_path, client, "Owner", "Alternative", "No award", odoo_history=True)
    report = json.loads(next(tmp_path.glob("t17-run-*.json")).read_text())
    assert len(calls) == 2 and len(report["operations"]) == 1
    intent = report["operations"][0]
    assert intent["path"].endswith("/from-odoo-history") and "status" not in intent
    assert intent["key"] == calls[-1].headers["Idempotency-Key"]
    assert intent["payload"] == json.loads(calls[-1].content)
    assert all("receipts" not in s for s in intent["payload"]["terms"]["suppliers"])
