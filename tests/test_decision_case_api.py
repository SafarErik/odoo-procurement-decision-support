"""Trusted HTTP boundary and stored-case lifecycle contracts for T12."""

import asyncio
from threading import Event, Lock
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from application.rfqs import ProcurementDataResponseError, ProcurementDataUnavailable
from backend.app.config import settings
from backend.app.main import app
from tests.test_decision_case_orchestration import (
    FakeComparisonReader,
    FakeCreations,
    FakeHistoryReader,
    FakeUnitOfWork,
    _command,
)

client = TestClient(app)
BASE = "/api/v1/procurement/decision-cases"


@pytest.fixture
def configured(monkeypatch):
    import backend.app.routes.decision_cases as routes

    uow = FakeUnitOfWork()
    comparison = FakeComparisonReader()
    history = FakeHistoryReader()
    monkeypatch.setattr(settings, "t12_trusted_caller_token", SecretStr("test-only-shared-secret"))
    monkeypatch.setattr(routes, "get_decision_unit_of_work", lambda: uow)
    monkeypatch.setattr(routes, "get_comparison_case_reader", lambda: comparison)
    monkeypatch.setattr(routes, "get_historical_performance_reader", lambda: history)
    return uow, comparison, history


def _headers(key=None, token="test-only-shared-secret"):
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": key or str(uuid4())}


def _payload():
    command = _command()

    def source(value):
        return {
            "value": format(value.value, "f"),
            "source_type": value.attribution.source_type,
            "source_reference": value.attribution.source_reference,
            "observed_at": value.attribution.observed_at.isoformat(),
        }

    return {
        "purchase_group_id": 501,
        "scoring_policy_id": "cost-focused",
        "supplemental_terms": [
            {
                "offer_id": item.offer_id,
                "hard_minimum_order_quantity": source(item.hard_minimum_order_quantity),
                "supplier_promised_lead_time_days": source(item.supplier_promised_lead_time_days),
            }
            for item in command.supplemental_terms
        ],
    }


def test_create_replay_get_finalize_and_stored_snapshots(configured, monkeypatch):
    _, comparison, history = configured
    key = str(uuid4())
    headers = _headers(key)
    first = client.post(BASE, json=_payload(), headers=headers)
    assert first.status_code == 201, first.text
    created = first.json()
    assert created["idempotent_replay"] is False
    assert created["recommended_offer_id"] is not None

    def forbidden_score(*args, **kwargs):
        raise AssertionError("Stored-case flows must not invoke a scorer")

    monkeypatch.setattr(
        "application.decision_case_orchestration.evaluate_procurement_decision",
        forbidden_score,
    )
    replay = client.post(BASE, json=_payload(), headers=headers)
    assert replay.status_code == 200
    assert replay.json()["decision_case_id"] == created["decision_case_id"]
    assert comparison.calls == 1 and history.calls == 0

    case_id = created["decision_case_id"]
    retrieved = client.get(f"{BASE}/{case_id}", headers=headers)
    assert retrieved.status_code == 200
    assert retrieved.json()["canonical_input"] == created["canonical_input"]
    assert comparison.calls == 1

    final_key = str(uuid4())
    decision = {
        "outcome": "accept_recommendation",
        "selected_offer_id": created["recommended_offer_id"],
        "rationale": None,
        "decided_at": "2026-09-22T08:30:00Z",
        "actor_reference": "buyer-supplied-label",
    }
    finalized = client.post(
        f"{BASE}/{case_id}/final-decision", json=decision, headers=_headers(final_key)
    )
    assert finalized.status_code == 200, finalized.text
    assert finalized.json()["state"] == "finalized"
    assert finalized.json()["human_decision"]["actor_reference"] == "buyer-supplied-label"
    assert finalized.json()["canonical_input"] == created["canonical_input"]
    assert finalized.json()["evaluation"] == created["evaluation"]
    assert (
        client.post(
            f"{BASE}/{case_id}/final-decision", json=decision, headers=_headers(final_key)
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"{BASE}/{case_id}/final-decision",
            json={**decision, "rationale": "changed"},
            headers=_headers(final_key),
        ).status_code
        == 409
    )
    assert comparison.calls == 1 and history.calls == 0


