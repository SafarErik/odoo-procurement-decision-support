"""Stored API-to-cockpit contracts, including source honesty and failure recovery."""

import asyncio
import json
from copy import deepcopy
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.app.config import settings as backend_settings
from backend.app.main import app
from frontend.app import PlanningState, planning_page
from frontend.config import FrontendSettings
from frontend.config import settings as frontend_settings
from frontend.planning_client import fetch_planning_case, submit_planning_request
from tests.t15_helpers import MemoryPlanningUnitOfWork, controlled_assets
from tests.test_t15_planning_api import forbidden

TOKEN = "t16-test-secret"


@pytest.fixture(scope="module")
def stored_cases(tmp_path_factory):
    directory = tmp_path_factory.mktemp("t16-model")
    payload = controlled_assets(directory)
    uow = MemoryPlanningUnitOfWork()
    headers = {"Authorization": f"Bearer {TOKEN}"}
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
        patch.setattr(backend_settings, "t12_trusted_caller_token", SecretStr(TOKEN))
        patch.setattr(backend_settings, "t15_trusted_model_directory", directory)
        with TestClient(app) as client:
            base = client.post(
                "/api/v2/procurement/planning-cases",
                json=payload,
                headers={**headers, "Idempotency-Key": str(uuid4())},
            )
            assert base.status_code == 201
            base = base.json()
            children = []
            for selected in (payload["suppliers"][:1], payload["suppliers"]):
                child = client.post(
                    f"/api/v2/procurement/planning-cases/{base['case_id']}/scenarios",
                    json={
                        "kind": "supplier_outage",
                        "source": payload["requirement_source"],
                        "suppliers": [
                            {"supplier_id": s["supplier_id"], "available": False} for s in selected
                        ],
                    },
                    headers={**headers, "Idempotency-Key": str(uuid4())},
                )
                assert child.status_code == 201
                children.append(child.json())
    return uow, base, *children


def test_real_stored_api_mapping_without_upstream_model_or_solver(stored_cases, monkeypatch):
    uow, base, child, infeasible = stored_cases
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    monkeypatch.setattr(backend_settings, "t12_trusted_caller_token", SecretStr(TOKEN))
    for name in (
        "infer_planning_features",
        "planning_solver_factory",
        "resolve_odoo_planning_input",
    ):
        monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
    monkeypatch.setattr("application.planning_cases.assemble_planning_input", forbidden)
    before = {key: row.snapshot for key, row in uow.rows.items()}

    async def read():
        return [
            await fetch_planning_case(
                "http://api.test/api/v2/procurement/planning-cases",
                case["case_id"],
                TOKEN,
                transport=httpx.ASGITransport(app=app),
            )
            for case in (base, child, infeasible)
        ]

    mapped = asyncio.run(read())
    assert all(error == "" for _, error in mapped)
    reference, scenario, no_plan = [display for display, _ in mapped]
    assert [p["cost"] for p in reference.plans] == ["102 EUR", "109 EUR"]
    assert reference.details["snapshot_hash"] == base["snapshot_hash"]
    assert scenario.details["parent_id"] == base["case_id"]
    assert "Cost delta: 4 EUR" in scenario.details["comparison"]
    assert no_plan.details["status"] == "infeasible" and no_plan.plans == []
    assert len(reference.allocations) == 6
    assert reference.assessments[0]["path"]
    assert "synthetic" in reference.details["input_kind"].lower()
    assert reference.provenance[0]["reference"]
    assert before == {key: row.snapshot for key, row in uow.rows.items()}


@pytest.mark.parametrize(
    "status,expected",
    [
        (404, "not found"),
        (401, "rejected"),
        (403, "rejected"),
        (503, "unavailable"),
        (500, "unavailable"),
        (302, "unavailable"),
    ],
)
def test_http_failures_are_safe_and_not_retried(status, expected):
    calls = []

    def respond(request):
        calls.append(request)
        assert request.method == "GET" and request.headers["Authorization"] == f"Bearer {TOKEN}"
        return httpx.Response(status, headers={"Location": "http://elsewhere.test/"}, text=TOKEN)

    display, error = asyncio.run(
        fetch_planning_case(
            "http://api.test/cases",
            str(uuid4()),
            TOKEN,
            transport=httpx.MockTransport(respond),
        )
    )
    assert display is None and expected in error and TOKEN not in error
    assert len(calls) == 1


