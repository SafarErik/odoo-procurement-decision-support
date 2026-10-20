"""Review/cancel are read-only; confirmation freezes the original decision intent."""

import asyncio
from copy import deepcopy
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from backend.app.main import app
from frontend.config import settings
from frontend.i18n import tr
from frontend.planning.state import PlanningState
from frontend.planning_client import _map_case, fetch_planning_case, submit_planning_request
from tests.frontend_patching import patch_client
from tests.test_t17_decisions import TOKEN, intent
from tests.test_t17_decisions import configured as configured
from tests.test_t17_decisions import stored_cases as stored_cases


def consume(state, handler):
    async def run():
        return [event async for event in handler.fn(state)]

    return asyncio.run(run())


@pytest.fixture
def prepared(configured, monkeypatch):
    _, uow, base, child, *_ = configured
    state = PlanningState(_reflex_internal_init=True)
    state.lang = "en"  # the assertions below read English texts
    state._show(_map_case(base, base["case_id"]))
    monkeypatch.setattr(settings, "backend_base_url", "http://test")
    monkeypatch.setattr(settings, "api_service_token", SecretStr(TOKEN))
    posts = []

    async def send(url, payload, key, token, lang="en"):
        posts.append((url, deepcopy(payload), key))
        return await submit_planning_request(
            url, payload, key, token, lang=lang, transport=httpx.ASGITransport(app=app)
        )

    patch_client(monkeypatch, "submit_planning_request", send)
    return state, uow, base, child, posts


def form(choice="Alternative 1", **changes):
    return {
        "choice": choice,
        "actor": "review buyer",
        "reason": "Prefer exposure",
        "demonstration": "on",
    } | changes


def test_review_cancel_confirm_freezes_exact_intent_and_cannot_double_save(prepared):
    state, uow, base, _, posts = prepared
    assert state.comparison_state == tr("state_awaiting", "en")
    state.choose_final_plan("Alternative 1")
    assert state.comparison_state == tr("state_selected", "en")
    assert not posts and not uow.decisions.rows
    submitted = form()
    state.review_final_decision(submitted)
    expected = deepcopy(state._decision_payload)
    assert state.decision_open and state.decision_review["choice"] == "Alternative 1"
    assert state.decision_review["cost"] == "€109.00"
    assert not state.has_pending and not posts and not uow.decisions.rows
    state.change_decision_confirmation(False)
    assert not state.decision_open and not state._decision_payload and not posts
    assert state.final_choice == "Alternative 1"
    assert state.comparison_state == tr("state_selected", "en")
    state.review_final_decision(submitted)
    submitted["actor"] = "different unreviewed value"
    events = consume(state, PlanningState.confirm_final_decision)
    assert len(posts) == 1 and posts[0][1] == expected
    assert posts[0][0].endswith(f"/{base['case_id']}/final-decision")
    assert state.details["final_outcome"] == "Approved" and not state.decision_open
    assert "saved-decision-heading" in str(events)
    assert len(uow.decisions.rows) == 1
    assert state.comparison_state == tr("state_approved", "en")
    assert consume(state, PlanningState.confirm_final_decision) == [] and len(posts) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"choice": ""},
        {"choice": "invented"},
        {"actor": " "},
        {"reason": " "},
        {"reason": "x" * 2001},
        {"demonstration": ""},
    ],
)
def test_invalid_review_and_confirm_without_review_never_post(prepared, changes):
    state, _, _, _, posts = prepared
    state.review_final_decision(form(**changes))
    assert not state.decision_open and state.error_message
    assert consume(state, PlanningState.confirm_final_decision) == [] and not posts


@pytest.mark.parametrize(
    "field,value",
    [
        ("case_id", str(uuid4())),
        ("snapshot_hash", "changed"),
        ("parent_id", str(uuid4())),
        ("final_outcome", "No-award"),
    ],
)
def test_changed_context_invalidates_confirmation(prepared, field, value):
    state, _, _, _, posts = prepared
    state.review_final_decision(form())
    state.details[field] = value
    consume(state, PlanningState.confirm_final_decision)
    assert not posts and not state.decision_open and "changed" in state.error_message


