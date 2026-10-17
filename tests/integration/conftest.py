"""Shared disposable PostgreSQL runtime for integration tests."""

import os
from collections.abc import Iterator

import pytest
from alembic import command as alembic_command
from alembic.config import Config

from persistence.session import create_session_factory


@pytest.fixture(scope="module")
def postgres_runtime() -> Iterator[tuple[object, object]]:
    database_url = os.getenv("TEST_DATABASE_URL", "")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not set for the isolated test database.")

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    alembic_command.downgrade(config, "base")
    alembic_command.upgrade(config, "head")
    engine, session_factory = create_session_factory(database_url)
    yield engine, session_factory
    engine.dispose()
