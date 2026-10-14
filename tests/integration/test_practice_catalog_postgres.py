"""Real atomic case+catalog storage, replay after ambiguity, and inherited metadata."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from application.decision_cases import RepositoryError
from backend.app.main import app
from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork
from tests.integration.test_t15_planning_postgres import assets as _assets
from tests.integration.test_t15_planning_postgres import configured as _configured
from tests.integration.test_t15_planning_postgres import forbidden, headers
from tests.integration.test_t15_planning_postgres import postgres_runtime as _postgres_runtime

assets = _assets
configured = _configured
postgres_runtime = _postgres_runtime
pytestmark = pytest.mark.integration
BASE = "/api/v2/procurement/planning-cases"


@pytest.mark.parametrize("failure", ["after_catalog", "before_commit", "after_commit"])
def test_atomic_storage_and_exact_replay_after_failure(configured, monkeypatch, failure):
    engine, factory, payload = configured
    payload = payload | {
        "catalog_context": {"workspace": "practice", "example_id": "supplier-outage"}
    }
    key = str(uuid4())

    class FailedUnitOfWork(SqlAlchemyPlanningUnitOfWork):
        def __enter__(self):
            super().__enter__()
            if failure == "after_catalog":
                add = self.cases.add_catalog

                def insert_then_fail(case_id, context):
                    add(case_id, context)
                    raise RepositoryError(
                        "repository_failure", "Injected failure after catalog insert"
                    )

                self.cases.add_catalog = insert_then_fail
            return self

        def commit(self):
            if failure == "after_commit":
                super().commit()
            raise RepositoryError("repository_failure", "Injected commit ambiguity")

    monkeypatch.setattr(
        "backend.app.routes.planning_cases.get_planning_unit_of_work",
        lambda: FailedUnitOfWork(factory),
    )
    with TestClient(app) as client:
        assert client.post(BASE, json=payload, headers=headers(key)).status_code == 503
        with engine.connect() as connection:
            for table in ("planning_cases", "planning_case_catalog"):
                assert connection.execute(text("SELECT count(*) FROM " + table)).scalar_one() == (
                    1 if failure == "after_commit" else 0
                )
        monkeypatch.setattr(
            "backend.app.routes.planning_cases.get_planning_unit_of_work",
            lambda: SqlAlchemyPlanningUnitOfWork(factory),
        )
        if failure == "after_commit":
            monkeypatch.setattr(
                "backend.app.routes.planning_cases.infer_planning_features", forbidden
            )
            monkeypatch.setattr(
                "backend.app.routes.planning_cases.planning_solver_factory", forbidden
            )
        replay = client.post(BASE, json=payload, headers=headers(key))
        assert replay.status_code == (200 if failure == "after_commit" else 201), replay.text
        assert (
            replay.json()["workspace"] == "practice"
            and replay.json()["example_id"] == "supplier-outage"
        )
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT count(*) FROM planning_case_catalog")).scalar_one()
                == 1
            )


def test_concurrent_classification_and_original_child_readback(configured, monkeypatch):
    engine, _, payload = configured
    classified = payload | {
        "catalog_context": {"workspace": "practice", "example_id": "compare-plans"}
    }
    key = str(uuid4())

    def create(_):
        with TestClient(app) as client:
            return client.post(BASE, json=classified, headers=headers(key))

    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(create, range(4)))
    assert sorted(r.status_code for r in responses) == [200, 200, 200, 201]
    base = responses[0].json()
    with TestClient(app) as client:
        legacy = client.post(BASE, json=payload, headers=headers()).json()
        assert (
            legacy["workspace"] == "unclassified"
            and legacy["snapshot_hash"] == base["snapshot_hash"]
        )
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
        assert child["workspace"] == "practice" and child["example_id"] == "compare-plans"
        monkeypatch.setattr("backend.app.routes.planning_cases.infer_planning_features", forbidden)
        monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
        assert (
            client.get(f"{BASE}/{child['case_id']}", headers=headers()).json()["workspace"]
            == "practice"
        )
        assert client.post(BASE, json=payload, headers=headers(key)).status_code == 409
        changed = payload | {
            "catalog_context": {"workspace": "practice", "example_id": "supplier-outage"}
        }
        assert client.post(BASE, json=changed, headers=headers(key)).status_code == 409
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM planning_case_catalog")).scalar_one() == 1
        )
