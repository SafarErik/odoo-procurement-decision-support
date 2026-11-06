"""Saved-case library: company scope on stored snapshots and unchanged UUID retrieval."""

import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app
from tests.helpers.planning_api import BASE, create_case, headers

pytestmark = pytest.mark.integration


def test_library_reads_stored_snapshots_for_bases_and_scenarios(postgres_history_api, monkeypatch):
    _, _, payload, _ = postgres_history_api
    with TestClient(app) as client:
        base = create_case(client, payload["terms"])
        child = client.post(
            f"{BASE}/{base['case_id']}/scenarios",
            headers=headers(),
            json={
                "kind": "supplier_outage",
                "source": payload["terms"]["requirement_source"],
                "suppliers": [
                    {
                        "supplier_id": payload["terms"]["suppliers"][0]["supplier_id"],
                        "available": False,
                    }
                ],
            },
        ).json()
        monkeypatch.setattr(settings, "planning_library_company_id", payload["terms"]["company_id"])
        page = client.get(BASE, headers=headers())
        assert page.status_code == 200, page.text
        assert [item["case_id"] for item in page.json()["items"]] == [base["case_id"]]
        monkeypatch.setattr(settings, "planning_library_company_id", "odoo:res.company:999")
        assert not client.get(BASE, headers=headers()).json()["items"]
        monkeypatch.setattr(settings, "planning_library_company_id", payload["terms"]["company_id"])
        children = client.get(f"{BASE}/{base['case_id']}/scenarios", headers=headers()).json()
        assert [item["case_id"] for item in children["items"]] == [child["case_id"]]
        assert (
            client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["snapshot_hash"]
            == base["snapshot_hash"]
        )
