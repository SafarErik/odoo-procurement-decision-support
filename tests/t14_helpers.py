"""Shared controlled training and planning fixtures; no live services."""

from datetime import timedelta
from decimal import Decimal

from decision_core.planning.models import (
    MinimumOrder,
    PlanningPolicy,
    PlanningRequest,
    ProcurementRequirement,
    QuantityRange,
    SupplierTerms,
)
from supplier_evaluation.contracts import QuantityValidity


def planning_fixture(model, split):
    scores = tuple(
        model.infer(e.snapshot, QuantityValidity(1, 100, "controlled-fixture-v1"))
        for e in split.test[:3]
    )
    context = scores[0].snapshot.context
    cutoff = scores[0].snapshot.cutoff
    deadline = (cutoff + timedelta(days=7)).date()
    request = PlanningRequest(
        ProcurementRequirement(context.product_id, 10, context.quantity_unit, "EUR", deadline),
        tuple(
            SupplierTerms(
                a.snapshot.context.supplier_id,
                context.product_id,
                context.quantity_unit,
                "EUR",
                Decimal(2 + i),
                10,
                True,
                MinimumOrder(None),
                QuantityRange(1, 100),
                QuantityRange(1, 100),
                deadline,
            )
            for i, a in enumerate(scores)
        ),
        PlanningPolicy(2, Decimal("0.8"), (Decimal("0.1"),)),
        None,
    )
    return request, scores, context.company_id, cutoff
