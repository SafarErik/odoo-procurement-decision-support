"""T15 uses the existing PostgreSQL session/transaction and advisory-lock patterns."""

import json
from datetime import UTC

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from application.decision_cases import RepositoryError
from application.planning_cases import SNAPSHOT_VERSION, PlanningCase, validate_snapshot
from application.planning_serialization import snapshot_json
from persistence.planning_decisions import SqlAlchemyPlanningDecisionRepository
from persistence.postgres import SqlAlchemyUnitOfWork
from persistence.schema import PlanningCaseRecord


class SqlAlchemyPlanningRepository:
    def __init__(self, session):
        self._session = session

    def lock(self, key: str) -> None:
        try:
            self._session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": "t15:" + key}
            )
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "The planning key could not be locked."
            ) from error

    def _read(self, statement) -> PlanningCase | None:
        try:
            row = self._session.execute(statement).scalar_one_or_none()
            if row is None:
                return None
            case = PlanningCase(
                row.case_id,
                row.created_at.astimezone(UTC),
                row.parent_id,
                row.idempotency_key,
                row.fingerprint,
                snapshot_json(row.snapshot),
            )
            if row.snapshot_version != SNAPSHOT_VERSION or case.snapshot_hash != row.snapshot_hash:
                raise RepositoryError(
                    "invalid_persisted_case", "The planning snapshot integrity check failed."
                )
            validate_snapshot(case)
            return case
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "The planning case could not be read."
            ) from error

    def by_key(self, key: str) -> PlanningCase | None:
        return self._read(
            select(PlanningCaseRecord).where(PlanningCaseRecord.idempotency_key == key)
        )

    def get(self, case_id: str) -> PlanningCase | None:
        return self._read(select(PlanningCaseRecord).where(PlanningCaseRecord.case_id == case_id))

    def add(self, case: PlanningCase) -> None:
        validate_snapshot(case)
        self._session.add(
            PlanningCaseRecord(
                case_id=case.case_id,
                parent_id=case.parent_id,
                created_at=case.created_at,
                idempotency_key=case.idempotency_key,
                fingerprint=case.fingerprint,
                snapshot_version=SNAPSHOT_VERSION,
                snapshot_hash=case.snapshot_hash,
                snapshot=json.loads(case.snapshot),
            )
        )
        try:
            self._session.flush()
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "The planning case could not be stored."
            ) from error


class SqlAlchemyPlanningUnitOfWork(SqlAlchemyUnitOfWork):
    def __enter__(self):
        super().__enter__()
        self.cases = SqlAlchemyPlanningRepository(self._session)
        self.decisions = SqlAlchemyPlanningDecisionRepository(self._session)
        return self
