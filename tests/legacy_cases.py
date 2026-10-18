"""Pre-P2 synthetic demo cases, recreated only to test that stored cases stay usable.

P2 removed the synthetic demo creation routes and the V1 tree from the runtime. Saved
demo cases remain readable, approvable and printable, so tests rebuild such cases
through the application use case with the original synthetic V1 model.
"""

import hashlib
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from application.planning_cases import create_planning_case
from application.planning_input import PlanningFacts, SupplierFacts
from application.provenance import SourceAttribution
from backend.app.dependencies import planning_solver_factory
from decision_core.planning.models import (
    MinimumOrder,
    PlanningPolicy,
    ProcurementRequirement,
    QuantityRange,
    SupplierTerms,
)
from supplier_evaluation.artifacts import load_model, save_model
from supplier_evaluation.contracts import SYNTHETIC, Context, LineEvidence, QuantityValidity
from supplier_evaluation.dataset import (
    BOUNDARY,
    EXTRACTED_AT,
    generate_dataset,
    prepare_dataset,
    save_dataset,
)
from supplier_evaluation.model import train

__all__ = ["create_legacy_case", "legacy_facts", "prepare_assets"]


def prepare_assets(directory, *, domain=None, supplier_count=3):
    if supplier_count not in (3, 5, 10):
        raise ValueError("Controlled workloads support 3, 5 or 10 suppliers.")
    rows = generate_dataset() if domain is None else generate_dataset(domain=domain)
    split = prepare_dataset(rows, boundary=BOUNDARY, extracted_at=EXTRACTED_AT)
    model = train(split)
    save_model(model, directory)
    save_dataset(directory / "dataset.json", rows)
    assessments = sorted(
        (
            model.infer(e.snapshot, QuantityValidity(1, 1000, "controlled-proxy-v1"))
            for e in split.test
        ),
        key=lambda a: (a.score, a.snapshot.context.supplier_id),
    )
    chosen = (assessments[-1], assessments[len(assessments) // 2], assessments[0])
    chosen += tuple(a for a in assessments if a not in chosen)[: supplier_count - 3]
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
    prices = ("10", "10.5", "11") + tuple(
        str(Decimal("11.5") + Decimal("0.5") * i) for i in range(supplier_count - 3)
    )
    capacities = (6, 8, 10) + (10,) * (supplier_count - 3)
    for a, price, capacity in zip(chosen, prices, capacities, strict=True):
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


def _source(value, field):
    return SourceAttribution(
        field,
        value["source_type"],
        value["source_reference"],
        datetime.fromisoformat(value["observed_at"]),
    )


def legacy_facts(payload) -> PlanningFacts:
    """The pre-P2 synthetic request contract, as the removed HTTP schema mapped it."""
    r, p = payload["requirement"], payload["policy"]
    suppliers = []
    for s in payload["suppliers"]:
        context = Context(
            s["supplier_id"], payload["company_id"], r["product_id"], r["quantity_unit"]
        )
        terms = SupplierTerms(
            s["supplier_id"],
            r["product_id"],
            r["quantity_unit"],
            r["currency"],
            Decimal(s["unit_price"]),
            s["capacity"],
            s["available"],
            MinimumOrder(s["minimum_order_quantity"]),
            QuantityRange(s["price_quantities"]["minimum"], s["price_quantities"]["maximum"]),
            QuantityRange(s["delivery_quantities"]["minimum"], s["delivery_quantities"]["maximum"]),
            date.fromisoformat(s["promised_date"]),
        )
        receipts = tuple(
            LineEvidence(
                line["line_id"],
                context,
                datetime.fromisoformat(line["expected_arrival"]),
                datetime.fromisoformat(line["completed_at"]),
                datetime.fromisoformat(line["available_at"]),
            )
            for line in s["receipts"]
        )
        validity = s["score_quantities"]
        suppliers.append(
            SupplierFacts(
                s["offer_id"],
                terms,
                _source(s["source"], "commercial_terms"),
                receipts,
                s["history_reference"],
                QuantityValidity(validity["minimum"], validity["maximum"], validity["reference"]),
            )
        )
    return PlanningFacts(
        payload["company_id"],
        datetime.fromisoformat(payload["as_of"]),
        ProcurementRequirement(
            r["product_id"],
            r["approved_quantity"],
            r["quantity_unit"],
            r["currency"],
            date.fromisoformat(r["required_date"]),
        ),
        payload["approval_reference"],
        _source(payload["requirement_source"], "requirement"),
        PlanningPolicy(
            p["max_suppliers"],
            None if p["concentration_limit"] is None else Decimal(p["concentration_limit"]),
            tuple(Decimal(e) for e in p["epsilons"]),
        ),
        _source(payload["policy_source"], "policy"),
        tuple(suppliers),
        SYNTHETIC,
    )


def legacy_infer(directory):
    """The removed V1 composition: trusted local artifact, manifest and checksum."""

    def infer(features):
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        model = load_model(directory, trusted_local=True)
        assert (
            manifest["artifact_sha256"]
            == hashlib.sha256((directory / "tree.joblib").read_bytes()).hexdigest()
        )
        return tuple(
            model.infer(snapshot, quantities) for snapshot, quantities in features
        ), manifest

    return infer


def create_legacy_case(uow, payload, directory, key=None):
    """Store one pre-P2 synthetic demo base case; returns the API-shaped response."""
    case, _ = create_planning_case(
        uow,
        key or str(uuid4()),
        facts=legacy_facts(payload),
        infer=legacy_infer(directory),
        solver_factory=planning_solver_factory,
    )
    return {
        "case_id": case.case_id,
        "created_at": case.created_at,
        "parent_id": None,
        "snapshot_hash": case.snapshot_hash,
        "snapshot": json.loads(case.snapshot),
    }
