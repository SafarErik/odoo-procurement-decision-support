"""Review is read-only; deliberate saves retain attribution and exact uncertain intent."""

import asyncio
import json
from copy import deepcopy

import httpx
import pytest

from backend.app.main import app
from frontend.planning.state import PlanningState
from frontend.planning_client import submit_planning_request
from tests.test_t15_odoo_planning import assets as assets
from tests.test_t15_odoo_planning import configured as configured
from tests.test_t16_odoo_planning import prepared_state as prepared_state


def consume(state, handler):
    async def run():
        return [event async for event in handler.fn(state)]

    return asyncio.run(run())


def test_review_has_no_io_and_save_replays_identical_classified_intent(
    configured, prepared_state, monkeypatch
):
    uow, original, _, _, upstream = configured
    state, form = prepared_state
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
    PlanningState.review_odoo.fn(state, form)
    assert not requests and not upstream and not uow.rows and not state.has_pending
    reviewed = deepcopy(state._review_payload)
    assert reviewed["controlled_input"]["suppliers"][0]["minimum_order_quantity"] is None
    assert state.review_suppliers[0]["moq"] == "None (no MOQ)"
    assert state.creation_review["captured"] == original["controlled_input"]["as_of"]
    assert state.creation_review["cutoff"] != state.creation_review["captured"]
    assert state._odoo_payload == original
    consume(state, PlanningState.save_reviewed_creation)
    assert len(requests) == 1 and state.has_pending and len(uow.rows) == 1 and upstream
    assert state.comparison_state == "Save response unconfirmed — recover the same request"
    recovery = json.loads(state.recovery_json)
    assert recovery["payload"] == reviewed
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