@pytest.mark.parametrize(
    "case_id,token",
    [
        ("../other", TOKEN),
        (str(uuid4()), ""),
        (str(uuid4()), "non-ascii-ő"),
        (str(uuid4()), "unsafe\ntoken"),
    ],
)
def test_invalid_identity_or_missing_secret_never_sends_request(case_id, token):
    display, error = asyncio.run(
        fetch_planning_case(
            "http://api.test/cases",
            case_id,
            token,
            transport=httpx.MockTransport(forbidden),
        )
    )
    assert display is None and error


@pytest.mark.parametrize("fault", ["identity", "version", "decimal", "source", "shape", "quantity"])
def test_malformed_snapshots_fail_closed(stored_cases, fault):
    payload = deepcopy(stored_cases[1])
    if fault == "identity":
        payload["case_id"] = str(uuid4())
    if fault == "version":
        payload["snapshot"]["snapshot_version"] = "future"
    if fault == "decimal":
        payload["snapshot"]["result"]["minimum_cost_plan"]["total_cost"] = "NaN"
    if fault == "source":
        payload["snapshot"]["assessments"][0]["snapshot"]["source_type"] = "odoo_observed"
    if fault == "shape":
        del payload["snapshot"]["request"]["requirement"]["currency"]
    if fault == "quantity":
        payload["snapshot"]["request"]["requirement"]["approved_quantity"] = 0
    display, error = asyncio.run(
        fetch_planning_case(
            "http://api.test/cases",
            stored_cases[1]["case_id"],
            TOKEN,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
        )
    )
    assert display is None and "snapshot" in error


def test_hybrid_provenance_and_exact_money_are_presented_without_relabelling(stored_cases):
    payload = deepcopy(stored_cases[1])
    payload["snapshot"]["facts"]["input_kind"] = "odoo_quotations_synthetic_history"
    payload["snapshot"]["provenance"]["entries"][0]["source_type"] = "odoo_json2"
    payload["snapshot"]["result"]["minimum_cost_plan"]["total_cost"] = "102.001"
    display, error = asyncio.run(
        fetch_planning_case(
            "http://api.test/cases",
            payload["case_id"],
            TOKEN,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
        )
    )
    assert not error and display.plans[0]["cost"] == "102.001 EUR"
    assert display.details["input_kind"] == "Live Odoo quotations; synthetic ML history"
    assert display.provenance[0]["type"] == "odoo_json2"


def test_state_loading_failure_clears_previous_case_and_recovery(stored_cases, monkeypatch):
    # Reflex imports this during event payload conversion, including plain forms.
    # It must work on a fresh frontend install (SQLAlchemy asyncio/greenlet).
    from reflex.model import Model

    assert Model is not None
    payload = stored_cases[1]
    display, _ = asyncio.run(
        fetch_planning_case(
            "http://api.test/cases",
            payload["case_id"],
            TOKEN,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
        )
    )
    outcomes = iter([(display, ""), (None, "Planning data is unavailable."), (display, "")])

    async def fetch(url, case_id, token):
        assert token == TOKEN and case_id == payload["case_id"]
        return next(outcomes)

    monkeypatch.setattr("frontend.app.fetch_planning_case", fetch)
    monkeypatch.setattr(frontend_settings, "t12_trusted_caller_token", SecretStr(TOKEN))
    state = PlanningState(_reflex_internal_init=True)

    async def submit():
        updates = PlanningState.load_case.fn(
            state, {"case_id": payload["case_id"], "token": "ignored"}
        )
        await anext(updates)
        assert state.is_loading and not state.has_case and state.plans == []
        async for _ in updates:
            pass
        assert not state.is_loading and TOKEN not in str(state.dict())

    asyncio.run(submit())
    assert state.has_case and state.plans
    asyncio.run(submit())
    assert not state.has_case and state.details == {} and state.plans == [] and state.error_message
    asyncio.run(submit())
    assert state.has_case and not state.error_message
    assert planning_page() is not None
    assert FrontendSettings(_env_file=None).planning_cases_url.endswith(
        "/api/v2/procurement/planning-cases"
    )


