"""Finalization selection, HTTP uncertainty and stored outcome presentation."""

import asyncio
from copy import deepcopy

import httpx
import pytest
from pydantic import SecretStr

from backend.app.main import app
from frontend.config import settings as frontend_settings
from frontend.planning.page import planning_page
from frontend.planning.state import PlanningState
from frontend.planning_client import fetch_planning_case, submit_planning_request
from tests.frontend_patching import patch_client
from tests.test_t17_decisions import BASE, TOKEN, intent
from tests.test_t17_decisions import configured as _configured
from tests.test_t17_decisions import stored_cases as _stored_cases

configured = _configured
stored_cases = _stored_cases


def test_explicit_selection_and_lost_success_response_recovery(configured, monkeypatch):
    _, uow, base, *_ = configured
    monkeypatch.setattr(frontend_settings, "backend_base_url", "http://test")
    monkeypatch.setattr(frontend_settings, "api_service_token", SecretStr(TOKEN))
    transport = httpx.ASGITransport(app=app)
    lost = []

    async def send(url, payload, key, token, lang="en"):
        result = await submit_planning_request(
            url, payload, key, token, lang=lang, transport=transport
        )
        lost.append((url, deepcopy(payload), key))
        if len(lost) == 1:
            assert result[0] is not None
            return None, "Response lost; retry the same decision", True
        return result

    patch_client(monkeypatch, "submit_planning_request", send)

    async def flow():
        display, error = await fetch_planning_case(
            "http://test" + BASE, base["case_id"], TOKEN, transport=transport
        )
        assert not error
        state = PlanningState(_reflex_internal_init=True)
        state.lang = "en"  # the assertions below read English texts
        state._show(display)
        assert state.final_choice == "" and state.details["final_outcome"] == ""
        form = {
            "choice": "",
            "actor": "test buyer",
            "reason": "prefer exposure",
            "demonstration": "on",
        }
        state.review_final_decision(form)
        assert not lost and "Choose a plan or No award" in state.error_message
        form["choice"] = "Alternative 1"
        state.review_final_decision(form)
        assert not lost and state.decision_open
        async for _ in state.confirm_final_decision():
            pass
        assert state.has_pending and not state.is_loading and not state.details["final_outcome"]
        pending = deepcopy(state._pending)
        assert "test buyer" in state.recovery_json and TOKEN not in state.recovery_json
        assert len(uow.decisions.rows) == 1
        state.review_final_decision(form | {"choice": "No-award"})
        assert len(lost) == 1 and state._pending == pending
        async for _ in state.recover_request():
            pass
        assert not state.has_pending and state.details["final_outcome"] == "Approved"
        assert state.details["final_plan"] == "Alternative 1"
        assert lost[0] == lost[1] and len(uow.decisions.rows) == 1
        loaded, error = await fetch_planning_case(
            "http://test" + BASE, base["case_id"], TOKEN, transport=transport
        )
        assert not error and loaded.details["final_audit"] == state.details["final_audit"]

    asyncio.run(flow())


@pytest.mark.parametrize("status", [409, 422, 503, 302])
def test_rejected_and_uncertain_finalization_responses(configured, status):
    _, _, base, *_ = configured
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status, json={"detail": "failure"})
    )

    async def run():
        return await submit_planning_request(
            "http://test" + BASE + f"/{base['case_id']}/final-decision",
            intent(base),
            base["case_id"],
            TOKEN,
            transport=transport,
        )

    result, error, uncertain = asyncio.run(run())
    assert result is None and error and uncertain == (status in (503, 302))


def test_no_award_and_scenario_controls_and_unavailable_load(configured, monkeypatch):
    _, _, base, child, *_ = configured

    async def unavailable(*args, **kwargs):
        return None, "Backend unavailable"

    patch_client(monkeypatch, "fetch_planning_case", unavailable)

    async def run():
        state = PlanningState(_reflex_internal_init=True)
        state.lang = "en"  # the assertions below read English texts
        state.details = {"final_outcome": "Approved"}
        state.has_case = True
        async for _ in state.load_case({"case_id": base["case_id"]}):
            pass
        assert not state.has_case and state.details == {} and state.error_message
        state.has_case = True
        state.details = {"parent_id": child["case_id"], "final_outcome": ""}
        state.review_final_decision({})
        assert "undecided base case" in state.error_message and not state.has_pending

    asyncio.run(run())
    rendered = str(planning_page())
    # Both languages are compiled into the page; the English texts are plain ASCII here.
    assert "Record no award" in rendered and "Review approval" in rendered
    assert "creates no Odoo order" in rendered
    assert "A scenario cannot be decided" in rendered
