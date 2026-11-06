"""Planning HTTP API helpers: auth headers, Odoo-history case creation, decision intents."""

from contextlib import contextmanager
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from tests.helpers.odoo_fakes import install_fake_odoo

BASE = "/api/v2/procurement/planning-cases"
# The service token every fake API in the fast and integration tests is configured with.
TOKEN = "history-test-token"
# Controlled workload over the fake Odoo quotation group 501 (prices 9 / 12 / 10 come from
# Odoo): demand 10, at most two suppliers, 80 % concentration, one 10 % risk allowance.
# Supplier 306 is the cheapest and (with 304) the riskiest, so cost and risk disagree.
CAPACITIES = {"odoo:res.partner:306": 6, "odoo:res.partner:304": 8, "odoo:res.partner:301": 10}


def headers(key=None):
    return {"Authorization": f"Bearer {TOKEN}", "Idempotency-Key": key or str(uuid4())}


def forbidden(*args, **kwargs):
    """Patched over Odoo reads, scoring and solving where a stored-only path must not reach."""
    raise AssertionError("Stored or replayed operation re-read Odoo, scored or solved")


@contextmanager
def odoo_case_api(history, uow, monkeypatch):
    """HTTP client over a fake read-only Odoo, the trained history model and ``uow``.

    Case creation reads the clock at ``history["now"]``, the end of the generated history.
    """

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return history["now"]

    for module in (
        "application.odoo_planning_input",
        "backend.app.dependencies",
        "odoo_adapter.comparison_case_reader",
        "odoo_adapter.product_history_reader",
    ):
        monkeypatch.setattr(f"{module}.datetime", Clock)
    install_fake_odoo(history, monkeypatch)
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    with TestClient(app, headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client


def controlled_terms(client):
    """The preview's buyer terms for group 501, reshaped into the controlled workload."""
    preview = client.get(f"{BASE}/odoo-history/preview?purchase_group_id=501")
    assert preview.status_code == 200, preview.text
    terms = preview.json()["terms"]
    terms["requirement"]["approved_quantity"] = 10
    terms["policy"] = {"max_suppliers": 2, "concentration_limit": "0.8", "epsilons": ["0.1"]}
    suppliers = {s["supplier_id"]: s for s in terms["suppliers"]}
    terms["suppliers"] = [
        suppliers[identity] | {"capacity": capacity} for identity, capacity in CAPACITIES.items()
    ]
    return terms


def create_case(client, terms, key=None):
    """Save one Odoo-history base case through the HTTP route; returns the response body."""
    response = client.post(
        f"{BASE}/from-odoo-history",
        json={"purchase_group_id": 501, "terms": terms},
        headers=headers(key),
    )
    assert response.status_code == 201, response.text
    return response.json()


def intent(case, index=0, outcome="approve"):
    """A final-decision request body for ``case``'s plan ``index``."""
    return {
        "snapshot_hash": case["snapshot_hash"],
        "outcome": outcome,
        "plan_index": index,
        "actor_reference": "  buyer audit reference  ",
        "rationale": "  prefer lower exposure  " if index != 0 else None,
        "demonstration_acknowledged": True,
    }


def approve(client, base, index=1):
    """Approve plan ``index`` of ``base``; returns the decision and its plan-PDF URL."""
    response = client.post(
        f"{BASE}/{base['case_id']}/final-decision", json=intent(base, index), headers=headers()
    )
    assert response.status_code == 201, response.text
    decision = response.json()["final_decision"]
    return decision, f"{BASE}/{base['case_id']}/approved-pdf/{decision['approved_content_hash']}"
