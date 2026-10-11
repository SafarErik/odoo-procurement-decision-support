"""Store immutable approved PDF artifacts separately from human decisions.

Revision ID: 20261010_01
Revises: 20261009_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20261010_01"
down_revision = "20261009_01"
branch_labels = None
depends_on = None


def upgrade():
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


def downgrade():
    op.drop_table("planning_documents")
    op.execute("DROP FUNCTION require_approved_planning_content()")
