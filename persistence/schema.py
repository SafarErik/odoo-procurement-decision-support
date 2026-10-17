"""SQLAlchemy mapping of the planning tables (consumed by Alembic and repositories)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    LargeBinary,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative metadata consumed by Alembic only."""


class PlanningCaseRecord(Base):
    """Immutable planning snapshot and creation mapping in one atomic row."""

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
