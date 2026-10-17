"""Controlled quotation binding, actual saved synthetic inference/CBC, and IO-free replay."""

import asyncio
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.app.config import settings
from backend.app.main import app
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from tests.t15_helpers import MemoryPlanningUnitOfWork, copy_payload
from tests.test_odoo_comparison_case_adapter import _payloads
from tools.t15_demo import BASE
from tools.t15_odoo_demo import prepare_odoo_assets


def quotation_reader(payloads, calls):
    def respond(request):
        calls.append(request.url.path)
        assert request.url.path.rsplit("/", 1)[1] in {"search_read", "search_count"}
        if request.url.path.endswith("purchase.order/search_count"):
            return httpx.Response(200, json=len(payloads["orders"]))
        if request.url.path.endswith("purchase.order/search_read"):
            return httpx.Response(200, json=payloads["orders"])
        if request.url.path.endswith("purchase.order.line/search_read"):
            return httpx.Response(200, json=payloads["lines"])
        if request.url.path.endswith("res.partner/search_read"):
            return httpx.Response(200, json=payloads["partners"])
        if request.url.path.endswith("res.currency/search_read"):
            return httpx.Response(200, json=[{"id": 2, "name": "USD"}])
        raise AssertionError(request.url.path)

    return OdooComparisonCaseReader(
        base_url="http://odoo.test",
        database="test",
        api_key="synthetic",
        transport=httpx.MockTransport(respond),
    )


@pytest.fixture(scope="module")
def assets(tmp_path_factory):
    directory = tmp_path_factory.mktemp("t15-odoo-model")
    reader = quotation_reader(_payloads(), [])
    case = asyncio.run(reader.read_comparison_case(501))
    code, observed = asyncio.run(reader.read_currency_code(case.offers[0].currency_id))
    payload, scenario = prepare_odoo_assets(directory, case, code, observed)
    return directory, payload, scenario


@pytest.fixture
def configured(assets, monkeypatch):
    directory, payload, scenario = assets
    uow, payloads, calls = MemoryPlanningUnitOfWork(), _payloads(), []
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    monkeypatch.setattr(
        "backend.app.dependencies.get_comparison_case_reader",
        lambda: quotation_reader(payloads, calls),
    )
    monkeypatch.setattr(settings, "supplier_model_directory", directory / "model")
    monkeypatch.setattr(settings, "api_service_token", SecretStr("controlled-test-token"))
    return uow, copy_payload(payload), copy_payload(scenario), payloads, calls


def headers(key=None):
    return {"Authorization": "Bearer controlled-test-token", "Idempotency-Key": key or str(uuid4())}


def forbidden(*args, **kwargs):
    raise AssertionError("Stored flow used an upstream/model/solver dependency")


def test_actual_hybrid_creation_provenance_outage_and_offline_replay(configured, monkeypatch):
    uow, payload, scenario, _, calls = configured
    monkeypatch.setattr("sklearn.tree.DecisionTreeClassifier.fit", forbidden)
    key, child_key = str(uuid4()), str(uuid4())
    with TestClient(app) as client:
        response = client.post(f"{BASE}/from-odoo", json=payload, headers=headers(key))
        assert response.status_code == 201, response.text
        base = response.json()
        snapshot = base["snapshot"]
        assert snapshot["facts"]["input_kind"] == "odoo_quotations_synthetic_history"
        assert snapshot["facts"]["comparison_case_id"] == "odoo:purchase.order.group:501"
        assert snapshot["request"]["requirement"]["approved_quantity"] == 200
        minimum = snapshot["result"]["minimum_cost_plan"]
        assert minimum["total_cost"] == "1850"
        assert [a["quantity"] for a in minimum["allocations"]] == [50, 0, 150]
        assert snapshot["result"]["alternatives"][0]["total_cost"] == "2200"
        assert snapshot["model_manifest"]["metadata"]["source_type"] == "t14_synthetic"
        assert all(a["snapshot"]["source_type"] == "t14_synthetic" for a in snapshot["assessments"])
        sources = {e["canonical_path"]: e for e in snapshot["provenance"]["entries"]}
        assert (
            sources["request.suppliers[odoo:res.partner:301].unit_price"]["source_type"]
            == "odoo_json2"
        )
        assert (
            sources["request.requirement.approved_quantity"]["source_type"]
            == "controlled_business_terms"
        )
        assert (
            sources["facts.suppliers[odoo:res.partner:301].receipts"]["source_type"]
            == "t14_synthetic"
        )
        assert calls and all(path.endswith(("search_read", "search_count")) for path in calls)
        monkeypatch.setattr(
            "backend.app.routes.planning_cases.resolve_odoo_planning_input", forbidden
        )
        monkeypatch.setattr("backend.app.routes.planning_cases.infer_planning_features", forbidden)
        child = client.post(
            f"{BASE}/{base['case_id']}/scenarios", json=scenario, headers=headers(child_key)
        )
        assert child.status_code == 201, child.text
        assert child.json()["snapshot"]["result"]["minimum_cost_plan"]["total_cost"] == "2200"
        monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
        monkeypatch.setattr(settings, "supplier_model_directory", None)
        assert (
            client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["snapshot"]
            == snapshot
        )
        reordered = copy_payload(payload)
        reordered["controlled_input"]["suppliers"].reverse()
        replay = client.post(f"{BASE}/from-odoo", json=reordered, headers=headers(key))
        assert replay.status_code == 200 and replay.json()["snapshot_hash"] == base["snapshot_hash"]
        assert (
            client.post(
                f"{BASE}/{base['case_id']}/scenarios", json=scenario, headers=headers(child_key)
            ).status_code
            == 200
        )
        changed = copy_payload(payload)
        changed["controlled_input"]["requirement"]["approved_quantity"] = 201
        assert (
            client.post(f"{BASE}/from-odoo", json=changed, headers=headers(key)).status_code == 409
        )
        assert (
            client.post(BASE, json=payload["controlled_input"], headers=headers(key)).status_code
            == 409
        )
        assert len(uow.rows) == 2


