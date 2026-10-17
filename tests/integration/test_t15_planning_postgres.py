"""Actual PostgreSQL and HTTP verification of immutable Odoo-history planning snapshots.

Odoo is a fake read-only JSON-2 transport; the model is trained offline in the test;
the database is the disposable integration database.
"""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from application.errors import RepositoryError
from backend.app.main import app
from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork
from tests.legacy_cases import create_legacy_case
from tests.t15_helpers import controlled_assets
from tests.test_odoo_purchase_history import headers, install_fake_odoo
from tests.test_odoo_purchase_history import history as history

pytestmark = pytest.mark.integration
BASE = "/api/v2/procurement/planning-cases"


@pytest.fixture
def configured(postgres_runtime, history, monkeypatch):
    engine, factory = postgres_runtime
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE planning_documents, planning_final_decisions, planning_cases")
        )
    calls = install_fake_odoo(history, monkeypatch)
    monkeypatch.setattr(
        "backend.app.routes.planning_cases.get_planning_unit_of_work",
        lambda: SqlAlchemyPlanningUnitOfWork(factory),
    )
    with TestClient(app) as client:
        preview = client.get(
            f"{BASE}/odoo-history/preview?purchase_group_id=501", headers=headers()
        )
        assert preview.status_code == 200, preview.text
    payload = {"purchase_group_id": 501, "terms": preview.json()["terms"]}
    return engine, factory, payload, calls


def forbidden(*args, **kwargs):
    raise AssertionError("Stored retrieval/replay touched Odoo, model or solver")


def create(client, payload, key=None):
    response = client.post(f"{BASE}/from-odoo-history", json=payload, headers=headers(key))
    assert response.status_code == 201, response.text
    return response.json()


def test_http_database_roundtrip_bidirectional_scenarios_and_stored_replay(configured, monkeypatch):
    engine, _, payload, calls = configured
    key = str(uuid4())
    with TestClient(app) as client:
        base = create(client, payload, key)
        case_id = base["case_id"]
        supplier = payload["terms"]["suppliers"][0]
        source = payload["terms"]["requirement_source"]
        scenarios = [
            {
                "kind": "capacity_change",
                "source": source,
                "suppliers": [
                    {"supplier_id": supplier["supplier_id"], "capacity": supplier["capacity"] * 2}
                ],
            },
            {
                "kind": "demand_change",
                "source": source,
                "approved_quantity": payload["terms"]["requirement"]["approved_quantity"] // 2,
            },
        ]
        children, child_key = [], str(uuid4())
        for index, scenario in enumerate(scenarios):
            response = client.post(
                f"{BASE}/{case_id}/scenarios",
                json=scenario,
                headers=headers(child_key if index == 0 else None),
            )
            assert response.status_code == 201, response.text
            children.append(response.json())
        assert all(c["parent_id"] == case_id for c in children)
        assert children[0]["snapshot"]["assessments"] == base["snapshot"]["assessments"]
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM planning_cases")).scalar_one() == 3
            assert (
                connection.execute(
                    text(
                        "SELECT snapshot->'facts'->>'input_kind' "
                        "FROM planning_cases WHERE case_id=:id"
                    ),
                    {"id": case_id},
                ).scalar_one()
                == "odoo_quotations_odoo_history"
            )
        before = len(calls)
        for name in (
            "resolve_odoo_history_input",
            "infer_odoo_history_features",
            "planning_solver_factory",
        ):
            monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
        monkeypatch.setattr("application.planning_cases.assemble_planning_input", forbidden)
        monkeypatch.setattr("application.planning_cases.create_procurement_plans", forbidden)
        assert (
            client.get(f"{BASE}/{case_id}", headers=headers()).json()["snapshot"]
            == base["snapshot"]
        )
        overview = client.get(f"{BASE}/{case_id}/suppliers", headers=headers())
        assert overview.status_code == 200 and len(overview.json()["suppliers"]) == 3
        replay = client.post(f"{BASE}/from-odoo-history", json=payload, headers=headers(key))
        assert replay.status_code == 200 and replay.json()["snapshot_hash"] == base["snapshot_hash"]
        assert (
            client.post(
                f"{BASE}/{case_id}/scenarios", json=scenarios[0], headers=headers(child_key)
            ).status_code
            == 200
        )
        conflict = client.post(
            f"{BASE}/{case_id}/scenarios", json=scenarios[1], headers=headers(child_key)
        )
        assert conflict.status_code == 409
        assert len(calls) == before


def test_pre_p2_synthetic_base_stays_readable(configured, tmp_path):
    engine, factory, *_ = configured
    payload = controlled_assets(tmp_path / "model")
    base = create_legacy_case(SqlAlchemyPlanningUnitOfWork(factory), payload, tmp_path / "model")
    with TestClient(app) as client:
        stored = client.get(f"{BASE}/{base['case_id']}", headers=headers())
    assert stored.status_code == 200 and stored.json()["origin"] == "demo"
    assert stored.json()["snapshot"]["result"]["minimum_cost_plan"]["total_cost"] == "102"


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE planning_cases SET snapshot = '{}'::jsonb WHERE case_id=:id",
        "UPDATE planning_cases SET fingerprint = repeat('0',64) WHERE case_id=:id",
        "UPDATE planning_cases SET idempotency_key = :key WHERE case_id=:id",
        "DELETE FROM planning_cases WHERE case_id=:id",
    ],
)
def test_database_rejects_snapshot_mapping_and_delete_mutation(configured, statement):
    engine, _, payload, _ = configured
    with TestClient(app) as client:
        base = create(client, payload)
        with pytest.raises(DBAPIError, match="immutable"):
            with engine.begin() as connection:
                connection.execute(text(statement), {"id": base["case_id"], "key": str(uuid4())})
        assert (
            client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["snapshot_hash"]
            == base["snapshot_hash"]
        )


def test_same_key_concurrent_creation_computes_once(configured, monkeypatch):
    engine, _, payload, _ = configured
    from backend.app.routes import planning_cases as routes

    actual_infer, calls = routes.infer_odoo_history_features, []

    def infer(features):
        calls.append(1)
        return actual_infer(features)

    monkeypatch.setattr(routes, "infer_odoo_history_features", infer)
    key = str(uuid4())

    def post():
        with TestClient(app) as client:
            return client.post(f"{BASE}/from-odoo-history", json=payload, headers=headers(key))

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: post(), range(2)))
    assert sorted(response.status_code for response in responses) == [200, 201], [
        r.text for r in responses
    ]
    assert responses[0].json()["case_id"] == responses[1].json()["case_id"]
    assert calls == [1]
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM planning_cases")).scalar_one() == 1


def test_failed_commit_rolls_back_case_and_key_then_allows_fresh_attempt(configured, monkeypatch):
    engine, _, payload, _ = configured
    key = str(uuid4())
    with monkeypatch.context() as patch:

        def fail_commit(self):
            raise RepositoryError("repository_failure", "Injected commit failure")

        patch.setattr(SqlAlchemyPlanningUnitOfWork, "commit", fail_commit)
        with TestClient(app) as client:
            response = client.post(f"{BASE}/from-odoo-history", json=payload, headers=headers(key))
            assert response.status_code == 503
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM planning_cases")).scalar_one() == 0
    with TestClient(app) as client:
        create(client, payload, key)
