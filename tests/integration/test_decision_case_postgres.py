"""PostgreSQL migration, transaction, immutability, and session tests for T11."""

from __future__ import annotations

import os
from collections.abc import Iterator
from uuid import uuid4

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

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
        connection.execute(text("TRUNCATE TABLE decision_cases"))
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
            "20260922_01"
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
