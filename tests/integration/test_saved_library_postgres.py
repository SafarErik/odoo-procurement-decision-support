"""Saved-case library: origin filter on stored snapshots and unchanged UUID retrieval."""

import pytest
from fastapi.testclient import TestClient

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

assets = _assets
configured = _configured
pytestmark = pytest.mark.integration
BASE = "/api/v2/procurement/planning-cases"


def test_origin_filter_reads_stored_snapshots_for_bases_and_scenarios(configured, monkeypatch):
    _, _, payload = configured
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
        assert base["origin"] == child["origin"] == "demo"
        for origin, expected in (("all", [base["case_id"]]), ("demo", [base["case_id"]])):
            page = client.get(BASE, params={"origin": origin}, headers=headers()).json()
            assert [item["case_id"] for item in page["items"]] == expected
            assert all(item["origin"] == "demo" for item in page["items"])
        assert not client.get(BASE, params={"origin": "odoo"}, headers=headers()).json()["items"]
        children = client.get(
            f"{BASE}/{base['case_id']}/scenarios", params={"origin": "demo"}, headers=headers()
        ).json()
        assert [item["case_id"] for item in children["items"]] == [child["case_id"]]
        assert (
            client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["snapshot_hash"]
            == base["snapshot_hash"]
        )