def test_hybrid_final_decision_and_creation_recovery_use_only_saved_evidence(
    configured, monkeypatch
):
    _, payload, _, _, calls = configured
    creation_key, final_key = str(uuid4()), str(uuid4())
    with TestClient(app) as client:
        created = client.post(f"{BASE}/from-odoo", json=payload, headers=headers(creation_key))
        assert created.status_code == 201, created.text
        case = created.json()
        before = calls.copy()
        for name in (
            "resolve_odoo_planning_input",
            "infer_planning_features",
            "planning_solver_factory",
        ):
            monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
        monkeypatch.setattr(settings, "supplier_model_directory", None)
        command = {
            "snapshot_hash": case["snapshot_hash"],
            "outcome": "approve",
            "plan_index": 1,
            "actor_reference": "hybrid demo buyer",
            "rationale": "Prefer lower saved exposure.",
            "demonstration_acknowledged": True,
        }
        approved = client.post(
            f"{BASE}/{case['case_id']}/final-decision", json=command, headers=headers(final_key)
        )
        assert approved.status_code == 201, approved.text
        recovered = client.post(f"{BASE}/from-odoo", json=payload, headers=headers(creation_key))
        assert recovered.status_code == 200, recovered.text
        assert recovered.json()["final_decision"] == approved.json()["final_decision"]
        assert recovered.json()["snapshot"] == case["snapshot"] and calls == before
        from io import BytesIO

        from pypdf import PdfReader

        pdf = client.get(
            f"{BASE}/{case['case_id']}/approved-pdf/"
            + approved.json()["final_decision"]["approved_content_hash"],
            headers=headers(),
        )
        assert pdf.status_code == 200, pdf.text
        text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf.content)).pages)
        assert "2200 USD" in text and "odoo_json2" in text and "t14_synthetic" in text
        assert calls == before


@pytest.mark.parametrize(
    "problem",
    [
        "price",
        "tax",
        "company",
        "product",
        "duplicate_supplier",
        "missing_terms",
        "future_cutoff",
        "observed_history",
        "unavailable",
    ],
)
def test_invalid_hybrid_input_never_solves_or_stores(configured, monkeypatch, problem):
    uow, payload, _, upstream, _ = configured
    body = payload["controlled_input"]
    if problem == "price":
        body["suppliers"][0]["unit_price"] = "1"
    elif problem == "tax":
        upstream["lines"][0]["tax_ids"] = [7]
    elif problem == "company":
        body["company_id"] = "odoo:res.company:99"
    elif problem == "product":
        upstream["lines"][0]["product_id"] = [999, "other"]
    elif problem == "duplicate_supplier":
        upstream["partners"][1]["commercial_partner_id"] = upstream["partners"][0][
            "commercial_partner_id"
        ]
    elif problem == "missing_terms":
        body["suppliers"].pop()
    elif problem == "future_cutoff":
        body["as_of"] = "2099-01-01T00:00:00Z"
    elif problem == "observed_history":
        body["source_type"] = "odoo_projection"
    else:
        from application.errors import RepositoryError

        def unavailable(*args):
            raise RepositoryError("raw", "private-token-database-url")

        monkeypatch.setattr(
            "backend.app.routes.planning_cases.resolve_odoo_planning_input", unavailable
        )
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    with TestClient(app) as client:
        response = client.post(f"{BASE}/from-odoo", json=payload, headers=headers())
    assert response.status_code == (503 if problem == "unavailable" else 422), response.text
    assert "private-token" not in response.text and not uow.rows
