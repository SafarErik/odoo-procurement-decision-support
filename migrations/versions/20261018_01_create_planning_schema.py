"""Create the immutable planning schema: cases, final decisions and approved PDFs.

Earlier development migrations (V1 decision cases, presentation catalog) were folded
into this baseline on 2026-10-18; existing development databases must be recreated.

Revision ID: 20261018_01
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261018_01"
down_revision = None
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

    op.create_table(
        "planning_documents",
        sa.Column("case_id", sa.String(36), primary_key=True),
        sa.Column("content_version", sa.String(64), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("reference", sa.String(128), nullable=False, unique=True),
        sa.Column("renderer_version", sa.String(128), nullable=False),
        sa.Column("pdf_hash", sa.String(64), nullable=False),
        sa.Column("pdf", sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["planning_final_decisions.case_id"]),
        sa.CheckConstraint("octet_length(pdf) BETWEEN 1 AND 2097152", name="ck_pdf_size"),
    )
    op.execute("""
        CREATE TRIGGER planning_documents_immutable
        BEFORE UPDATE OR DELETE ON planning_documents
        FOR EACH ROW EXECUTE FUNCTION reject_planning_case_mutation();

        CREATE FUNCTION require_approved_planning_content() RETURNS trigger AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM planning_final_decisions
                           WHERE case_id = NEW.case_id
                           AND record #>> '{audit,outcome}' = 'approve'
                           AND record ->> 'approved_content_hash' = NEW.content_hash
                           AND record #>> '{approved_content,content_version}'
                               = NEW.content_version)
            THEN
                RAISE EXCEPTION 'PDF artifacts require the exact approved content';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER planning_documents_approved_only
        BEFORE INSERT ON planning_documents
        FOR EACH ROW EXECUTE FUNCTION require_approved_planning_content();
    """)


def downgrade() -> None:
    op.drop_table("planning_documents")
    op.execute("DROP FUNCTION require_approved_planning_content()")
    op.drop_table("planning_final_decisions")
    op.execute("DROP FUNCTION require_original_planning_base()")
    op.drop_table("planning_cases")
    op.execute("DROP FUNCTION reject_planning_case_mutation()")