def test_conflict_auth_and_input_errors(configured, monkeypatch):
    _, comparison, _ = configured
    payload = _payload()
    key = str(uuid4())
    assert client.post(BASE, json=payload).status_code == 401
    assert client.post(BASE, json=payload, headers=_headers(token="wrong")).status_code == 401
    assert client.post(BASE, json=payload, headers=_headers(key)).status_code == 201
    changed = {**payload, "scoring_policy_id": "urgent"}
    conflict = client.post(BASE, json=changed, headers=_headers(key))
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "creation_idempotency_conflict"
    assert comparison.calls == 1
    assert client.get(f"{BASE}/{uuid4()}", headers=_headers()).status_code == 404
    assert (
        client.post(
            BASE, json={**payload, "supplemental_terms": []}, headers=_headers()
        ).status_code
        == 422
    )
    assert (
        client.post(
            BASE,
            json={
                **payload,
                "supplemental_terms": [
                    {
                        **payload["supplemental_terms"][0],
                        "hard_minimum_order_quantity": {
                            **payload["supplemental_terms"][0]["hard_minimum_order_quantity"],
                            "value": 1.5,
                        },
                    }
                ],
            },
            headers=_headers(),
        ).status_code
        == 422
    )
    non_utc = _payload()
    non_utc["supplemental_terms"][0]["hard_minimum_order_quantity"]["observed_at"] = (
        "2026-09-22T09:00:00+01:00"
    )
    assert client.post(BASE, json=non_utc, headers=_headers()).status_code == 422
    monkeypatch.setattr(settings, "t12_trusted_caller_token", SecretStr(""))
    assert client.get(f"{BASE}/{uuid4()}", headers=_headers()).status_code == 503


def test_openapi_describes_shared_secret_and_preserves_t3():
    schema = client.get("/openapi.json").json()
    assert BASE in schema["paths"]
    assert f"{BASE}/{{decision_case_id}}/final-decision" in schema["paths"]
    assert "/api/v1/procurement/decisions/evaluate" in schema["paths"]
    description = schema["paths"][BASE]["post"]["description"]
    assert "does not authenticate" in description
    assert "actor_reference" in description


@pytest.mark.parametrize("prefix", [BASE, "/api/v2/procurement/planning-cases"])
def test_non_ascii_bearer_is_rejected_and_invalid_configuration_fails_closed(
    configured, monkeypatch, prefix
):
    response = client.get(f"{prefix}/{uuid4()}", headers=[(b"Authorization", b"Bearer \xff")])
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    monkeypatch.setattr(settings, "t12_trusted_caller_token", SecretStr("invalid-\u00ff"))
    assert client.get(f"{prefix}/{uuid4()}", headers=_headers()).status_code == 503


