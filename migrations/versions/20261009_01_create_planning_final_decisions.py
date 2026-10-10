"""Add immutable V2 human decisions without changing planning snapshots.

Revision ID: 20261009_01
Revises: 20261005_01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261009_01"
down_revision = "20261005_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "planning_final_decisions",
        sa.Column("case_id", sa.String(36), nullable=False),
        sa.Column("idempotency_key", sa.String(36), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("record_hash", sa.String(64), nullable=False),
        sa.Column("record", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("case_id"),
        sa.ForeignKeyConstraint(["case_id"], ["planning_cases.case_id"]),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.execute("""
        CREATE TRIGGER planning_final_decisions_immutable
        BEFORE UPDATE OR DELETE ON planning_final_decisions
        FOR EACH ROW EXECUTE FUNCTION reject_planning_case_mutation();

        CREATE FUNCTION require_original_planning_base() RETURNS trigger AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM planning_cases
                           WHERE case_id = NEW.case_id AND parent_id IS NULL) THEN
                RAISE EXCEPTION 'final decisions require an original planning base';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER planning_final_decisions_base_only
        BEFORE INSERT ON planning_final_decisions
        FOR EACH ROW EXECUTE FUNCTION require_original_planning_base();
    """)


def downgrade():
    op.drop_table("planning_final_decisions")
    op.execute("DROP FUNCTION require_original_planning_base()")
