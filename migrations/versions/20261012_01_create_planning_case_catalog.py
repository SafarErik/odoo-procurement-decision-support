"""Add empty immutable case catalog; no backfill or snapshot changes.

Revision ID: 20261012_01
Revises: 20261010_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20261012_01"
down_revision = "20261010_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "planning_case_catalog",
        sa.Column("case_id", sa.String(36), primary_key=True),
        sa.Column("workspace", sa.String(16), nullable=False),
        sa.Column("example_id", sa.String(80)),
        sa.ForeignKeyConstraint(["case_id"], ["planning_cases.case_id"]),
        sa.CheckConstraint("workspace IN ('controlled', 'practice')", name="ck_catalog_workspace"),
    )
    op.create_index("ix_planning_case_catalog_workspace", "planning_case_catalog", ["workspace"])
    op.execute("""
        CREATE TRIGGER planning_case_catalog_immutable
        BEFORE UPDATE OR DELETE ON planning_case_catalog
        FOR EACH ROW EXECUTE FUNCTION reject_planning_case_mutation();

        CREATE FUNCTION require_catalog_original_base() RETURNS trigger AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM planning_cases
                           WHERE case_id = NEW.case_id AND parent_id IS NULL)
            THEN
                RAISE EXCEPTION 'Catalog classification requires an original base';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER planning_case_catalog_original_only
        BEFORE INSERT ON planning_case_catalog
        FOR EACH ROW EXECUTE FUNCTION require_catalog_original_base();
    """)


def downgrade():
    op.drop_table("planning_case_catalog")
    op.execute("DROP FUNCTION require_catalog_original_base()")
