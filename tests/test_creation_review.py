"""Group selection, read-only review and attributed saves on the Odoo-history flow."""

import asyncio
import json
from copy import deepcopy

import httpx
import pytest
from pydantic import SecretStr

from backend.app.config import settings as backend_settings
from backend.app.main import app
from frontend.config import settings as frontend_settings
from frontend.odoo_history_client import fetch_odoo_history, fetch_quotation_groups
from frontend.planning.state import PlanningState
from frontend.planning_client import submit_planning_request
from tests.test_odoo_purchase_history import configured as configured
from tests.test_odoo_purchase_history import history as history

TOKEN = "history-test-token"


def consume(state, handler, *args):
    async def run():
        return [event async for event in handler.fn(state, *args)]

    return asyncio.run(run())


@pytest.fixture
def prepared_state(configured, monkeypatch):
    """A cockpit that listed the open groups, chose group 501 and read its history preview."""
    asgi = httpx.ASGITransport(app=app)
    monkeypatch.setattr(frontend_settings, "backend_base_url", "http://api.test")
    monkeypatch.setattr(frontend_settings, "api_service_token", SecretStr(TOKEN))
    monkeypatch.setattr(backend_settings, "planning_library_company_id", "odoo:res.company:1")
    for name, function in (
        ("fetch_quotation_groups", fetch_quotation_groups),
        ("fetch_odoo_history", fetch_odoo_history),
    ):

        async def through_api(*args, function=function, **kwargs):
            return await function(*args, **kwargs, transport=asgi)

        monkeypatch.setattr(f"frontend.planning.state.{name}", through_api)
    state = PlanningState(_reflex_internal_init=True)
    consume(state, PlanningState.load_quotation_groups)
    assert [g["value"] for g in state.quotation_groups] == ["501"], state.error_message
    assert (
        state.selected_group == "501"
        and "T6 Comparison Product" in (state.quotation_groups[0]["label"])
    )
    consume(state, PlanningState.load_odoo_history)
    assert state.odoo_ready and state.odoo_history_mode, state.error_message
    terms = state._odoo_payload["controlled_input"]
    form = {
        "odoo_quantity": str(terms["requirement"]["approved_quantity"]),
        "odoo_required_date": terms["requirement"]["required_date"],
    }
    for s in terms["suppliers"]:
        form.update(
            {
                s["supplier_id"] + "_capacity": str(s["capacity"]),
                s["supplier_id"] + "_moq": "5",
                s["supplier_id"] + "_promised_date": s["promised_date"],
            }
        )
    return state, form


def test_group_choice_is_limited_to_listed_selectable_groups(prepared_state):
    state, _ = prepared_state
    PlanningState.select_quotation_group.fn(state, "999")
    assert state.selected_group == "501"
    state.selected_group = ""
    consume(state, PlanningState.load_odoo_history)
    assert "choose an open Odoo quotation group" in state.error_message


def test_switching_group_drops_the_loaded_preview(prepared_state):
    state, form = prepared_state
    PlanningState.review_odoo.fn(state, form)
    assert state._review_payload and state.odoo_ready
    PlanningState.select_quotation_group.fn(state, "501")  # same group: preview stays
    assert state._review_payload and state.odoo_ready and state.odoo_offers
    state.quotation_groups = [*state.quotation_groups, {"value": "502", "selectable": "yes"}]
    PlanningState.select_quotation_group.fn(state, "502")
    assert state.selected_group == "502"
    assert not state.odoo_ready and not state.odoo_history_mode
    assert not state._review_payload and not state.creation_review
    assert not state._odoo_payload and not state.odoo_offers and not state.odoo_history_rows
    assert state.odoo_history_readiness == ""


