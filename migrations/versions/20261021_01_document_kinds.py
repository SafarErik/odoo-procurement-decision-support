"""Store a plan and an audit document per (case, language) for the PDF v3 split (ADR-036).

Existing rows are the combined v1/v2 documents (plan + audit appendix in one PDF); they
become ``kind = 'plan'`` and keep their bytes, reference and renderer version; the
reference column is widened for the longer v3 references. ADD COLUMN and widening
do not fire the row-level immutability trigger; it is disabled around the change anyway
so that no stored artifact can be touched by this migration.

Revision ID: 20261021_01
Revises: 20261019_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20261021_01"
down_revision = "20261019_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE planning_documents DISABLE TRIGGER planning_documents_immutable")
    op.add_column(
        "planning_documents",
        sa.Column("kind", sa.String(8), nullable=False, server_default="plan"),
    )
    op.alter_column("planning_documents", "kind", server_default=None)
    # v3 references add ":plan" / ":audit" and exceed the former 128 characters.
    op.alter_column(
        "planning_documents",
        "reference",
        type_=sa.String(160),
        existing_type=sa.String(128),
        existing_nullable=False,
    )
    op.drop_constraint("pk_planning_documents", "planning_documents", type_="primary")
    op.create_primary_key(
        "pk_planning_documents", "planning_documents", ["case_id", "language", "kind"]
    )
    op.create_check_constraint(
        "ck_planning_documents_kind", "planning_documents", "kind IN ('plan', 'audit')"
    )
    op.execute("ALTER TABLE planning_documents ENABLE TRIGGER planning_documents_immutable")


def downgrade() -> None:
    # The per-language baseline serves only combined v1/v2 documents. Audit documents and
    # v3 plan documents would fail its reference check, and stored artifacts are never
    # deleted, so the downgrade refuses while any of them exist.
    count = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT count(*) FROM planning_documents "
                "WHERE kind <> 'plan' OR reference LIKE 't17-approved-pdf-v3:%'"
            )
        )
        .scalar_one()
    )
    if count:
        raise RuntimeError(
            f"Downgrade refused: {count} audit or v3 plan document(s) are stored and immutable."
        )
    op.execute("ALTER TABLE planning_documents DISABLE TRIGGER planning_documents_immutable")
    op.drop_constraint("ck_planning_documents_kind", "planning_documents", type_="check")
    op.drop_constraint("pk_planning_documents", "planning_documents", type_="primary")
    op.create_primary_key("pk_planning_documents", "planning_documents", ["case_id", "language"])
    op.drop_column("planning_documents", "kind")
    op.alter_column(
        "planning_documents",
        "reference",
        type_=sa.String(128),
        existing_type=sa.String(160),
        existing_nullable=False,
    )
    op.execute("ALTER TABLE planning_documents ENABLE TRIGGER planning_documents_immutable")
