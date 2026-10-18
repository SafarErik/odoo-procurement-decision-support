"""The per-language PDF migration: v1 English artifacts survive a round trip, v2 rows go."""

import os

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy import text

from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork
from tests.integration.test_t17_decisions_postgres import configured as _configured
from tests.integration.test_t17_decisions_postgres import stored_cases as _stored_cases
from tests.legacy_cases import create_legacy_case
from tests.t15_helpers import controlled_assets
from tests.test_t17_decisions import headers
from tests.test_t21_documents import approve

pytestmark = pytest.mark.integration
configured = _configured
stored_cases = _stored_cases


def test_downgrade_keeps_v1_english_and_removes_v2_artifacts(configured, tmp_path):
    engine, factory, client, base, _ = configured
    _, url = approve(client, base)
    assert client.get(url, headers=headers()).status_code == 200  # Hungarian v2
    with engine.begin() as connection:  # a pre-P2 English v1 artifact of the same content
        connection.execute(
            text(
                "INSERT INTO planning_documents (case_id, content_version, content_hash, "
                "reference, renderer_version, pdf_hash, pdf, language) "
                "SELECT case_id, content_version, content_hash, "
                "'t17-approved-pdf-v1:' || case_id || ':' || content_hash, "
                "'legacy/layout-v1', pdf_hash, pdf, 'en' "
                "FROM planning_documents WHERE language = 'hu'"
            )
        )
    legacy = client.get(url, params={"language": "en"}, headers=headers())
    assert legacy.headers["x-pdf-reference"].startswith("t17-approved-pdf-v1:")
    other = create_legacy_case(
        SqlAlchemyPlanningUnitOfWork(factory), controlled_assets(tmp_path / "m"), tmp_path / "m"
    )
    _, other_url = approve(client, other)
    english_v2 = client.get(other_url, params={"language": "en"}, headers=headers())
    assert english_v2.headers["x-pdf-reference"].startswith("t17-approved-pdf-v2:")

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", os.environ["TEST_DATABASE_URL"].replace("%", "%%"))
    engine.dispose()
    alembic_command.downgrade(config, "20261018_01")
    with engine.connect() as connection:
        columns = connection.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'planning_documents'"
            )
        ).scalars()
        assert "language" not in set(columns)
        rows = connection.execute(text("SELECT case_id, reference FROM planning_documents")).all()
    assert rows == [(base["case_id"], legacy.headers["x-pdf-reference"])]
    engine.dispose()
    alembic_command.upgrade(config, "head")

    again = client.get(url, params={"language": "en"}, headers=headers())
    assert again.status_code == 200 and again.content == legacy.content
    assert again.headers["x-pdf-reference"] == legacy.headers["x-pdf-reference"]
    rerendered = client.get(other_url, params={"language": "en"}, headers=headers())
    assert rerendered.status_code == 200
    assert rerendered.headers["x-pdf-reference"] == english_v2.headers["x-pdf-reference"]