def test_same_key_http_requests_share_one_event_loop_without_blocking(configured, monkeypatch):
    from backend.app.routes import decision_cases as routes

    shared, comparison, _ = configured
    key_lock, reading, waiting = Lock(), Event(), Event()

    class LockedCreations(FakeCreations):
        def lock(self, key):
            if key_lock.locked():
                waiting.set()
            self.held = key_lock.acquire(timeout=2)
            assert self.held, "The API event loop blocked the first transaction's Odoo read."

    class LockedUnitOfWork(FakeUnitOfWork):
        def __init__(self):
            super().__init__()
            self.cases = shared.cases
            self.creations = LockedCreations()
            self.creations.items = shared.creations.items

        def __exit__(self, *args):
            if self.creations.held:
                key_lock.release()

    async def delayed_read(group_id):
        reading.set()
        assert await asyncio.to_thread(waiting.wait, 2)
        return await FakeComparisonReader.read_comparison_case(comparison, group_id)

    monkeypatch.setattr(comparison, "read_comparison_case", delayed_read)
    monkeypatch.setattr(routes, "get_decision_unit_of_work", LockedUnitOfWork)

    async def send():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as concurrent_client:
            headers = _headers()
            first = asyncio.create_task(
                concurrent_client.post(BASE, json=_payload(), headers=headers)
            )
            assert await asyncio.to_thread(reading.wait, 2)
            second = asyncio.create_task(
                concurrent_client.post(BASE, json=_payload(), headers=headers)
            )
            return await asyncio.gather(first, second)

    responses = asyncio.run(send())
    assert sorted(response.status_code for response in responses) == [200, 201]
    assert responses[0].json()["decision_case_id"] == responses[1].json()["decision_case_id"]
    assert comparison.calls == 1 and len(shared.cases.items) == 1


@pytest.mark.parametrize("outcome", ["override_recommendation", "no_award"])
def test_other_human_outcomes_and_invalid_selection(configured, outcome):
    created = client.post(BASE, json=_payload(), headers=_headers()).json()
    case_id = created["decision_case_id"]
    ranked = created["evaluation"]["decision_result"]["ranked_offers"]
    other = next(
        item["offer"]["offer_id"]
        for item in ranked
        if item["offer"]["offer_id"] != created["recommended_offer_id"]
    )
    decision = {
        "outcome": outcome,
        "selected_offer_id": other if outcome == "override_recommendation" else None,
        "rationale": "Buyer review recorded.",
        "decided_at": "2026-09-22T08:30:00Z",
        "actor_reference": "unverified-buyer-label",
    }
    invalid = {**decision, "selected_offer_id": "odoo:purchase.order:10C"}
    assert (
        client.post(
            f"{BASE}/{case_id}/final-decision", json=invalid, headers=_headers()
        ).status_code
        == 422
    )
    result = client.post(f"{BASE}/{case_id}/final-decision", json=decision, headers=_headers())
    assert result.status_code == 200, result.text
    assert result.json()["human_decision"]["outcome"] == outcome


@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        (ProcurementDataUnavailable("secret-upstream-detail"), 503),
        (ProcurementDataResponseError("secret-upstream-detail"), 502),
    ],
)
def test_upstream_errors_are_safe(configured, monkeypatch, failure, expected):
    import backend.app.routes.decision_cases as routes

    class BrokenReader:
        async def read_comparison_case(self, group_id):
            raise failure

    monkeypatch.setattr(routes, "get_comparison_case_reader", BrokenReader)
    response = client.post(BASE, json=_payload(), headers=_headers())
    assert response.status_code == expected
    assert "secret-upstream-detail" not in response.text
    assert "test-only-shared-secret" not in response.text


def test_persistence_error_and_non_utc_finalization_are_safe(configured, monkeypatch):
    import backend.app.routes.decision_cases as routes
    from application.decision_cases import RepositoryError

    created = client.post(BASE, json=_payload(), headers=_headers()).json()
    case_id = created["decision_case_id"]
    invalid = {
        "outcome": "no_award",
        "selected_offer_id": None,
        "rationale": "Documented reason",
        "decided_at": "2026-09-22T09:30:00+01:00",
        "actor_reference": "caller-label",
    }
    assert (
        client.post(
            f"{BASE}/{case_id}/final-decision", json=invalid, headers=_headers()
        ).status_code
        == 422
    )

    def unavailable():
        raise RepositoryError("repository_failure", "secret database detail")

    monkeypatch.setattr(routes, "get_decision_unit_of_work", unavailable)
    response = client.get(f"{BASE}/{case_id}", headers=_headers())
    assert response.status_code == 503
    assert "secret database detail" not in response.text
    assert "test-only-shared-secret" not in response.text