def test_no_award_requires_reason_has_no_plan_and_child_cannot_review(prepared):
    state, _, _, child, posts = prepared
    state.review_final_decision(form("No-award", reason=" "))
    assert not state.decision_open and not posts
    state.review_final_decision(form("No-award", reason="Decline the saved options"))
    assert "cost" not in state.decision_review
    consume(state, PlanningState.confirm_final_decision)
    assert posts[0][1]["outcome"] == "no_award" and posts[0][1]["plan_index"] is None
    assert state.details["final_outcome"] == "No-award"
    assert state.comparison_state == tr("state_no_award", "en")
    state._show(_map_case(child, child["case_id"]))
    assert state.comparison_state == tr("state_scenario", "en")
    state.review_final_decision(form("No-award"))
    assert not state.decision_open and len(posts) == 1


def test_minimum_cost_also_requires_deliberate_buyer_rationale(prepared):
    state, _, _, _, posts = prepared
    state.review_final_decision(form("Minimum cost", reason=" "))
    assert not state.decision_open and not posts
    assert state.error_message == tr("err_reason", "en")
    state.review_final_decision(form("Minimum cost", reason="The cost saving fits our needs."))
    assert state.decision_open and not posts


@pytest.mark.parametrize("recovering", [False, True])
def test_conflict_blocks_further_posts_and_reopens_recorded_decision_only(
    prepared, configured, monkeypatch, recovering
):
    state, uow, base, _, posts = prepared
    client = configured[0]
    if recovering:
        state._prepare_request(
            "http://test/api/v2/procurement/planning-cases/" + base["case_id"] + "/final-decision",
            intent(base, index=1),
        )
        state.is_loading = False
    saved = client.post(
        f"/api/v2/procurement/planning-cases/{base['case_id']}/final-decision",
        json=intent(base),
        headers={"Authorization": f"Bearer {TOKEN}", "Idempotency-Key": str(uuid4())},
    )
    assert saved.status_code == 201
    if recovering:
        consume(state, PlanningState.recover_request)
        pending = deepcopy(state._pending)
        assert state.has_pending
    else:
        state.review_final_decision(form())
        consume(state, PlanningState.confirm_final_decision)
    assert state.decision_conflict and state.error_message == tr("err_decision_conflict", "en")
    assert state.comparison_state == tr("state_conflict", "en")
    assert "request-recovery-heading" in str(PlanningState.focus_pending_save.fn(state))
    assert len(posts) == len(uow.decisions.rows) == 1
    recovery = state.recovery_json
    state.review_final_decision(form())
    consume(state, PlanningState.confirm_final_decision)
    consume(state, PlanningState.recover_request)
    assert len(posts) == 1 and not state.decision_open

    async def unavailable(*args, **kwargs):
        return None, "Planning data is unavailable."

    patch_client(monkeypatch, "fetch_planning_case", unavailable)
    consume(state, PlanningState.reopen_conflicted_decision)
    assert state.decision_conflict and state.recovery_json == recovery
    if recovering:
        assert state._pending == pending and state.has_pending

    async def no_record(*args, **kwargs):
        return _map_case(base, base["case_id"]), ""

    patch_client(monkeypatch, "fetch_planning_case", no_record)
    consume(state, PlanningState.reopen_conflicted_decision)
    assert state.decision_conflict and "No recorded decision" in state.error_message
    assert state.recovery_json == recovery and len(posts) == 1

    async def fetch(url, case_id, token, lang="en"):
        return await fetch_planning_case(
            url, case_id, token, lang=lang, transport=httpx.ASGITransport(app=app)
        )

    patch_client(monkeypatch, "fetch_planning_case", fetch)
    consume(state, PlanningState.reopen_conflicted_decision)
    assert not state.has_pending and not state.decision_conflict
    assert state.details["final_plan"] == "Minimum cost"
    assert state.details["snapshot_hash"] == base["snapshot_hash"]
    assert len(posts) == len(uow.decisions.rows) == 1
