"""SQLAlchemy mapping for the T11 PostgreSQL decision-case table."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative metadata consumed by Alembic only."""


class DecisionCaseRecord(Base):
    """Persistence representation; domain objects deliberately remain non-ORM."""

    __tablename__ = "decision_cases"
    __table_args__ = (
        PrimaryKeyConstraint("decision_case_id", name="pk_decision_cases"),
        UniqueConstraint("idempotency_key", name="uq_decision_cases_idempotency_key"),
        CheckConstraint("snapshot_version = 1", name="ck_decision_cases_snapshot_version"),
        CheckConstraint("state IN ('evaluated', 'finalized')", name="ck_decision_cases_state"),
        CheckConstraint(
            "human_outcome IS NULL OR human_outcome IN "
            "('accept_recommendation', 'override_recommendation', 'no_award')",
            name="ck_decision_cases_human_outcome",
        ),
        CheckConstraint(
            "human_outcome IS NULL OR "
            "(human_outcome = 'accept_recommendation' AND selected_offer_id IS NOT NULL) OR "
            "(human_outcome = 'override_recommendation' AND selected_offer_id IS NOT NULL "
            "AND length(btrim(rationale)) > 0) OR "
            "(human_outcome = 'no_award' AND selected_offer_id IS NULL "
            "AND length(btrim(rationale)) > 0)",
            name="ck_decision_cases_outcome_fields",
        ),
        CheckConstraint(
            "(state = 'evaluated' AND human_outcome IS NULL AND selected_offer_id IS NULL "
            "AND rationale IS NULL AND decided_at IS NULL AND actor_reference IS NULL "
            "AND idempotency_key IS NULL) OR "
            "(state = 'finalized' AND human_outcome IS NOT NULL AND decided_at IS NOT NULL "
            "AND actor_reference IS NOT NULL AND idempotency_key IS NOT NULL)",
            name="ck_decision_cases_lifecycle_fields",
        ),
    )

    decision_case_id: Mapped[str] = mapped_column(String(36), nullable=False)
    snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recommended_offer_id: Mapped[str | None] = mapped_column(String(255))
    canonical_input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    scoring_policy_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    evaluation_result_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    provenance_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    human_outcome: Mapped[str | None] = mapped_column(String(32))
    selected_offer_id: Mapped[str | None] = mapped_column(String(255))
    rationale: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actor_reference: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str | None] = mapped_column(String(36))


class DecisionCaseCreationRecord(Base):
    """Durable create-key mapping, committed with its immutable case."""

    __tablename__ = "decision_case_creations"
    __table_args__ = (PrimaryKeyConstraint("idempotency_key", name="pk_decision_case_creations"),)

    idempotency_key: Mapped[str] = mapped_column(String(36), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("decision_cases.decision_case_id"), nullable=False, unique=True
    )


class PlanningCaseRecord(Base):
    """Immutable V2 snapshot and creation mapping in one atomic row; V1 stays intact."""

    __tablename__ = "planning_cases"
    __table_args__ = (
        PrimaryKeyConstraint("case_id", name="pk_planning_cases"),
        CheckConstraint(
            "snapshot_version = 't15-controlled-planning-v1'", name="ck_planning_cases_version"
        ),
    )

    case_id: Mapped[str] = mapped_column(String(36), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("planning_cases.case_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_version: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class PlanningFinalDecisionRecord(Base):
    """One immutable human outcome and approved content per original planning case."""

    __tablename__ = "planning_final_decisions"

    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("planning_cases.case_id"), primary_key=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    record: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class PlanningDocumentRecord(Base):
    """One immutable rendered artifact for the immutable approved content."""

    __tablename__ = "planning_documents"

    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("planning_final_decisions.case_id"), primary_key=True
    )
    content_version: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    reference: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    renderer_version: Mapped[str] = mapped_column(String(128), nullable=False)
    pdf_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    pdf: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
