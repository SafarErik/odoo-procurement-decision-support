"""The per-language PDF migration keeps stored English artifacts byte-identical."""

import os

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy import text

from tests.integration.test_t17_decisions_postgres import configured as _configured
from tests.integration.test_t17_decisions_postgres import stored_cases as _stored_cases
from tests.test_t17_decisions import headers
from tests.test_t21_documents import approve

pytestmark = pytest.mark.integration
configured = _configured
stored_cases = _stored_cases


def test_downgrade_and_upgrade_preserve_english_artifact(configured):
    engine, _, client, base, _ = configured
    _, url = approve(client, base)
    english = client.get(url, params={"language": "en"}, headers=headers())
    assert english.status_code == 200
    assert client.get(url, headers=headers()).status_code == 200  # Hungarian
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
        assert connection.execute(text("SELECT count(*) FROM planning_documents")).scalar() == 1
    engine.dispose()
    alembic_command.upgrade(config, "head")
    again = client.get(url, params={"language": "en"}, headers=headers())
    assert again.status_code == 200 and again.content == english.content
    assert again.headers["x-pdf-reference"] == english.headers["x-pdf-reference"]