def test_creation_lost_response_exact_recovery_outage_and_stored_retrieval(tmp_path, monkeypatch):
    directory = tmp_path / "model"
    payload = controlled_assets(directory)
    fixture = tmp_path / "create-request.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(FrontendSettings, "controlled_demo_file", property(lambda _: fixture))
    monkeypatch.setattr(backend_settings, "t12_trusted_caller_token", SecretStr(TOKEN))
    monkeypatch.setattr(frontend_settings, "t12_trusted_caller_token", SecretStr(TOKEN))
    monkeypatch.setattr(backend_settings, "t15_trusted_model_directory", directory)
    uow = MemoryPlanningUnitOfWork()
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    calls = []
    asgi = httpx.ASGITransport(app=app)

    async def lose_first_response(request):
        calls.append((request.url.path, request.headers["Idempotency-Key"], request.content))
        if len(calls) == 2:
            return httpx.Response(401, text=TOKEN)
        response = await asgi.handle_async_request(request)
        if len(calls) == 1:
            assert response.status_code == 201 and len(uow.rows) == 1
            raise httpx.ReadTimeout("Response lost after commit", request=request)
        return response

    async def post(url, body, key, token):
        return await submit_planning_request(
            url, body, key, token, transport=httpx.MockTransport(lose_first_response)
        )

    monkeypatch.setattr("frontend.app.submit_planning_request", post)
    state = PlanningState(_reflex_internal_init=True)
    PlanningState.prepare_demo.fn(state)
    assert state.demo_ready and state.demo_offers

    async def event(handler, *args):
        async for _ in handler.fn(state, *args):
            assert state.is_loading

    asyncio.run(event(PlanningState.create_demo, {"quantity": "10", "token": "ignored"}))
    assert state.has_pending and not state.has_case and len(calls) == 1
    recovery = json.loads(state.recovery_json)
    expected = deepcopy(payload)
    expected["approval_reference"] = "controlled-demand-10-t16-v1"
    expected["requirement_source"] = {
        "source_type": "controlled_business_terms",
        "source_reference": "t16-ui-demand-v1",
        "observed_at": payload["as_of"],
    }
    assert recovery["payload"] == expected and recovery["key"] == state.request_key
    assert json.loads(fixture.read_text(encoding="utf-8")) == payload
    assert TOKEN not in str(state.dict()) and TOKEN not in state.recovery_json
    asyncio.run(event(PlanningState.create_demo, {"quantity": "11"}))
    assert len(calls) == 1  # Changed intent cannot replace an uncertain request.
    asyncio.run(event(PlanningState.recover_request))
    assert state.has_pending and len(uow.rows) == 1
    assert state._pending["key"] == recovery["key"]
    asyncio.run(event(PlanningState.create_demo, {"quantity": "11"}))
    assert len(calls) == 2
    asyncio.run(event(PlanningState.recover_request))
    assert calls[0] == calls[1] == calls[2] and len(uow.rows) == 1
    assert state.has_case and not state.has_pending
    assert [p["cost"] for p in state.plans] == ["102 EUR", "109 EUR"]
    assert state.plans[0]["exposure_display"] == "98.6 / 100"
    assert state.plans[1]["premium_display"] == "+7 EUR (+6.9%) above minimum"
    base_id = state.details["case_id"]
    snapshot = uow.rows[base_id].snapshot
    for name in ("infer_planning_features", "resolve_odoo_planning_input"):
        monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
    asyncio.run(
        event(PlanningState.run_outage, {"supplier": payload["suppliers"][0]["supplier_id"]})
    )
    assert state.details["parent_id"] == base_id and state.details["base_id"] == base_id
    assert state.plans[0]["cost"] == "106 EUR" and len(uow.rows) == 2
    assert uow.rows[base_id].snapshot == snapshot
    assert calls[3][1] != calls[0][1]
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    display, error = asyncio.run(
        fetch_planning_case(
            frontend_settings.planning_cases_url, state.details["case_id"], TOKEN, transport=asgi
        )
    )
    assert not error and display.details == state.details
    assert display.assessments[0]["class_label"] in ("Schedule regular", "Schedule watch")
    assert "completed receipts" in display.assessments[0]["history_summary"]


@pytest.mark.parametrize(
    "status,uncertain", [(401, False), (409, False), (422, False), (503, True), (302, True)]
)
def test_post_errors_keep_secrets_private_and_never_retry(status, uncertain):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(status, text=TOKEN, headers={"Location": "http://elsewhere.test"})

    display, error, pending = asyncio.run(
        submit_planning_request(
            "http://api.test/cases",
            {"synthetic": True},
            str(uuid4()),
            TOKEN,
            transport=httpx.MockTransport(respond),
        )
    )
    assert display is None and error and TOKEN not in error and pending is uncertain
    assert len(calls) == 1 and calls[0].method == "POST"


@pytest.mark.parametrize("quantity", ["0", "1001", "1.5", "-1", "١٠", 10, "x" * 100])
def test_invalid_demo_quantity_never_posts(quantity):
    state = PlanningState(_reflex_internal_init=True)
    state.demo_ready = True

    async def submit():
        async for _ in PlanningState.create_demo.fn(state, {"quantity": quantity}):
            pass

    asyncio.run(submit())
    assert state.error_message and not state.has_pending and not state._pending
