"""Shared disposable PostgreSQL runtime for integration tests."""

import os
from collections.abc import Iterator

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy import text

from persistence.session import create_session_factory


@pytest.fixture(scope="module")
def postgres_runtime() -> Iterator[tuple[object, object]]:
    database_url = os.getenv("TEST_DATABASE_URL", "")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not set for the isolated test database.")

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    engine, session_factory = create_session_factory(database_url)
    # Stored documents are immutable and the document downgrade refuses to drop audit/v3
    # artifacts; TRUNCATE fires no row triggers, so empty the disposable tables first.
    with engine.begin() as connection:
        if connection.execute(text("SELECT to_regclass('planning_documents')")).scalar():
            connection.execute(
                text("TRUNCATE planning_documents, planning_final_decisions, planning_cases")
            )
    engine.dispose()
    alembic_command.downgrade(config, "base")
    alembic_command.upgrade(config, "head")
    yield engine, session_factory
    engine.dispose()
