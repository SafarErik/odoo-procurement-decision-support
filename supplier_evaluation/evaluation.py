"""Held-out metrics and an actual in-process three-supplier T13 solver demonstration."""

from dataclasses import asdict, replace
from datetime import timedelta
from decimal import Decimal

from sklearn.metrics import accuracy_score, confusion_matrix

from application.procurement_planning import PlanningCommand, create_procurement_plans
from decision_core.planning.models import (
    MinimumOrder,
    PlanningPolicy,
    PlanningRequest,
    PlanningStatus,
    ProcurementRequirement,
    QuantityRange,
    SupplierTerms,
)
from optimization_adapter.pulp_cbc import PulpCbcSolver
from supplier_evaluation.contracts import SEED, QuantityValidity, digest
from supplier_evaluation.dataset import Split, split_details
from supplier_evaluation.model import TreeModel
from supplier_evaluation.planning_bridge import risk_inputs


def classification_metrics(labels: list[int], predictions: list[int]) -> dict:
    if (
        not labels
        or len(labels) != len(predictions)
        or any(type(v) is not int or v not in (0, 1) for v in labels + predictions)
    ):
        raise ValueError("Nonempty binary classification results required.")
    matrix = confusion_matrix(labels, predictions, labels=[0, 1]).tolist()
    classes, undefined = [], []
    for k in (0, 1):
        tp = matrix[k][k]
        support = sum(matrix[k])
        predicted = sum(row[k] for row in matrix)
        precision = tp / predicted if predicted else None
        recall = tp / support if support else None
        f1 = 2 * tp / (support + predicted) if support + predicted else None
        if precision is None:
            undefined.append(f"class {k} precision undefined: no predicted positives")
        if recall is None:
            undefined.append(f"class {k} recall undefined: absent held-out class")
        if f1 is None:
            undefined.append(f"class {k} F1 undefined: absent true and predicted class")
        classes.append(
            {
                "class": k,
                "support": support,
                "predicted_support": predicted,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )
    macro = {
        metric: (
            sum(c[metric] for c in classes) / 2
            if all(c[metric] is not None for c in classes)
            else None
        )
        for metric in ("precision", "recall", "f1")
    }
    return {
        "confusion_matrix_labels_0_1": matrix,
        "accuracy": float(accuracy_score(labels, predictions)),
        "per_class": classes,
        "macro": macro,
        "undefined_metrics": undefined,
    }


def evaluate(model: TreeModel, split: Split) -> dict:
    model.validate()
    if model.metadata["training_id"] != digest(
        [asdict(e) for e in sorted(split.train, key=lambda e: e.observation_id)]
    ):
        raise ValueError("Evaluation split does not match this model's training data.")
    assessments = tuple(
        model.infer(e.snapshot, QuantityValidity(1, 1000, "controlled-proxy-v1"))
        for e in split.test
    )
    return {
        "split": split_details(split),
        "seed": SEED,
        "model": model.metadata,
        "metrics": classification_metrics(
            [e.label for e in split.test], [a.predicted_class for a in assessments]
        ),
        "heldout_assessment_hash": digest([a.reference for a in assessments]),
        "tree": model.global_explanation(),
        "limitations": [
            "All receipts and labels are synthetic; no real Odoo training export was used.",
            "The model learns an intentionally constructed noisy labelling mechanism.",
            "Scores are uncalibrated supplier-context planning exposure proxies.",
            "Controlled quantity independence is not empirical delivery validity.",
            "No real-world predictive superiority or complete V2 workflow claim.",
        ],
    }


def demonstrate_planning(model: TreeModel, split: Split) -> dict:
    scored = [
        model.infer(e.snapshot, QuantityValidity(1, 1000, "controlled-proxy-v1"))
        for e in split.test
    ]
    scored.sort(key=lambda a: (a.score, a.snapshot.context.supplier_id))
    if scored[0].score == scored[-1].score:
        raise ValueError("Demonstration needs distinct valid scored suppliers.")
    chosen = (scored[-1], scored[len(scored) // 2], scored[0])
    domain = chosen[0].snapshot.context
    as_of = max(a.snapshot.cutoff for a in chosen)
    deadline = (as_of + timedelta(days=7)).date()
    terms = tuple(
        SupplierTerms(
            a.snapshot.context.supplier_id,
            domain.product_id,
            domain.quantity_unit,
            "EUR",
            price,
            capacity,
            True,
            MinimumOrder(None),
            QuantityRange(1, 1000),
            QuantityRange(1, 1000),
            deadline,
        )
        for a, price, capacity in zip(
            chosen, (Decimal("10"), Decimal("10.5"), Decimal("11")), (6, 8, 10), strict=True
        )
    )
    request = PlanningRequest(
        ProcurementRequirement(domain.product_id, 10, domain.quantity_unit, "EUR", deadline),
        terms,
        PlanningPolicy(2, Decimal("0.8"), (Decimal("0.1"),)),
        None,
    )
    coefficients, context = risk_inputs(request, chosen, company_id=domain.company_id, as_of=as_of)
    command = PlanningCommand(replace(request, risk_coefficients=coefficients), context)
    result = create_procurement_plans(command, PulpCbcSolver())
    if result.status is not PlanningStatus.OPTIMAL or result.minimum_cost_plan is None:
        raise ValueError(f"Actual CBC demonstration failed: {result.status}")

    def plan(p):
        return {
            "allocations": [asdict(a) for a in p.allocations],
            "total_cost": str(p.total_cost),
            "risk_exposure": str(p.risk_exposure),
            "cost_premium": str(p.cost_premium),
        }

    return {
        "status": result.status.value,
        "context": asdict(context),
        "supplier_scores": {a.snapshot.context.supplier_id: str(a.score) for a in chosen},
        "minimum_cost": plan(result.minimum_cost_plan),
        "alternatives": [plan(p) for p in result.alternatives],
        "quantity_validity": "explicit constant controlled proxy on [1,1000]",
        "demonstration_only": True,
    }
