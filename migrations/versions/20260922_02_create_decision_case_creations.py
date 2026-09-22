"""Add atomic creation-idempotency mapping.

Revision ID: 20260922_02
Revises: 20260922_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20260922_02"
down_revision = "20260922_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decision_case_creations",
        sa.Column("idempotency_key", sa.String(36), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("decision_case_id", sa.String(36), nullable=False),
        sa.PrimaryKeyConstraint("idempotency_key", name="pk_decision_case_creations"),
        sa.ForeignKeyConstraint(["decision_case_id"], ["decision_cases.decision_case_id"]),
        sa.UniqueConstraint("decision_case_id"),
    )


def downgrade() -> None:
    op.drop_table("decision_case_creations")
