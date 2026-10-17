"""Real PDF artifact transactions, approval binding and immutability."""

import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import pytest
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from application.errors import RepositoryError
from document_adapter.approved_pdf import render_approved_pdf
from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork
from tests.integration.test_t17_decisions_postgres import configured as _configured
from tests.integration.test_t17_decisions_postgres import stored_cases as _stored_cases
from tests.test_t15_planning_api import forbidden
from tests.test_t17_decisions import BASE, headers
from tests.test_t21_documents import approve

pytestmark = pytest.mark.integration
configured = _configured
stored_cases = _stored_cases


def test_contending_pdf_downloads_store_one_artifact_without_changing_approval(
    configured, monkeypatch
):
    engine, _, client, base, _ = configured
    decision, url = approve(client, base)
    calls = []

    def render(content):
        calls.append(content)
        return render_approved_pdf(content)

    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", render)
    with engine.connect() as holder, ThreadPoolExecutor(max_workers=2) as pool:
        holder.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
            {"key": "t21:pdf:" + base["case_id"]},
        )
        futures = [pool.submit(client.get, url, headers=headers()) for _ in range(2)]
        try:
            deadline = time.monotonic() + 10
            waiting = 0
            while time.monotonic() < deadline:
                holder.execute(text("SELECT pg_stat_clear_snapshot()"))
                waiting = holder.execute(
                    text(
                        "SELECT count(*) FROM pg_stat_activity WHERE "
                        "datname=current_database() AND wait_event='advisory' "
                        "AND pid <> pg_backend_pid()"
                    )
                ).scalar_one()
                if waiting >= 2:
                    break
                time.sleep(0.05)
            assert waiting >= 2
        finally:
            holder.commit()
        responses = [f.result(timeout=30) for f in futures]
    assert [r.status_code for r in responses] == [200, 200]
    assert len(calls) == 1 and calls[0] == decision["approved_content"]
    assert responses[0].content == responses[1].content
    assert (
        "Approved procurement plan"
        in PdfReader(BytesIO(responses[0].content)).pages[0].extract_text()
    )
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM planning_documents")).scalar_one() == 1
        assert (
            connection.execute(
                text("SELECT snapshot_hash FROM planning_cases WHERE case_id=:id"),
                {"id": base["case_id"]},
            ).scalar_one()
            == base["snapshot_hash"]
        )
    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", forbidden)
    assert client.get(url, headers=headers()).status_code == 200
    assert (
        client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["final_decision"]
        == decision
    )


@pytest.mark.parametrize(
    "mutation", ["UPDATE planning_documents SET pdf = pdf", "DELETE FROM planning_documents"]
)
def test_direct_pdf_mutation_rejected(configured, mutation):
    engine, _, client, base, _ = configured
    _, url = approve(client, base)
    assert client.get(url, headers=headers()).status_code == 200
    with pytest.raises(DBAPIError), engine.begin() as connection:
        connection.execute(text(mutation))


def test_pdf_insert_requires_exact_approved_content(configured):
    engine, _, client, base, _ = configured
    _, url = approve(client, base)
    assert client.get(url, headers=headers()).status_code == 200
    with pytest.raises(DBAPIError, match="PDF artifacts require"), engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO planning_documents "
                "SELECT case_id, content_version, repeat('0',64), reference || '-bad', "
                "renderer_version, pdf_hash, pdf FROM planning_documents"
            )
        )


def test_render_failure_and_post_flush_rollback_leave_approval_intact(configured, monkeypatch):
    engine, _, client, base, _ = configured
    decision, url = approve(client, base)

    def fail(*args):
        raise RepositoryError("repository_failure", "PDF save failed")

    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", fail)
    assert client.get(url, headers=headers()).status_code == 503
    monkeypatch.setattr(
        "backend.app.routes.planning_cases.render_approved_document", render_approved_pdf
    )
    commit = SqlAlchemyPlanningUnitOfWork.commit
    monkeypatch.setattr(SqlAlchemyPlanningUnitOfWork, "commit", fail)
    assert client.get(url, headers=headers()).status_code == 503
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM planning_documents")).scalar_one() == 0
    assert (
        client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["final_decision"]
        == decision
    )
    monkeypatch.setattr(SqlAlchemyPlanningUnitOfWork, "commit", commit)
    assert client.get(url, headers=headers()).status_code == 200
