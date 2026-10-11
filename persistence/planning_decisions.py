"""PostgreSQL finalization namespace, immutable records and transaction locks."""

import json

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from application.decision_cases import RepositoryError
from application.planning_decisions import PlanningFinalDecision
from application.planning_serialization import snapshot_json
from persistence.schema import PlanningFinalDecisionRecord


class SqlAlchemyPlanningDecisionRepository:
    def __init__(self, session):
        self._session = session

    def lock(self, key):
        try:
            self._session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": "t17:" + key}
            )
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "Finalization could not be locked."
            ) from error

    def _read(self, statement):
        try:
            row = self._session.execute(statement).scalar_one_or_none()
            if row is None:
                return None
            decision = PlanningFinalDecision(
                row.case_id, row.idempotency_key, row.fingerprint, snapshot_json(row.record)
            )
            if decision.record_hash != row.record_hash:
                raise RepositoryError(
                    "invalid_persisted_decision", "Final decision integrity failed."
                )
            return decision
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "Final decision could not be read."
            ) from error

    def get(self, case_id):
        return self._read(
            select(PlanningFinalDecisionRecord).where(
                PlanningFinalDecisionRecord.case_id == case_id
            )
        )

    def by_key(self, key):
        return self._read(
            select(PlanningFinalDecisionRecord).where(
                PlanningFinalDecisionRecord.idempotency_key == key
            )
        )

    def add(self, decision):
        self._session.add(
            PlanningFinalDecisionRecord(
                case_id=decision.case_id,
                idempotency_key=decision.idempotency_key,
                fingerprint=decision.fingerprint,
                record_hash=decision.record_hash,
                record=json.loads(decision.record),
            )
        )
        try:
            self._session.flush()
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "Final decision could not be stored."
            ) from error
