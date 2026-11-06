"""Disposable PostgreSQL runtime and the API fixtures that store cases in it."""

import os
from collections.abc import Iterator

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text

from backend.app.config import settings
from backend.app.main import app
from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork
from persistence.session import create_session_factory
from tests.helpers.odoo_fakes import install_fake_odoo
from tests.helpers.planning_api import BASE, TOKEN, headers


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
    _empty_tables(engine)
    engine.dispose()
    alembic_command.downgrade(config, "base")
    alembic_command.upgrade(config, "head")
    yield engine, session_factory
    engine.dispose()


def _empty_tables(engine):
    with engine.begin() as connection:
        if connection.execute(text("SELECT to_regclass('planning_documents')")).scalar():
            connection.execute(
                text("TRUNCATE planning_documents, planning_final_decisions, planning_cases")
            )


@pytest.fixture
def postgres_history_api(postgres_runtime, history, monkeypatch):
    """Fake Odoo over ``history`` and empty PostgreSQL tables.

    Returns ``(engine, factory, payload, calls)``; ``payload`` is the preview's create body.
    """
    engine, factory = postgres_runtime
    _empty_tables(engine)
    calls = install_fake_odoo(history, monkeypatch)
    monkeypatch.setattr(
        "backend.app.routes.planning_cases.get_planning_unit_of_work",
        lambda: SqlAlchemyPlanningUnitOfWork(factory),
    )
    with TestClient(app) as client:
        preview = client.get(
            f"{BASE}/odoo-history/preview?purchase_group_id=501", headers=headers()
        )
        assert preview.status_code == 200, preview.text
    payload = {"purchase_group_id": 501, "terms": preview.json()["terms"]}
    return engine, factory, payload, calls


@pytest.fixture
def postgres_decision_api(postgres_runtime, stored_cases, monkeypatch):
    """``stored_cases`` copied into empty PostgreSQL tables, served over HTTP.

    Yields ``(engine, factory, client, base, child)``.
    """
    engine, factory = postgres_runtime
    memory, base, child, _ = stored_cases
    _empty_tables(engine)
    with SqlAlchemyPlanningUnitOfWork(factory) as uow:
        for row in memory.rows.values():
            uow.cases.add(row)
        uow.commit()
    monkeypatch.setattr(settings, "api_service_token", SecretStr(TOKEN))
    monkeypatch.setattr(
        "backend.app.routes.planning_cases.get_planning_unit_of_work",
        lambda: SqlAlchemyPlanningUnitOfWork(factory),
    )
    with TestClient(app) as client:
        yield engine, factory, client, base, child
