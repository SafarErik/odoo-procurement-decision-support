"""Controlled saved-model fixture and transactional fast-test repository."""

import json
from datetime import timedelta

from supplier_evaluation.artifacts import save_model
from supplier_evaluation.contracts import SYNTHETIC, QuantityValidity
from supplier_evaluation.dataset import BOUNDARY, EXTRACTED_AT, generate_dataset, prepare_dataset
from supplier_evaluation.model import train


def controlled_assets(directory):
    rows = generate_dataset()
    split = prepare_dataset(rows, boundary=BOUNDARY, extracted_at=EXTRACTED_AT)
    model = train(split)
    save_model(model, directory)
    assessments = sorted(
        (
            model.infer(e.snapshot, QuantityValidity(1, 1000, "controlled-proxy-v1"))
            for e in split.test
        ),
        key=lambda a: (a.score, a.snapshot.context.supplier_id),
    )
    chosen = (assessments[-1], assessments[len(assessments) // 2], assessments[0])
    context, cutoff = chosen[0].snapshot.context, chosen[0].snapshot.cutoff
    deadline = (cutoff + timedelta(days=7)).date().isoformat()
    source = {
        "source_type": "controlled_business_terms",
        "source_reference": "t15-demo-v1",
        "observed_at": cutoff.isoformat(),
    }
    payload = {
        "source_type": SYNTHETIC,
        "company_id": context.company_id,
        "as_of": cutoff.isoformat(),
        "approval_reference": "controlled-demand-10-v1",
        "requirement": {
            "product_id": context.product_id,
            "approved_quantity": 10,
            "quantity_unit": context.quantity_unit,
            "currency": "EUR",
            "required_date": deadline,
        },
        "requirement_source": source.copy(),
        "policy_source": source.copy(),
        "policy": {"max_suppliers": 2, "concentration_limit": "0.8", "epsilons": ["0.1"]},
        "suppliers": [],
    }
    by_context = {row.context: row for row in rows if row.cutoff == cutoff}
    for a, price, capacity in zip(chosen, ("10", "10.5", "11"), (6, 8, 10), strict=True):
        row = by_context[a.snapshot.context]
        payload["suppliers"].append(
            {
                "supplier_id": row.context.supplier_id,
                "offer_id": "offer:" + row.context.supplier_id,
                "unit_price": price,
                "capacity": capacity,
                "available": True,
                "minimum_order_quantity": None,
                "price_quantities": {"minimum": 1, "maximum": 1000},
                "delivery_quantities": {"minimum": 1, "maximum": 1000},
                "promised_date": deadline,
                "source": source.copy(),
                "history_reference": row.source_reference,
                "score_quantities": {
                    "minimum": 1,
                    "maximum": 1000,
                    "reference": "controlled-proxy-v1",
                },
                "receipts": [
                    {
                        "line_id": line.line_id,
                        "expected_arrival": line.expected_arrival.isoformat(),
                        "completed_at": line.completed_at.isoformat(),
                        "available_at": line.available_at.isoformat(),
                    }
                    for line in row.history
                ],
            }
        )
    return payload


def copy_payload(payload):
    return json.loads(json.dumps(payload))


class MemoryPlanningUnitOfWork:
    """Snapshot row/key rollback, matching the single-row durable mapping contract."""

    def __init__(self):
        self.rows = {}
        self.cases = self

    def __enter__(self):
        self.before = self.rows.copy()
        self.committed = False
        return self

    def __exit__(self, *args):
        if not self.committed:
            self.rows = self.before

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
