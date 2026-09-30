"""Experimental application bridge: only supplier IDs and canonical scores enter MILP."""

from dataclasses import asdict
from decimal import Decimal

from tools.v2_ml_risk.model import SupplierRiskAssessment
from tools.v2_optimization.models import (
    ProcurementOptimizationInput,
    Status,
    Supplier,
    SupplierRiskScore,
)
from tools.v2_optimization.solver import optimize


def allocation_proof(assessments: tuple[SupplierRiskAssessment, ...]) -> dict:
    if len(assessments) != 3:
        raise ValueError("The demonstration requires exactly three assessments.")
    data = ProcurementOptimizationInput(
        100,
        tuple(
            Supplier(a.supplier_id, cost, capacity)
            for a, cost, capacity in zip(
                assessments,
                (Decimal("10"), Decimal("10.5"), Decimal("11")),
                (60, 80, 100),
                strict=True,
            )
        ),
        2,
        Decimal("0.8"),
    )
    scores = tuple(SupplierRiskScore(a.supplier_id, a.ml_risk_score) for a in assessments)
    minimum = optimize(data, risk_scores=scores)
    risk_aware = optimize(data, epsilon=Decimal("0.05"), risk_scores=scores)
    if minimum.status is not Status.OPTIMAL or risk_aware.status is not Status.OPTIMAL:
        raise ValueError("Demonstration requires proven optimal experimental plans.")
    assert minimum.plan is not None and risk_aware.plan is not None
    return {
        "scores": [asdict(s) for s in scores],
        "input": asdict(data),
        "epsilon": "0.05",
        "minimum_cost": asdict(minimum.plan),
        "risk_aware": asdict(risk_aware.plan),
        "allocation_changed": minimum.plan.allocations != risk_aware.plan.allocations,
        "exposure_definition": "sum(quantity_i * canonical_ML_score_i) / required_quantity",
        "interpretation": "Illustrative score exposure, not probability or expected loss.",
    }
