"""Reflex terms -> live-read adapter contract -> saved tree/CBC; stored-only recovery."""

import asyncio
import json
from copy import deepcopy
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from backend.app.main import app
from frontend.app import PlanningState, planning_page
from frontend.config import FrontendSettings
from frontend.config import settings as frontend_settings
from frontend.planning_client import fetch_planning_case, submit_planning_request
from tests.test_t15_odoo_planning import assets as assets
from tests.test_t15_odoo_planning import configured as configured
from tests.test_t15_odoo_planning import forbidden

TOKEN = "controlled-test-token"


@pytest.fixture
def prepared_state(assets, monkeypatch):
    directory, payload, _ = assets
    monkeypatch.setattr(
        FrontendSettings,
        "controlled_odoo_file",
        property(lambda _: directory / "create-request.json"),
    )
    monkeypatch.setattr(frontend_settings, "t12_trusted_caller_token", SecretStr(TOKEN))
    state = PlanningState(_reflex_internal_init=True)
    PlanningState.prepare_odoo.fn(state)
    assert state.odoo_ready
    form = {
        "odoo_quantity": "200",
        "odoo_required_date": payload["controlled_input"]["requirement"]["required_date"],
    }
    for s in payload["controlled_input"]["suppliers"]:
        form.update(
            {
                s["supplier_id"] + "_capacity": str(s["capacity"]),
                s["supplier_id"] + "_moq": str(s["minimum_order_quantity"]),
                s["supplier_id"] + "_promised_date": s["promised_date"],
            }
        )
    return state, form


async def event(state, handler, *args):
    async for effect in handler.fn(state, *args):
        if effect is None:
            assert state.is_loading
    assert not state.is_loading


def test_odoo_creation_lost_response_exact_recovery_outage_and_get(
    configured,
    prepared_state,
    monkeypatch,
):
    uow, payload, _, _, odoo_calls = configured
    state, form = prepared_state
    asgi, requests = httpx.ASGITransport(app=app), []

    async def lose_response(request):
        requests.append((request.url.path, request.headers["Idempotency-Key"], request.content))
        response = await asgi.handle_async_request(request)
        if len(requests) == 1:
            assert response.status_code == 201, response.text
            raise httpx.ReadTimeout("Lost after commit", request=request)
        return response

    async def post(url, body, key, token):
        return await submit_planning_request(
            url,
            body,
            key,
            token,
            transport=httpx.MockTransport(lose_response),
        )

    monkeypatch.setattr("frontend.planning.state.submit_planning_request", post)
    form.update({"token": "ignored", "unit_price": "0", "model_directory": "ignored"})
    asyncio.run(event(state, PlanningState.create_odoo, form))
    assert state.has_pending and not state.has_case and len(uow.rows) == 1
    recovery = json.loads(state.recovery_json)
    submitted = recovery["payload"]["controlled_input"]
    assert submitted["requirement"]["approved_quantity"] == 200
    for expected, actual in zip(payload["controlled_input"]["suppliers"], submitted["suppliers"]):
        assert actual["unit_price"] == expected["unit_price"]
        assert actual["receipts"] == expected["receipts"]
        assert actual["source"]["source_reference"] == "t16-ui-odoo-terms-v1"
    assert state._odoo_payload == payload and TOKEN not in str(state.dict())
    assert TOKEN not in state.recovery_json and "model_directory" not in state.recovery_json
    assert odoo_calls
    read_count = len(odoo_calls)
    for name in ("resolve_odoo_planning_input", "infer_planning_features"):
        monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
    asyncio.run(event(state, PlanningState.create_odoo, {**form, "odoo_quantity": "201"}))
    assert len(requests) == 1
    asyncio.run(event(state, PlanningState.recover_request))
    assert requests[0] == requests[1] and len(uow.rows) == 1
    assert state.has_case and not state.has_pending and not state.error_message
    assert [p["cost"] for p in state.plans] == ["1,850 USD", "2,200 USD"]
    base_id = state.details["case_id"]
    snapshot = deepcopy(uow.rows[base_id].snapshot)
    provenance = {e["canonical_path"]: e for e in json.loads(snapshot)["provenance"]["entries"]}
    assert (
        provenance["request.requirement.approved_quantity"]["source_reference"]
        == "t16-ui-odoo-terms-v1"
    )
    assert (
        provenance["request.suppliers[odoo:res.partner:301].unit_price"]["source_type"]
        == "odoo_json2"
    )
    asyncio.run(
        event(
            state,
            PlanningState.run_scenario,
            {
                "kind": "supplier_outage",
                "supplier": payload["controlled_input"]["suppliers"][-1]["supplier_id"],
            },
        )
    )
    assert state.plans[0]["cost"] == "2,200 USD" and len(uow.rows) == 2
    assert state.details["parent_id"] == base_id
    assert uow.rows[base_id].snapshot == snapshot and len(odoo_calls) == read_count
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    display, error = asyncio.run(
        fetch_planning_case(
            frontend_settings.planning_cases_url,
            state.details["case_id"],
            TOKEN,
            transport=asgi,
        )
    )
    assert not error and display.details == state.details and len(odoo_calls) == read_count
    assert planning_page() is not None


