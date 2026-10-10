"""Actual PostgreSQL and HTTP verification of controlled immutable T15 snapshots."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from application.decision_cases import RepositoryError
from backend.app.config import settings
from backend.app.main import app
from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork
from tests.integration.test_decision_case_postgres import postgres_runtime as _postgres_runtime
from tests.t15_helpers import controlled_assets

pytestmark = pytest.mark.integration
BASE = "/api/v2/procurement/planning-cases"
postgres_runtime = _postgres_runtime


@pytest.fixture(scope="module")
def assets(tmp_path_factory):
    directory = tmp_path_factory.mktemp("t15-pg-model")
    return directory, controlled_assets(directory)


@pytest.fixture
def configured(postgres_runtime, assets, monkeypatch):
    engine, factory = postgres_runtime
    directory, payload = assets
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE planning_final_decisions, planning_cases"))
    monkeypatch.setattr(settings, "t15_trusted_model_directory", directory)
    monkeypatch.setattr(settings, "t12_trusted_caller_token", SecretStr("t15-pg-test-secret"))
    monkeypatch.setattr(
        "backend.app.routes.planning_cases.get_planning_unit_of_work",
        lambda: SqlAlchemyPlanningUnitOfWork(factory),
    )
    return engine, factory, payload


def headers(key=None):
    return {"Authorization": "Bearer t15-pg-test-secret", "Idempotency-Key": key or str(uuid4())}


def forbidden(*args, **kwargs):
    raise AssertionError("Stored retrieval/replay touched model or solver")


def test_http_database_roundtrip_scenarios_and_stored_replay(configured, monkeypatch):
    engine, _, payload = configured
    key = str(uuid4())
    with TestClient(app) as client:
        response = client.post(BASE, json=payload, headers=headers(key))
        assert response.status_code == 201, response.text
        base = response.json()
        case_id = base["case_id"]
        supplier = payload["suppliers"][0]["supplier_id"]
        scenario = {
            "kind": "capacity_reduction",
            "source": payload["requirement_source"],
            "suppliers": [{"supplier_id": supplier, "capacity": 2}],
        }
        child_key = str(uuid4())
        response = client.post(
            f"{BASE}/{case_id}/scenarios", json=scenario, headers=headers(child_key)
        )
        assert response.status_code == 201, response.text
        child = response.json()
        assert child["parent_id"] == case_id
        assert child["snapshot"]["assessments"] == base["snapshot"]["assessments"]
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM planning_cases")).scalar_one() == 2
            assert (
                connection.execute(
                    text(
                        "SELECT snapshot->'result'->'minimum_cost_plan'->>'total_cost' "
                        "FROM planning_cases WHERE case_id=:id"
                    ),
                    {"id": case_id},
                ).scalar_one()
                == "102"
            )
        monkeypatch.setattr(settings, "t15_trusted_model_directory", None)
        monkeypatch.setattr("backend.app.routes.planning_cases.infer_planning_features", forbidden)
        monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
        monkeypatch.setattr("application.planning_cases.assemble_planning_input", forbidden)
        monkeypatch.setattr("application.planning_cases.create_procurement_plans", forbidden)
        assert (
            client.get(f"{BASE}/{case_id}", headers=headers()).json()["snapshot"]
            == base["snapshot"]
        )
        assert (
            client.get(f"{BASE}/{child['case_id']}", headers=headers()).json()["snapshot_hash"]
            == child["snapshot_hash"]
        )
        assert client.post(BASE, json=payload, headers=headers(key)).status_code == 200
        assert (
            client.post(
                f"{BASE}/{case_id}/scenarios", json=scenario, headers=headers(child_key)
            ).status_code
            == 200
        )
        assert client.post(BASE, json=payload, headers=headers(child_key)).status_code == 409


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
    engine, _, payload = configured
    with TestClient(app) as client:
        response = client.post(BASE, json=payload, headers=headers())
        assert response.status_code == 201, response.text
        base = response.json()
        with pytest.raises(DBAPIError, match="immutable"):
            with engine.begin() as connection:
                connection.execute(text(statement), {"id": base["case_id"], "key": str(uuid4())})
        assert (
            client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["snapshot_hash"]
            == base["snapshot_hash"]
        )


def test_same_key_concurrent_creation_computes_once(configured, monkeypatch):
    engine, _, payload = configured
    from backend.app.routes import planning_cases as routes

    actual_infer, calls = routes.infer_planning_features, []

    def infer(features):
        calls.append(1)
        return actual_infer(features)

    monkeypatch.setattr(routes, "infer_planning_features", infer)
    key = str(uuid4())

    def create():
        with TestClient(app) as client:
            return client.post(BASE, json=payload, headers=headers(key))

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: create(), range(2)))
    assert sorted(response.status_code for response in responses) == [200, 201], [
        r.text for r in responses
    ]
    assert responses[0].json()["case_id"] == responses[1].json()["case_id"]
    assert calls == [1]
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM planning_cases")).scalar_one() == 1


def test_failed_commit_rolls_back_case_and_key_then_allows_fresh_attempt(configured, monkeypatch):
    engine, _, payload = configured
    key = str(uuid4())
    with monkeypatch.context() as patch:

        def fail_commit(self):
            raise RepositoryError("repository_failure", "Injected commit failure")

        patch.setattr(SqlAlchemyPlanningUnitOfWork, "commit", fail_commit)
        with TestClient(app) as client:
            assert client.post(BASE, json=payload, headers=headers(key)).status_code == 503
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM planning_cases")).scalar_one() == 0
    with TestClient(app) as client:
        assert client.post(BASE, json=payload, headers=headers(key)).status_code == 201


def test_hybrid_quotation_case_roundtrip_and_upstream_free_replay(
    configured, monkeypatch, tmp_path
):
    import asyncio

    from tests.test_odoo_comparison_case_adapter import _payloads
    from tests.test_t15_odoo_planning import quotation_reader
    from tools.t15_odoo_demo import prepare_odoo_assets

    engine, _, _ = configured
    reader = quotation_reader(_payloads(), [])
    case = asyncio.run(reader.read_comparison_case(501))
    code, observed = asyncio.run(reader.read_currency_code(case.offers[0].currency_id))
    payload, scenario = prepare_odoo_assets(tmp_path, case, code, observed)
    monkeypatch.setattr(settings, "t15_trusted_model_directory", tmp_path / "model")
    monkeypatch.setattr("backend.app.dependencies.get_comparison_case_reader", lambda: reader)
    key = str(uuid4())
    with TestClient(app) as client:
        response = client.post(f"{BASE}/from-odoo", json=payload, headers=headers(key))
        assert response.status_code == 201, response.text
        base = response.json()
        response = client.post(
            f"{BASE}/{base['case_id']}/scenarios", json=scenario, headers=headers()
        )
        assert response.status_code == 201, response.text
        child = response.json()
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM planning_cases")).scalar_one() == 2
            assert (
                connection.execute(
                    text(
                        "SELECT snapshot->'facts'->>'input_kind' "
                        "FROM planning_cases WHERE case_id=:id"
                    ),
                    {"id": base["case_id"]},
                ).scalar_one()
                == "odoo_quotations_synthetic_history"
            )
        monkeypatch.setattr(
            "backend.app.routes.planning_cases.resolve_odoo_planning_input", forbidden
        )
        monkeypatch.setattr("backend.app.routes.planning_cases.infer_planning_features", forbidden)
        monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
        assert (
            client.post(f"{BASE}/from-odoo", json=payload, headers=headers(key)).json()[
                "snapshot_hash"
            ]
            == base["snapshot_hash"]
        )
        for stored in (base, child):
            assert (
                client.get(f"{BASE}/{stored['case_id']}", headers=headers()).json()["snapshot"]
                == stored["snapshot"]
            )