def test_review_has_no_io_and_save_replays_identical_classified_intent(
    configured, prepared_state, monkeypatch
):
    upstream, uow = configured
    state, form = prepared_state
    original = deepcopy(state._odoo_payload)
    supplier = original["controlled_input"]["suppliers"][0]["supplier_id"]
    form[supplier + "_moq"] = ""
    form["unit_price"] = "0"
    requests = []
    asgi = httpx.ASGITransport(app=app)

    async def lose_first(request):
        requests.append((request.content, request.headers["Idempotency-Key"]))
        response = await asgi.handle_async_request(request)
        if len(requests) == 1:
            assert response.status_code == 201, response.text
            raise httpx.ReadTimeout("Lost after commit", request=request)
        return response

    async def post(url, payload, key, token):
        return await submit_planning_request(
            url, payload, key, token, transport=httpx.MockTransport(lose_first)
        )

    monkeypatch.setattr("frontend.planning.state.submit_planning_request", post)
    read_before = len(upstream)
    PlanningState.review_odoo.fn(state, form)
    assert not requests and len(upstream) == read_before and not uow.rows
    assert not state.has_pending
    reviewed = deepcopy(state._review_payload)
    assert reviewed["purchase_group_id"] == 501
    assert reviewed["terms"]["suppliers"][0]["minimum_order_quantity"] is None
    assert state.review_suppliers[0]["moq"] == "None (no MOQ)"
    assert state.creation_review["captured"] == original["controlled_input"]["as_of"]
    assert state.creation_review["history_source"].startswith("Odoo purchase history")
    assert state._odoo_payload == original
    consume(state, PlanningState.save_reviewed_creation)
    assert len(requests) == 1 and state.has_pending and len(uow.rows) == 1
    assert state.comparison_state == "Save response unconfirmed — recover the same request"
    recovery = json.loads(state.recovery_json)
    assert recovery["payload"] == reviewed
    assert recovery["url"].endswith("/from-odoo-history")
    PlanningState.edit_creation_terms.fn(state)
    PlanningState.review_odoo.fn(state, form | {"odoo_quantity": "201"})
    consume(state, PlanningState.save_reviewed_creation)
    assert json.loads(state.recovery_json) == recovery and len(requests) == 1
    upstream_before = list(upstream)
    consume(state, PlanningState.recover_request)
    assert requests[0] == requests[1] and len(uow.rows) == 1 and upstream == upstream_before
    assert state.has_case and not state.has_pending and not state._review_payload
    assert state.details["origin"] == "odoo"
    assert state.notice == "Comparison saved. Approval is a separate choice."
    assert state.comparison_state == "Saved comparison — awaiting a decision"
    assert not state.final_choice and not state.details["final_outcome"]


@pytest.mark.parametrize(
    "field,value,identity",
    [
        ("odoo_quantity", "0", "odoo-quantity"),
        ("odoo_quantity", "١٠", "odoo-quantity"),
        ("odoo_required_date", "2020-01-01", "odoo-required-date"),
        ("odoo:res.partner:301_capacity", "-1", "odoo:res.partner:301_capacity"),
        ("odoo:res.partner:301_moq", "0", "odoo:res.partner:301_moq"),
        ("odoo:res.partner:301_promised_date", "bad", "odoo:res.partner:301_promised_date"),
    ],
)
def test_review_field_errors_cannot_create_intent(prepared_state, field, value, identity):
    state, form = prepared_state
    result = PlanningState.review_odoo.fn(state, form | {field: value})
    assert result and identity in state.creation_errors
    assert not state._review_payload and not state._pending and not state.request_key


def test_edit_and_malformed_prepared_data_remove_review(prepared_state):
    state, form = prepared_state
    PlanningState.review_odoo.fn(state, form)
    assert state._review_payload
    PlanningState.edit_creation_terms.fn(state)
    assert not state._review_payload and state.creation_dirty
    state._odoo_payload["controlled_input"]["suppliers"][0]["available"] = "false"
    PlanningState.review_odoo.fn(state, form)
    assert not state._review_payload and "incomplete" in state.error_message


def test_reviewed_required_date_cannot_expire_into_a_new_save(prepared_state):
    state, form = prepared_state
    PlanningState.review_odoo.fn(state, form)
    state.creation_review["required_date"] = "2020-01-01"
    consume(state, PlanningState.save_reviewed_creation)
    assert "now past" in state.error_message and not state._pending and not state.request_key


def test_failed_new_save_does_not_treat_previous_case_as_success(prepared_state, monkeypatch):
    state, form = prepared_state
    state.has_case = True
    state.details = {"case_id": "previous-case"}
    PlanningState.review_odoo.fn(state, form)

    async def failed(*args):
        return None, "Planning access was denied.", False

    monkeypatch.setattr("frontend.planning.state.submit_planning_request", failed)
    events = consume(state, PlanningState.save_reviewed_creation)
    assert events == [None] and state._review_payload and state.error_message
    assert state.details["case_id"] == "previous-case" and not state.has_pending


def test_unavailable_group_listing_is_actionable(monkeypatch):
    async def unavailable(*args, **kwargs):
        return await fetch_quotation_groups(
            "http://api.test/groups",
            "token",
            transport=httpx.MockTransport(lambda request: httpx.Response(503)),
        )

    monkeypatch.setattr("frontend.planning.state.fetch_quotation_groups", unavailable)
    state = PlanningState(_reflex_internal_init=True)
    consume(state, PlanningState.load_quotation_groups)
    assert state.quotation_groups == [] and state.selected_group == ""
    assert "unavailable" in state.error_message and not state.is_loading
