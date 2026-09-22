"""Create immutable T11 decision cases.

Revision ID: 20260922_01
Revises: None
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260922_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the decision-case table and database immutability guard."""

    op.create_table(
        "decision_cases",
        sa.Column("decision_case_id", sa.String(length=36), nullable=False),
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("policy_name", sa.String(length=255), nullable=False),
        sa.Column("recommended_offer_id", sa.String(length=255), nullable=True),
        sa.Column("canonical_input_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("scoring_policy_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("evaluation_result_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("provenance_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("human_outcome", sa.String(length=32), nullable=True),
        sa.Column("selected_offer_id", sa.String(length=255), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actor_reference", sa.String(length=255), nullable=True),
        sa.Column("idempotency_key", sa.String(length=36), nullable=True),
        sa.CheckConstraint("snapshot_version = 1", name="ck_decision_cases_snapshot_version"),
        sa.CheckConstraint("state IN ('evaluated', 'finalized')", name="ck_decision_cases_state"),
        sa.CheckConstraint(
            "human_outcome IS NULL OR human_outcome IN "
            "('accept_recommendation', 'override_recommendation', 'no_award')",
            name="ck_decision_cases_human_outcome",
        ),
        sa.CheckConstraint(
            "human_outcome IS NULL OR "
            "(human_outcome = 'accept_recommendation' AND selected_offer_id IS NOT NULL) OR "
            "(human_outcome = 'override_recommendation' AND selected_offer_id IS NOT NULL "
            "AND length(btrim(rationale)) > 0) OR "
            "(human_outcome = 'no_award' AND selected_offer_id IS NULL "
            "AND length(btrim(rationale)) > 0)",
            name="ck_decision_cases_outcome_fields",
        ),
        sa.CheckConstraint(
            "(state = 'evaluated' AND human_outcome IS NULL AND selected_offer_id IS NULL "
            "AND rationale IS NULL AND decided_at IS NULL AND actor_reference IS NULL "
            "AND idempotency_key IS NULL) OR "
            "(state = 'finalized' AND human_outcome IS NOT NULL AND decided_at IS NOT NULL "
            "AND actor_reference IS NOT NULL AND idempotency_key IS NOT NULL)",
            name="ck_decision_cases_lifecycle_fields",
        ),
        sa.PrimaryKeyConstraint("decision_case_id", name="pk_decision_cases"),
        sa.UniqueConstraint("idempotency_key", name="uq_decision_cases_idempotency_key"),
    )
    op.execute(
        """
        CREATE FUNCTION reject_decision_case_snapshot_mutation()
        RETURNS trigger AS $$
        BEGIN
            IF OLD.decision_case_id IS DISTINCT FROM NEW.decision_case_id
               OR OLD.snapshot_version IS DISTINCT FROM NEW.snapshot_version
               OR OLD.created_at IS DISTINCT FROM NEW.created_at
               OR OLD.policy_name IS DISTINCT FROM NEW.policy_name
               OR OLD.recommended_offer_id IS DISTINCT FROM NEW.recommended_offer_id
               OR OLD.canonical_input_snapshot IS DISTINCT FROM NEW.canonical_input_snapshot
               OR OLD.scoring_policy_snapshot IS DISTINCT FROM NEW.scoring_policy_snapshot
               OR OLD.evaluation_result_snapshot IS DISTINCT FROM NEW.evaluation_result_snapshot
               OR OLD.provenance_snapshot IS DISTINCT FROM NEW.provenance_snapshot THEN
                RAISE EXCEPTION 'decision-case evaluation snapshots are immutable';
            END IF;
            IF OLD.state = 'finalized' AND ROW(OLD.*) IS DISTINCT FROM ROW(NEW.*) THEN
                RAISE EXCEPTION 'finalized decision cases are immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER decision_cases_immutable_update
        BEFORE UPDATE ON decision_cases
        FOR EACH ROW EXECUTE FUNCTION reject_decision_case_snapshot_mutation();
        """
    )


def downgrade() -> None:
    """Remove only the T11 schema objects."""

    op.execute("DROP TRIGGER decision_cases_immutable_update ON decision_cases")
    op.execute("DROP FUNCTION reject_decision_case_snapshot_mutation()")
    op.drop_table("decision_cases")
