"""Disposable PostgreSQL human-decision races, immutability and atomic rollback."""

import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from application.errors import RepositoryError
from backend.app.config import settings
from backend.app.main import app
from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork
from tests.test_t17_decisions import BASE, TOKEN, headers, intent
from tests.test_t17_decisions import stored_cases as _stored_cases

pytestmark = pytest.mark.integration
stored_cases = _stored_cases


@pytest.fixture
def configured(postgres_runtime, stored_cases, monkeypatch):
    engine, factory = postgres_runtime
    memory, base, child, _ = stored_cases
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE planning_documents, planning_final_decisions, planning_cases")
        )
    with SqlAlchemyPlanningUnitOfWork(factory) as uow:
        for row in memory.rows.values():
            uow.cases.add(row)
        uow.commit()
    monkeypatch.setattr(settings, "api_service_token", SecretStr(TOKEN))
    monkeypatch.setattr(
        "backend.app.routes.planning_cases.get_planning_unit_of_work",
        lambda: SqlAlchemyPlanningUnitOfWork(factory),
    )
    with TestClient(app) as client:
        yield engine, factory, client, base, child


@pytest.mark.parametrize("same_intent", [True, False])
def test_genuinely_contending_finalization_transactions(configured, same_intent):
    engine, _, client, base, _ = configured
    key = str(uuid4())
    commands = [intent(base), intent(base) if same_intent else intent(base, 1)]
    keys = [key, key if same_intent else str(uuid4())]
    url = f"{BASE}/{base['case_id']}/final-decision"
    with engine.connect() as holder, ThreadPoolExecutor(max_workers=2) as pool:
        holder.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
            {"key": "t17:case:" + base["case_id"]},
        )
        futures = [
            pool.submit(client.post, url, json=c, headers=headers(k))
            for c, k in zip(commands, keys, strict=True)
        ]
        try:
            deadline = time.monotonic() + 10
            waiting = 0
            while time.monotonic() < deadline:
                holder.execute(text("SELECT pg_stat_clear_snapshot()"))
                waiting = holder.execute(
                    text(
                        "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() "
                        "AND wait_event = 'advisory' AND pid <> pg_backend_pid()"
                    )
                ).scalar_one()
                if waiting >= 2:
                    break
                time.sleep(0.05)
            assert waiting >= 2, "Both requests must actually wait on PostgreSQL transaction locks"
        finally:
            holder.commit()
        responses = [f.result(timeout=15) for f in futures]
    assert sorted(r.status_code for r in responses) == ([200, 201] if same_intent else [201, 409])
    winner = next(r.json() for r in responses if r.status_code == 201)
    if same_intent:
        assert responses[0].json()["final_decision"] == responses[1].json()["final_decision"]
    loaded = client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()
    assert loaded["final_decision"] == winner["final_decision"]
    assert (
        loaded["snapshot_hash"] == base["snapshot_hash"] and loaded["snapshot"] == base["snapshot"]
    )
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM planning_final_decisions")).scalar_one()
            == 1
        )


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE planning_final_decisions SET record='{}'::jsonb WHERE case_id=:id",
        "UPDATE planning_final_decisions SET idempotency_key=:key WHERE case_id=:id",
        "DELETE FROM planning_final_decisions WHERE case_id=:id",
        "UPDATE planning_cases SET snapshot='{}'::jsonb WHERE case_id=:id",
        "DELETE FROM planning_cases WHERE case_id=:id",
    ],
)
def test_database_rejects_final_decision_and_snapshot_mutation(configured, statement):
    engine, _, client, base, _ = configured
    response = client.post(
        f"{BASE}/{base['case_id']}/final-decision", json=intent(base), headers=headers()
    )
    assert response.status_code == 201, response.text
    with pytest.raises(DBAPIError, match="immutable"):
        with engine.begin() as connection:
            connection.execute(text(statement), {"id": base["case_id"], "key": str(uuid4())})
    assert (
        client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["final_decision"]
        == response.json()["final_decision"]
    )


def test_database_rollback_after_insert_and_before_commit(configured, monkeypatch):
    engine, factory, client, base, _ = configured

    class FailedCommit(SqlAlchemyPlanningUnitOfWork):
        def commit(self):
            raise RepositoryError("repository_failure", "Injected transaction failure")

    monkeypatch.setattr(
        "backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: FailedCommit(factory)
    )
    key = str(uuid4())
    url = f"{BASE}/{base['case_id']}/final-decision"
    assert client.post(url, json=intent(base), headers=headers(key)).status_code == 503
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM planning_final_decisions")).scalar_one()
            == 0
        )
    monkeypatch.setattr(
        "backend.app.routes.planning_cases.get_planning_unit_of_work",
        lambda: SqlAlchemyPlanningUnitOfWork(factory),
    )
    assert client.post(url, json=intent(base), headers=headers(key)).status_code == 201


def test_database_base_only_and_global_key_uniqueness(configured):
    engine, _, client, base, child = configured
    key = str(uuid4())
    assert (
        client.post(
            f"{BASE}/{base['case_id']}/final-decision", json=intent(base), headers=headers(key)
        ).status_code
        == 201
    )
    with pytest.raises(DBAPIError, match="original planning base"):
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO planning_final_decisions "
                    "SELECT :child, :key, fingerprint, record_hash, record "
                    "FROM planning_final_decisions WHERE case_id=:base"
                ),
                {"child": child["case_id"], "key": str(uuid4()), "base": base["case_id"]},
            )
    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO planning_final_decisions "
                    "SELECT case_id, idempotency_key, fingerprint, record_hash, record "
                    "FROM planning_final_decisions WHERE case_id=:base"
                ),
                {"base": base["case_id"]},
            )
