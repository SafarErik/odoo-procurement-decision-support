"""Catalog intent/path/replay compatibility and deliberate fresh Practice drafts."""

import json
from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from application.planning_cases import fingerprint
from application.planning_catalog import PRACTICE_EXAMPLES
from backend.app.main import app
from frontend.config import FrontendSettings
from frontend.planning.practice import EXERCISES, practice_page
from frontend.planning.state import PlanningState
from tests.test_t15_odoo_planning import assets as _odoo_assets
from tests.test_t15_odoo_planning import configured as _odoo_configured
from tests.test_t15_planning_api import assets as _assets
from tests.test_t15_planning_api import configured as _configured
from tests.test_t15_planning_api import forbidden, headers

assets = _assets
configured = _configured
odoo_assets = _odoo_assets
BASE = "/api/v2/procurement/planning-cases"
client = TestClient(app)


@pytest.mark.parametrize("example", [None, *PRACTICE_EXAMPLES])
def test_classified_create_replay_conflict_and_child_inheritance(configured, monkeypatch, example):
    uow, payload = configured
    key = str(uuid4())
    classified = payload | {"catalog_context": {"workspace": "practice", "example_id": example}}
    response = client.post(BASE, json=classified, headers=headers(key))
    assert response.status_code == 201, response.text
    base = response.json()
    assert base["workspace"] == "practice" and base["example_id"] == example
    assert len(uow.catalog) == 1 and "catalog_context" not in base["snapshot"]["facts"]
    unclassified = client.post(BASE, json=payload, headers=headers()).json()
    assert unclassified["workspace"] == "unclassified"
    assert base["snapshot_hash"] == unclassified["snapshot_hash"]
    child = client.post(
        f"{BASE}/{base['case_id']}/scenarios",
        headers=headers(),
        json={
            "kind": "supplier_outage",
            "source": payload["requirement_source"],
            "suppliers": [
                {"supplier_id": payload["suppliers"][0]["supplier_id"], "available": False}
            ],
        },
    ).json()
    assert child["workspace"] == "practice" and child["example_id"] == example
    assert len(uow.catalog) == 1
    monkeypatch.setattr(uow, "add_catalog", forbidden)
    monkeypatch.setattr("backend.app.routes.planning_cases.infer_planning_features", forbidden)
    monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
    replay = client.post(BASE, json=classified, headers=headers(key))
    assert replay.status_code == 200 and replay.json()["idempotent_replay"]
    assert replay.json()["workspace"] == "practice"
    assert (
        client.get(f"{BASE}/{child['case_id']}", headers=headers()).json()["workspace"]
        == "practice"
    )
    changed = deepcopy(classified)
    changed["catalog_context"]["example_id"] = (
        "compare-plans" if example != "compare-plans" else None
    )
    assert client.post(BASE, json=changed, headers=headers(key)).status_code == 409
    assert client.post(BASE, json=payload, headers=headers(key)).status_code == 409
    assert len(uow.catalog) == 1


@pytest.mark.parametrize(
    "context",
    [
        {"workspace": "controlled"},
        {"workspace": "practice", "example_id": "unknown"},
        {"workspace": "practice", "example_id": ""},
        {"workspace": "practice", "extra": True},
        {"workspace": "unclassified"},
    ],
)
def test_rejected_context_never_acquires_sources(configured, monkeypatch, context):
    uow, payload = configured
    monkeypatch.setattr("backend.app.routes.planning_cases.infer_planning_features", forbidden)
    assert (
        client.post(
            BASE, json=payload | {"catalog_context": context}, headers=headers()
        ).status_code
        == 422
    )
    assert not uow.rows and not uow.catalog


def test_omitted_and_null_context_keep_old_fingerprint_and_never_reclassify(
    configured, monkeypatch
):
    from application.planning_cases import normalize_planning_facts
    from backend.app.planning_case_schemas import PlanningCreateRequest

    uow, payload = configured
    key = str(uuid4())
    base = client.post(BASE, json=payload, headers=headers(key)).json()
    expected = fingerprint(
        {
            "operation": "base",
            "facts": normalize_planning_facts(PlanningCreateRequest(**payload).to_facts()),
        }
    )
    assert uow.rows[base["case_id"]].fingerprint == expected and not uow.catalog
    monkeypatch.setattr(uow, "add_catalog", forbidden)
    replay = client.post(BASE, json=payload | {"catalog_context": None}, headers=headers(key))
    assert replay.status_code == 200 and replay.json()["workspace"] == "unclassified"
    assert replay.json()["snapshot_hash"] == base["snapshot_hash"] and not uow.catalog
    assert (
        client.post(
            BASE,
            json=payload | {"catalog_context": {"workspace": "practice"}},
            headers=headers(key),
        ).status_code
        == 409
    )


def test_odoo_context_is_outer_controlled_only(odoo_assets, monkeypatch):

    # Reuse the existing prepared-reader fixture, without live Odoo mutation.
    configured = _odoo_configured.__wrapped__(odoo_assets, monkeypatch)
    uow, payload, *_ = configured
    token = {"Authorization": "Bearer controlled-test-token", "Idempotency-Key": str(uuid4())}
    for context in (
        {"workspace": "practice"},
        {"workspace": "controlled", "example_id": "compare-plans"},
    ):
        assert (
            client.post(
                BASE + "/from-odoo", json=payload | {"catalog_context": context}, headers=token
            ).status_code
            == 422
        )
    nested = deepcopy(payload)
    nested["controlled_input"]["catalog_context"] = {"workspace": "practice"}
    assert client.post(BASE + "/from-odoo", json=nested, headers=token).status_code == 422
    response = client.post(
        BASE + "/from-odoo",
        json=payload | {"catalog_context": {"workspace": "controlled"}},
        headers=token,
    )
    assert response.status_code == 201, response.text
    assert response.json()["workspace"] == "controlled" and len(uow.catalog) == 1
    assert response.json()["snapshot"]["facts"]["input_kind"] == "odoo_quotations_synthetic_history"


def test_practice_selection_is_read_only_fresh_and_pending_guarded(assets, monkeypatch):
    directory, payload = assets
    (directory / "create-request.json").write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(
        FrontendSettings,
        "controlled_demo_file",
        property(lambda _: directory / "create-request.json"),
    )
    assert tuple(e[0] for e in EXERCISES) == PRACTICE_EXAMPLES
    state = PlanningState(_reflex_internal_init=True)
    state.has_case = True
    state.details = {"case_id": "old-finalized", "final_outcome": "Approved"}
    PlanningState.choose_practice_task.fn(state, "supplier-outage")
    assert state.demo_ready and not state.has_case and not state.details
    assert not state._pending and state.practice_task == "supplier-outage"
    state.has_pending = True
    state._pending = {"key": "same", "payload": {"catalog_context": {"workspace": "practice"}}}
    pending = deepcopy(state._pending)
    PlanningState.choose_practice_task.fn(state, "compare-plans")
    assert state.practice_task == "supplier-outage" and state._pending == pending
    assert state.open_practice() is None
    assert practice_page()
