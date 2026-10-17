"""Store one immutable approved PDF per (case, language) for the HU/EN PDF v2.

Existing rows are the English v1 artifacts and keep their bytes and reference; the
column default only labels them during this migration. ADD COLUMN does not fire the
row-level immutability triggers, so no stored artifact is updated.

Revision ID: 20261019_01
Revises: 20261018_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20261019_01"
down_revision = "20261018_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "planning_documents",
        sa.Column("language", sa.String(2), nullable=False, server_default="en"),
    )
    op.alter_column("planning_documents", "language", server_default=None)
    op.drop_constraint("planning_documents_pkey", "planning_documents", type_="primary")
    op.create_primary_key("pk_planning_documents", "planning_documents", ["case_id", "language"])
    op.create_check_constraint(
        "ck_planning_documents_language", "planning_documents", "language IN ('hu', 'en')"
    )


def downgrade() -> None:
    # Hungarian artifacts cannot be represented by the single-language baseline.
    op.execute("ALTER TABLE planning_documents DISABLE TRIGGER planning_documents_immutable")
    op.execute("DELETE FROM planning_documents WHERE language <> 'en'")
    op.execute("ALTER TABLE planning_documents ENABLE TRIGGER planning_documents_immutable")
    op.drop_constraint("ck_planning_documents_language", "planning_documents", type_="check")
    op.drop_constraint("pk_planning_documents", "planning_documents", type_="primary")
    op.create_primary_key("planning_documents_pkey", "planning_documents", ["case_id"])
    op.drop_column("planning_documents", "language")
