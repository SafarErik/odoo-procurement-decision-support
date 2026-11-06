"""Transactional fast-test repository and shared Odoo-history case helpers."""

import json
from contextlib import contextmanager
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

BASE = "/api/v2/procurement/planning-cases"
# Controlled workload over the fake Odoo quotation group 501 (prices 9 / 12 / 10 come from
# Odoo): demand 10, at most two suppliers, 80 % concentration, one 10 % risk allowance.
# Supplier 306 is the cheapest and (with 304) the riskiest, so cost and risk disagree.
CAPACITIES = {"odoo:res.partner:306": 6, "odoo:res.partner:304": 8, "odoo:res.partner:301": 10}


def copy_payload(payload):
    return json.loads(json.dumps(payload))


@contextmanager
def odoo_case_api(history, uow, monkeypatch):
    """HTTP client over a fake read-only Odoo, the trained history model and ``uow``.

    Case creation reads the clock at ``history["now"]``, the end of the generated history.
    """
    from backend.app.main import app
    from tests.test_odoo_purchase_history import install_fake_odoo

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
    with TestClient(app, headers={"Authorization": "Bearer history-test-token"}) as client:
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
        headers={"Idempotency-Key": key or str(uuid4())},
    )
    assert response.status_code == 201, response.text
    return response.json()


class MemoryPlanningUnitOfWork:
    """Snapshot row/key rollback, matching the single-row durable mapping contract."""

    def __init__(self):
        self.rows = {}
        self.catalog = {}
        self.cases = self
        self.decisions = MemoryPlanningDecisions()
        self.documents = MemoryPlanningDocuments()

    def __enter__(self):
        self.before = self.rows.copy()
        self.before_catalog = self.catalog.copy()
        self.before_decisions = self.decisions.rows.copy()
        self.before_documents = self.documents.rows.copy()
        self.committed = False
        return self

    def __exit__(self, *args):
        if not self.committed:
            self.rows = self.before
            self.catalog = self.before_catalog
            self.decisions.rows = self.before_decisions
            self.documents.rows = self.before_documents

    def commit(self):
        self.committed = True

    def lock(self, key):
        pass

    def get(self, case_id):
        return self.rows.get(case_id)

    def by_key(self, key):
        return next((case for case in self.rows.values() if case.idempotency_key == key), None)

    def add(self, case):
        assert self.by_key(case.idempotency_key) is None
        self.rows[case.case_id] = case

    def add_catalog(self, case_id, context):
        assert case_id not in self.catalog and self.rows[case_id].parent_id is None
        self.catalog[case_id] = context

    def catalog_for(self, case_id):
        return self.catalog.get(case_id)


class MemoryPlanningDecisions:
    def __init__(self):
        self.rows = {}

    def lock(self, key):
        pass

    def get(self, case_id):
        return self.rows.get(case_id)

    def by_key(self, key):
        return next((d for d in self.rows.values() if d.idempotency_key == key), None)

    def add(self, decision):
        assert decision.case_id not in self.rows and self.by_key(decision.idempotency_key) is None
        self.rows[decision.case_id] = decision


class MemoryPlanningDocuments:
    def __init__(self):
        self.rows = {}

    def lock(self, case_id):
        pass

    def get(self, case_id, language, kind):
        return self.rows.get((case_id, language, kind))

    def add(self, document):
        key = (document.case_id, document.language, document.kind)
        assert key not in self.rows
        self.rows[key] = document
