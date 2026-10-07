"""PostgreSQL migration, transaction, immutability, and session tests for T11."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from application.decision_case_orchestration import OrchestrationError, create_decision_case
from application.decision_cases import (
    DecisionCaseError,
    DecisionCaseState,
    HumanDecisionCommand,
    HumanDecisionOutcome,
    get_decision_case,
    record_human_decision,
    store_evaluated_decision_case,
)
from persistence import SqlAlchemyUnitOfWork, create_session_factory
from tests.t11_helpers import NOW, variant
from tests.test_decision_case_orchestration import (
    FakeComparisonReader,
    FakeHistoryReader,
)
from tests.test_decision_case_orchestration import (
    _command as _create_command,
)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def postgres_runtime() -> Iterator[tuple[object, object]]:
    database_url = os.getenv("T11_TEST_DATABASE_URL", "")
    if not database_url:
        pytest.skip("T11_TEST_DATABASE_URL is not set for the isolated test database.")

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    alembic_command.downgrade(config, "base")
    alembic_command.upgrade(config, "head")
    engine, session_factory = create_session_factory(database_url)
    yield engine, session_factory
    engine.dispose()


@pytest.fixture(autouse=True)
def empty_decision_cases(postgres_runtime) -> Iterator[None]:
    engine, _ = postgres_runtime
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE decision_case_creations, decision_cases"))
    yield


def _store(session_factory, case_id: str, name: str = "legacy"):
    assembled, policy, evaluation = variant(name)
    return store_evaluated_decision_case(
        SqlAlchemyUnitOfWork(session_factory),
        decision_case_id=case_id,
        created_at=NOW,
        assembled_input=assembled,
        scoring_policy=policy,
        evaluation=evaluation,
    )


def _command(
    outcome: HumanDecisionOutcome,
    selected_offer_id: str | None,
    rationale: str | None,
    key: str,
) -> HumanDecisionCommand:
    return HumanDecisionCommand(
        outcome=outcome,
        selected_offer_id=selected_offer_id,
        rationale=rationale,
        decided_at=NOW,
        actor_reference="integration-buyer-reference",
        idempotency_key=key,
    )


def test_clean_database_migration_creates_versioned_immutable_schema(postgres_runtime) -> None:
    engine, _ = postgres_runtime
    inspector = inspect(engine)

    assert "decision_cases" in inspector.get_table_names()
    assert {item["name"] for item in inspector.get_unique_constraints("decision_cases")} == {
        "uq_decision_cases_idempotency_key"
    }
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "20261005_01"
        )


@pytest.mark.parametrize("name", ["legacy", "historical_active", "historical_fallback"])
def test_all_snapshot_variants_survive_separate_sessions(postgres_runtime, name: str) -> None:
    _, session_factory = postgres_runtime
    case_id = str(uuid4())
    stored = _store(session_factory, case_id, name)

    retrieved = get_decision_case(SqlAlchemyUnitOfWork(session_factory), case_id)

    assert retrieved == stored
    assert retrieved.assembled_input.provenance == stored.assembled_input.provenance
    assert retrieved.evaluation == stored.evaluation


def test_duplicate_case_primary_key_is_translated(postgres_runtime) -> None:
    _, session_factory = postgres_runtime
    case_id = str(uuid4())
    _store(session_factory, case_id)

    with pytest.raises(DecisionCaseError) as captured:
        _store(session_factory, case_id)

    assert captured.value.code == "duplicate_decision_case_id"


def test_failed_finalization_rolls_back_and_keeps_case_open(postgres_runtime) -> None:
    _, session_factory = postgres_runtime
    case_id = str(uuid4())
    _store(session_factory, case_id)

    with pytest.raises(DecisionCaseError) as captured:
        record_human_decision(
            SqlAlchemyUnitOfWork(session_factory),
            case_id,
            _command(
                HumanDecisionOutcome.OVERRIDE_RECOMMENDATION,
                "unknown-offer",
                "Invalid attempt.",
                str(uuid4()),
            ),
        )

    assert captured.value.code == "selected_offer_not_eligible"
    retrieved = get_decision_case(SqlAlchemyUnitOfWork(session_factory), case_id)
    assert retrieved.state is DecisionCaseState.EVALUATED
    assert retrieved.human_decision is None


def test_snapshot_columns_are_immutable_at_database_boundary(postgres_runtime) -> None:
    engine, session_factory = postgres_runtime
    case_id = str(uuid4())
    _store(session_factory, case_id)

    with pytest.raises(DBAPIError, match="evaluation snapshots are immutable"):
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE decision_cases SET policy_name = 'mutated' "
                    "WHERE decision_case_id = :case_id"
                ),
                {"case_id": case_id},
            )

    retrieved = get_decision_case(SqlAlchemyUnitOfWork(session_factory), case_id)
    assert retrieved.scoring_policy.name == "cost-focused"


def test_sequential_double_finalization_and_idempotency(postgres_runtime) -> None:
    _, session_factory = postgres_runtime
    case_id = str(uuid4())
    _store(session_factory, case_id)
    key = str(uuid4())
    accepted = _command(HumanDecisionOutcome.ACCEPT_RECOMMENDATION, "offer-A", None, key)
    first = record_human_decision(SqlAlchemyUnitOfWork(session_factory), case_id, accepted)

    assert record_human_decision(SqlAlchemyUnitOfWork(session_factory), case_id, accepted) == first
    with pytest.raises(DecisionCaseError) as conflicting_payload:
        record_human_decision(
            SqlAlchemyUnitOfWork(session_factory),
            case_id,
            _command(
                HumanDecisionOutcome.ACCEPT_RECOMMENDATION,
                "offer-A",
                "changed",
                key,
            ),
        )
    assert conflicting_payload.value.code == "idempotency_key_conflict"

    with pytest.raises(DecisionCaseError) as second_finalization:
        record_human_decision(
            SqlAlchemyUnitOfWork(session_factory),
            case_id,
            _command(
                HumanDecisionOutcome.NO_AWARD,
                None,
                "A later incompatible decision.",
                str(uuid4()),
            ),
        )
    assert second_finalization.value.code == "decision_case_already_finalized"


def test_idempotency_key_is_unique_across_cases(postgres_runtime) -> None:
    _, session_factory = postgres_runtime
    first_id = str(uuid4())
    second_id = str(uuid4())
    _store(session_factory, first_id)
    _store(session_factory, second_id)
    key = str(uuid4())
    accepted = _command(HumanDecisionOutcome.ACCEPT_RECOMMENDATION, "offer-A", None, key)
    record_human_decision(SqlAlchemyUnitOfWork(session_factory), first_id, accepted)

    with pytest.raises(DecisionCaseError) as captured:
        record_human_decision(SqlAlchemyUnitOfWork(session_factory), second_id, accepted)

    assert captured.value.code == "idempotency_key_conflict"
    assert (
        get_decision_case(SqlAlchemyUnitOfWork(session_factory), second_id).state
        is DecisionCaseState.EVALUATED
    )


def _t12_create(session_factory, command, comparison=None):
    return asyncio.run(
        create_decision_case(
            command,
            comparison_reader=comparison or FakeComparisonReader(),
            history_reader=FakeHistoryReader(),
            unit_of_work=SqlAlchemyUnitOfWork(session_factory),
            clock=lambda: NOW,
        )
    )


def test_t12_creation_mapping_survives_sessions_and_finalization(postgres_runtime) -> None:
    engine, session_factory = postgres_runtime
    inspector = inspect(engine)
    assert "decision_case_creations" in inspector.get_table_names()
    assert {column["name"] for column in inspector.get_columns("decision_case_creations")} == {
        "idempotency_key",
        "request_fingerprint",
        "decision_case_id",
    }
    command = _create_command()
    reader = FakeComparisonReader()
    created = _t12_create(session_factory, command, reader)
    replayed = _t12_create(session_factory, command, reader)
    assert replayed.replayed and replayed.decision_case == created.decision_case
    assert reader.calls == 1
    stored = get_decision_case(
        SqlAlchemyUnitOfWork(session_factory), created.decision_case.decision_case_id
    )
    assert stored == created.decision_case
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM decision_case_creations")).scalar_one()
            == 1
        )
        assert connection.execute(text("SELECT count(*) FROM decision_cases")).scalar_one() == 1

    human = _command(
        HumanDecisionOutcome.ACCEPT_RECOMMENDATION,
        stored.recommended_offer_id,
        None,
        str(uuid4()),
    )
    finalized = record_human_decision(
        SqlAlchemyUnitOfWork(session_factory), stored.decision_case_id, human
    )
    assert finalized.assembled_input == stored.assembled_input
    assert finalized.evaluation == stored.evaluation
    assert finalized.scoring_policy == stored.scoring_policy


def test_t12_concurrent_identical_requests_store_one_case(postgres_runtime) -> None:
    engine, session_factory = postgres_runtime
    command = _create_command()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_t12_create, session_factory, command) for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]
    assert results[0].decision_case.decision_case_id == results[1].decision_case.decision_case_id
    assert sorted(item.replayed for item in results) == [False, True]
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM decision_case_creations")).scalar_one()
            == 1
        )
        assert connection.execute(text("SELECT count(*) FROM decision_cases")).scalar_one() == 1


def test_t12_concurrent_conflicting_requests_store_one_case(postgres_runtime) -> None:
    engine, session_factory = postgres_runtime
    command = _create_command()
    from dataclasses import replace

    changed = replace(command, scoring_policy_id="urgent")
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_t12_create, session_factory, item) for item in (command, changed)]
        outcomes = []
        for future in futures:
            try:
                outcomes.append(future.result(timeout=20))
            except OrchestrationError as error:
                outcomes.append(error)
    assert sum(isinstance(item, OrchestrationError) for item in outcomes) == 1
    assert (
        next(item for item in outcomes if isinstance(item, OrchestrationError)).code
        == "creation_idempotency_conflict"
    )
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM decision_case_creations")).scalar_one()
            == 1
        )
        assert connection.execute(text("SELECT count(*) FROM decision_cases")).scalar_one() == 1


def test_t12_failed_case_insert_leaves_no_create_key(postgres_runtime) -> None:
    engine, session_factory = postgres_runtime
    command = _create_command()
    first = _t12_create(session_factory, command)
    second_command = _create_command()
    with pytest.raises(OrchestrationError) as captured:
        asyncio.run(
            create_decision_case(
                second_command,
                comparison_reader=FakeComparisonReader(),
                history_reader=FakeHistoryReader(),
                unit_of_work=SqlAlchemyUnitOfWork(session_factory),
                clock=lambda: NOW,
                new_id=lambda: first.decision_case.decision_case_id,
            )
        )
    assert captured.value.code == "decision_case_persistence_failed"
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM decision_case_creations")).scalar_one()
            == 1
        )
        assert connection.execute(text("SELECT count(*) FROM decision_cases")).scalar_one() == 1


def test_t12_actual_http_flow_uses_postgres_and_no_recomputation(
    postgres_runtime, monkeypatch
) -> None:
    from fastapi.testclient import TestClient
    from pydantic import SecretStr

    import backend.app.routes.decision_cases as routes
    from backend.app.config import settings
    from backend.app.main import app
    from tests.test_decision_case_api import _payload

    _, session_factory = postgres_runtime
    reader = FakeComparisonReader()
    history = FakeHistoryReader()
    monkeypatch.setattr(settings, "t12_trusted_caller_token", SecretStr("isolated-test-token"))
    monkeypatch.setattr(routes, "get_comparison_case_reader", lambda: reader)
    monkeypatch.setattr(routes, "get_historical_performance_reader", lambda: history)
    monkeypatch.setattr(
        routes, "get_decision_unit_of_work", lambda: SqlAlchemyUnitOfWork(session_factory)
    )
    http = TestClient(app)
    base = "/api/v1/procurement/decision-cases"
    headers = {"Authorization": "Bearer isolated-test-token", "Idempotency-Key": str(uuid4())}
    created_response = http.post(base, json=_payload(), headers=headers)
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    case_id = created["decision_case_id"]
    assert http.post(base, json=_payload(), headers=headers).status_code == 200
    stored = http.get(f"{base}/{case_id}", headers=headers)
    assert stored.status_code == 200
    assert stored.json()["canonical_input"] == created["canonical_input"]
    assert stored.json()["evaluation"] == created["evaluation"]
    decision = {
        "outcome": "accept_recommendation",
        "selected_offer_id": created["recommended_offer_id"],
        "rationale": None,
        "decided_at": "2026-09-22T08:30:00Z",
        "actor_reference": "human-provided-audit-label",
    }
    final_headers = {**headers, "Idempotency-Key": str(uuid4())}
    finalized = http.post(f"{base}/{case_id}/final-decision", json=decision, headers=final_headers)
    assert finalized.status_code == 200, finalized.text
    again = http.get(f"{base}/{case_id}", headers=headers)
    assert again.json()["state"] == "finalized"
    for field in ("canonical_input", "scoring_policy", "evaluation", "provenance"):
        assert again.json()[field] == created[field]
    assert reader.calls == 1 and history.calls == 0
