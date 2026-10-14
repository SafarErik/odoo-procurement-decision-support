"""Additive catalog schema, immutable joins and unchanged UUID retrieval."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from backend.app.config import settings
from backend.app.main import app
from tests.integration.test_t15_planning_postgres import (
    assets as _assets,
)
from tests.integration.test_t15_planning_postgres import (
    configured as _configured,
)
from tests.integration.test_t15_planning_postgres import (
    headers,
)
from tests.integration.test_t15_planning_postgres import (
    postgres_runtime as _postgres_runtime,
)

assets = _assets
configured = _configured
postgres_runtime = _postgres_runtime
pytestmark = pytest.mark.integration
BASE = "/api/v2/procurement/planning-cases"


def test_empty_catalog_immutable_base_only_and_inherited_queries(configured, monkeypatch):
    engine, _, payload = configured
    monkeypatch.setattr(settings, "planning_library_company_id", payload["company_id"])
    with TestClient(app) as client:
        base = client.post(BASE, json=payload, headers=headers()).json()
        child = client.post(
            f"{BASE}/{base['case_id']}/scenarios",
            headers=headers(),
            json={
                "kind": "supplier_outage",
                "source": payload["requirement_source"],
                "suppliers": [
                    {"supplier_id": payload["suppliers"][0]["supplier_id"], "available": False}
                ],
            },
        ).json()
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT count(*) FROM planning_case_catalog")).scalar_one()
                == 0
            )
        assert not client.get(BASE, headers=headers()).json()["items"]
        assert (
            client.get(BASE, params={"workspace": "unclassified"}, headers=headers()).json()[
                "items"
            ][0]["case_id"]
            == base["case_id"]
        )
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO planning_case_catalog(case_id,workspace) VALUES (:id,'practice')"
                ),
                {"id": base["case_id"]},
            )
        for statement, case_id in (
            (
                "INSERT INTO planning_case_catalog(case_id,workspace) VALUES (:id,'practice')",
                child["case_id"],
            ),
            (
                "UPDATE planning_case_catalog SET workspace='controlled' WHERE case_id=:id",
                base["case_id"],
            ),
            ("DELETE FROM planning_case_catalog WHERE case_id=:id", base["case_id"]),
        ):
            with pytest.raises(DBAPIError), engine.begin() as connection:
                connection.execute(text(statement), {"id": case_id})
        assert not client.get(BASE, params={"workspace": "unclassified"}, headers=headers()).json()[
            "items"
        ]
        page = client.get(BASE, params={"workspace": "practice"}, headers=headers()).json()
        assert page["items"][0]["workspace"] == "practice"
        children = client.get(
            f"{BASE}/{base['case_id']}/scenarios",
            params={"workspace": "practice"},
            headers=headers(),
        ).json()
        assert children["items"][0]["case_id"] == child["case_id"]
        assert children["items"][0]["workspace"] == "practice"
        assert (
            client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["snapshot_hash"]
            == base["snapshot_hash"]
        )
