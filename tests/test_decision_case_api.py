"""Trusted HTTP boundary and stored-case lifecycle contracts for T12."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from application.rfqs import ProcurementDataResponseError, ProcurementDataUnavailable
from backend.app.config import settings
from backend.app.main import app
from tests.test_decision_case_orchestration import (
    FakeComparisonReader,
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


def test_create_replay_get_finalize_and_stored_snapshots(configured):
    _, comparison, history = configured
    key = str(uuid4())
    headers = _headers(key)
    first = client.post(BASE, json=_payload(), headers=headers)
    assert first.status_code == 201, first.text
    created = first.json()
    assert created["idempotent_replay"] is False
    assert created["recommended_offer_id"] is not None
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
