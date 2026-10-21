"""Document migrations: per-language (20261019) and plan/audit kinds (20261021, ADR-036).

Since the split the API only stores v3 documents, so the combined v1/v2 artifacts these
migrations must preserve are written with SQL at the older schema.
"""

import hashlib
import os

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from backend.app.dependencies import render_approved_document
from document_adapter.approved_pdf import render_plan_pdf
from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork
from tests.integration.test_t17_decisions_postgres import configured as _configured
from tests.integration.test_t17_decisions_postgres import stored_cases as _stored_cases
from tests.legacy_cases import create_legacy_case
from tests.t15_helpers import controlled_assets
from tests.test_t15_planning_api import forbidden
from tests.test_t17_decisions import headers
from tests.test_t21_documents import approve

pytestmark = pytest.mark.integration
configured = _configured
stored_cases = _stored_cases


def _config():
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", os.environ["TEST_DATABASE_URL"].replace("%", "%%"))
    return config


def _migrate(engine, direction, revision):
    engine.dispose()
    getattr(alembic_command, direction)(_config(), revision)


def _insert_combined(engine, decision, case_id, language, reference, renderer):
    """A combined plan + appendix artifact as stored before the split (no kind column)."""
    pdf, _ = render_plan_pdf(decision["approved_content"], language)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO planning_documents (case_id, language, content_version, "
                "content_hash, reference, renderer_version, pdf_hash, pdf) "
                "VALUES (:case, :language, :version, :hash, :reference, :renderer, "
                ":pdf_hash, :pdf)"
            ),
            {
                "case": case_id,
                "language": language,
                "version": decision["approved_content"]["content_version"],
                "hash": decision["approved_content_hash"],
                "reference": reference,
                "renderer": renderer,
                "pdf_hash": hashlib.sha256(pdf).hexdigest(),
                "pdf": pdf,
            },
        )
    return pdf


def test_per_language_downgrade_keeps_v1_english_and_removes_v2(configured, tmp_path):
    engine, factory, client, base, _ = configured
    decision, url = approve(client, base)
    other = create_legacy_case(
        SqlAlchemyPlanningUnitOfWork(factory), controlled_assets(tmp_path / "m"), tmp_path / "m"
    )
    other_decision, other_url = approve(client, other)
    content_hash = decision["approved_content_hash"]
    _migrate(engine, "downgrade", "20261019_01")
    _insert_combined(
        engine,
        decision,
        base["case_id"],
        "hu",
        f"t17-approved-pdf-v2:{base['case_id']}:hu:{content_hash}",
        "legacy/layout-v3",
    )
    v1 = f"t17-approved-pdf-v1:{base['case_id']}:{content_hash}"
    legacy = _insert_combined(engine, decision, base["case_id"], "en", v1, "legacy/layout-v1")
    other_hash = other_decision["approved_content_hash"]
    _insert_combined(
        engine,
        other_decision,
        other["case_id"],
        "en",
        f"t17-approved-pdf-v2:{other['case_id']}:en:{other_hash}",
        "legacy/layout-v4",
    )

    _migrate(engine, "downgrade", "20261018_01")
    with engine.connect() as connection:
        columns = connection.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'planning_documents'"
            )
        ).scalars()
        assert "language" not in set(columns)
        rows = connection.execute(text("SELECT case_id, reference FROM planning_documents")).all()
    assert rows == [(base["case_id"], v1)]
    _migrate(engine, "upgrade", "head")

    again = client.get(url, params={"language": "en"}, headers=headers())
    assert again.status_code == 200 and again.content == legacy
    assert again.headers["x-pdf-reference"] == v1 and again.headers["x-document-kind"] == "plan"
    rerendered = client.get(other_url, params={"language": "en"}, headers=headers())
    assert rerendered.status_code == 200
    assert rerendered.headers["x-pdf-reference"] == (
        f"t17-approved-pdf-v3:{other['case_id']}:en:plan:{other_hash}"
    )


@pytest.mark.parametrize("renderer", ["layout-v3", "layout-v4"])
def test_combined_documents_become_plan_and_downgrade_refuses_audit(
    configured, monkeypatch, renderer
):
    engine, _, client, base, _ = configured
    decision, url = approve(client, base)
    content_hash = decision["approved_content_hash"]
    reference = f"t17-approved-pdf-v2:{base['case_id']}:hu:{content_hash}"
    renderer_version = f"reportlab/ProcurementDejaVu/{renderer}"
    _migrate(engine, "downgrade", "20261019_01")
    combined = _insert_combined(
        engine, decision, base["case_id"], "hu", reference, renderer_version
    )
    _migrate(engine, "upgrade", "head")

    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT kind, reference, renderer_version, pdf_hash, pdf "
                "FROM planning_documents WHERE case_id = :case"
            ),
            {"case": base["case_id"]},
        ).one()
    assert tuple(row) == (
        "plan",
        reference,
        renderer_version,
        hashlib.sha256(combined).hexdigest(),
        combined,
    )
    route_renderer = "backend.app.routes.planning_cases.render_approved_document"
    monkeypatch.setattr(route_renderer, forbidden)
    plan = client.get(url, headers=headers())
    assert plan.status_code == 200 and plan.content == combined
    assert plan.headers["x-pdf-reference"] == reference
    assert plan.headers["x-document-kind"] == "plan"
    monkeypatch.setattr(route_renderer, render_approved_document)
    audit = client.get(url, params={"kind": "audit"}, headers=headers())
    assert audit.status_code == 200 and audit.headers["x-document-kind"] == "audit"
    assert audit.headers["x-approved-content-hash"] == content_hash
    assert audit.headers["x-pdf-reference"] == (
        f"t17-approved-pdf-v3:{base['case_id']}:hu:audit:{content_hash}"
    )

    with pytest.raises(RuntimeError, match="Downgrade refused"):
        _migrate(engine, "downgrade", "20261019_01")
    with engine.connect() as connection:
        kinds = connection.execute(
            text("SELECT kind FROM planning_documents ORDER BY kind")
        ).scalars()
        assert list(kinds) == ["audit", "plan"]
    with pytest.raises(DBAPIError), engine.begin() as connection:
        connection.execute(text("UPDATE planning_documents SET kind = 'audit'"))
    with pytest.raises(DBAPIError), engine.begin() as connection:
        connection.execute(text("DELETE FROM planning_documents WHERE kind = 'audit'"))
