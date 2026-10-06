"""Add isolated immutable controlled V2 planning cases.

Revision ID: 20261005_01
Revises: 20260922_02
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261005_01"
down_revision = "20260922_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "planning_cases",
        sa.Column("case_id", sa.String(36), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idempotency_key", sa.String(36), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("snapshot_version", sa.String(64), nullable=False),
        sa.Column("snapshot_hash", sa.String(64), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("case_id", name="pk_planning_cases"),
        sa.ForeignKeyConstraint(["parent_id"], ["planning_cases.case_id"]),
        sa.UniqueConstraint("idempotency_key"),
        sa.CheckConstraint(
            "snapshot_version = 't15-controlled-planning-v1'", name="ck_planning_cases_version"
        ),
    )
    op.execute("""
        CREATE FUNCTION reject_planning_case_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'planning-case snapshots and creation mappings are immutable';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER planning_cases_immutable
        BEFORE UPDATE OR DELETE ON planning_cases
        FOR EACH ROW EXECUTE FUNCTION reject_planning_case_mutation();
    """)


def downgrade() -> None:
    op.drop_table("planning_cases")
    op.execute("DROP FUNCTION reject_planning_case_mutation()")
