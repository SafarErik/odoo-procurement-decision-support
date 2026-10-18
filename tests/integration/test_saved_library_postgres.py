"""Saved-case library: origin filter on stored snapshots and unchanged UUID retrieval."""

import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app
from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork
from tests.integration.test_t15_planning_postgres import configured as _configured
from tests.integration.test_t15_planning_postgres import create
from tests.legacy_cases import create_legacy_case
from tests.t15_helpers import controlled_assets
from tests.test_odoo_purchase_history import headers
from tests.test_odoo_purchase_history import history as _history

configured, history = _configured, _history
pytestmark = pytest.mark.integration
BASE = "/api/v2/procurement/planning-cases"


def test_origin_filter_reads_stored_snapshots_for_bases_and_scenarios(
    configured, monkeypatch, tmp_path
):
    _, factory, payload, _ = configured
    legacy_payload = controlled_assets(tmp_path / "model")
    legacy = create_legacy_case(
        SqlAlchemyPlanningUnitOfWork(factory), legacy_payload, tmp_path / "model"
    )
    with TestClient(app) as client:
        base = create(client, payload)
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
        assert base["origin"] == child["origin"] == "odoo"
        for company, origin, expected in (
            (payload["terms"]["company_id"], "odoo", base["case_id"]),
            (legacy_payload["company_id"], "demo", legacy["case_id"]),
        ):
            monkeypatch.setattr(settings, "planning_library_company_id", company)
            for selected in ("all", origin):
                page = client.get(BASE, params={"origin": selected}, headers=headers())
                assert page.status_code == 200, page.text
                assert [item["case_id"] for item in page.json()["items"]] == [expected]
                assert all(item["origin"] == origin for item in page.json()["items"])
            other = "demo" if origin == "odoo" else "odoo"
            assert not client.get(BASE, params={"origin": other}, headers=headers()).json()["items"]
        monkeypatch.setattr(settings, "planning_library_company_id", payload["terms"]["company_id"])
        children = client.get(
            f"{BASE}/{base['case_id']}/scenarios", params={"origin": "odoo"}, headers=headers()
        ).json()
        assert [item["case_id"] for item in children["items"]] == [child["case_id"]]
        assert (
            client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["snapshot_hash"]
            == base["snapshot_hash"]
        )