def test_changed_odoo_price_rejected_without_persistence(configured, prepared_state, monkeypatch):
    uow, _, _, upstream, _ = configured
    state, form = prepared_state
    upstream["lines"][0]["price_unit"] = 99
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)

    async def post(url, body, key, token):
        return await submit_planning_request(
            url, body, key, token, transport=httpx.ASGITransport(app=app)
        )

    monkeypatch.setattr("frontend.planning.state.submit_planning_request", post)
    asyncio.run(event(state, PlanningState.create_odoo, form))
    assert not uow.rows and not state.has_case and not state.has_pending
    assert "re-prepare" in state.error_message


@pytest.mark.parametrize(
    "field,value",
    [
        ("odoo_quantity", "0"),
        ("odoo_quantity", "1001"),
        ("odoo_quantity", "١٠"),
        ("odoo_quantity", 200),
        ("odoo_required_date", "2020-01-01"),
        ("odoo_required_date", "2026-02-30"),
        ("odoo:res.partner:301_capacity", "-1"),
        ("odoo:res.partner:301_moq", "0"),
        ("odoo:res.partner:301_promised_date", "invalid"),
    ],
)
def test_invalid_terms_never_post(prepared_state, monkeypatch, field, value):
    state, form = prepared_state
    monkeypatch.setattr("frontend.planning.state.submit_planning_request", forbidden)
    asyncio.run(event(state, PlanningState.create_odoo, {**form, field: value}))
    assert state.error_message and not state.has_pending and not state._pending


def test_blank_moq_and_changed_terms_are_explicit(prepared_state, monkeypatch):
    state, form = prepared_state
    captured = []

    async def post(url, payload, key, token):
        captured.append(payload)
        return None, "Unavailable", True

    monkeypatch.setattr("frontend.planning.state.submit_planning_request", post)
    form.update({"odoo:res.partner:301_moq": "", "odoo:res.partner:301_capacity": "0"})
    asyncio.run(event(state, PlanningState.create_odoo, form))
    supplier = captured[0]["controlled_input"]["suppliers"][0]
    assert supplier["minimum_order_quantity"] is None and supplier["capacity"] == 0
    assert state.has_pending


@pytest.mark.parametrize("change", ["source", "group"])
def test_response_must_match_odoo_source_and_group(configured, change):
    _, payload, _, _, _ = configured
    transport = httpx.ASGITransport(app=app)

    async def corrupt(request):
        response = await transport.handle_async_request(request)
        await response.aread()
        data = json.loads(response.content)
        assert response.status_code == 201, data
        facts = data["snapshot"]["facts"]
        if change == "source":
            facts["input_kind"] = "controlled_synthetic"
        else:
            facts["comparison_case_id"] = "odoo:purchase.order.group:999"
        return httpx.Response(201, json=data)

    display, error, pending = asyncio.run(
        submit_planning_request(
            frontend_settings.planning_cases_url + "/from-odoo",
            payload,
            str(uuid4()),
            TOKEN,
            transport=httpx.MockTransport(corrupt),
        )
    )
    assert display is None and error and pending


def test_missing_preparation_is_actionable(tmp_path, monkeypatch):
    monkeypatch.setattr(
        FrontendSettings, "controlled_odoo_file", property(lambda _: tmp_path / "missing")
    )
    state = PlanningState(_reflex_internal_init=True)
    PlanningState.prepare_odoo.fn(state)
    assert not state.odoo_ready and not state._odoo_payload
    assert "offline" in state.error_message
