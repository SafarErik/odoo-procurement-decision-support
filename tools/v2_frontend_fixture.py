"""Offline generation of deterministic UI fixtures; never imported by the frontend."""

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from tools.v2_optimization.models import (
    ProcurementOptimizationInput,
    Status,
    Supplier,
    SupplierRiskScore,
)
from tools.v2_optimization.solver import optimize

ROOT = Path(__file__).resolve().parents[1]
NAMES = {"A": "Northline Components", "B": "Danube Supply", "C": "Pannon Industrial"}
COLORS = {"A": "#397BA6", "B": "#0B7773", "C": "#AF782B"}
POLICIES = (
    ("minimum", "Minimum Cost", None),
    ("balanced", "Balanced", Decimal("0.02")),
    ("lower", "Lower-Risk Alternative", Decimal("0.05")),
)


def build() -> dict:
    ml = json.loads((ROOT / "docs/spikes/v2-ml-supplier-risk-results.json").read_text())
    assessments = dict(zip(NAMES, ml["integration_assessments"], strict=True))
    scores = tuple(
        SupplierRiskScore(i, Decimal(a["ml_risk_score"])) for i, a in assessments.items()
    )
    base = ProcurementOptimizationInput(
        100,
        (
            Supplier("A", Decimal("10"), 60),
            Supplier("B", Decimal("10.5"), 80),
            Supplier("C", Decimal("11"), 100),
        ),
        2,
        Decimal("0.8"),
    )

    def plans(data):
        result = []
        minimum = optimize(data, risk_scores=scores)
        if minimum.status is not Status.OPTIMAL:
            assert minimum.plan is None
            return [], [str(reason.detail) for reason in minimum.reasons]
        for identity, title, epsilon in POLICIES:
            solved = (
                minimum if epsilon is None else optimize(data, risk_scores=scores, epsilon=epsilon)
            )
            assert solved.status is Status.OPTIMAL and solved.plan is not None
            plan = solved.plan
            result.append(
                {
                    "plan_id": identity,
                    "title": title,
                    "feasible": True,
                    "quantity": plan.total_quantity,
                    "total_cost": str(plan.total_cost),
                    "cost_premium": str(plan.cost_premium or Decimal(0)),
                    "risk_exposure": str(plan.risk_proxy),
                    "largest_share": str(plan.concentration),
                    "supplier_count": plan.selected_supplier_count,
                    "allocations": [
                        {
                            "supplier_id": i,
                            "name": NAMES[i],
                            "quantity": q,
                            "share": float(Decimal(q) / data.required_quantity * 100),
                            "color": COLORS[i],
                        }
                        for i, q in plan.allocations
                    ],
                    "explanations": [
                        f"{NAMES[r.supplier_id]} reaches its stated capacity."
                        if r.code == "capacity_binding"
                        else (
                            f"{NAMES[r.supplier_id]} receives no quantity "
                            "in this objective solution."
                        )
                        if r.code == "zero_in_optimal_plan"
                        else (
                            f"Cost is €{plan.total_cost - minimum.plan.total_cost:.2f} higher "
                            f"({plan.cost_premium:.2%}) than the minimum-cost plan."
                        )
                        if r.code == "cost_premium"
                        else r.detail
                        for r in plan.explanations
                    ]
                    + [
                        "Model-derived score exposure is a planning proxy, "
                        "not a delivery probability.",
                        "Baltic Parts is contextual only: no delivery commitment was admitted.",
                    ],
                }
            )
        return result, []

    original, _ = plans(base)
    scenarios = {
        "baseline": {
            "label": "Original case",
            "quantity": 100,
            "plans": original,
            "reasons": [],
            "deltas": [],
        }
    }
    for operation in ("outage", "capacity", "demand", "price", "shortfall"):
        for identity in NAMES:
            data = base
            if operation == "demand":
                data = replace(base, required_quantity=120)
            elif operation == "shortfall":
                data = replace(
                    base, suppliers=tuple(replace(s, capacity=10) for s in base.suppliers)
                )
            else:
                data = replace(
                    base,
                    suppliers=tuple(
                        replace(
                            s,
                            **(
                                {"available": False}
                                if operation == "outage"
                                else {"capacity": 30}
                                if operation == "capacity"
                                else {"unit_cost": s.unit_cost * Decimal("1.2")}
                            ),
                        )
                        if s.supplier_id == identity
                        else s
                        for s in base.suppliers
                    ),
                )
            output, reasons = plans(data)
            labels = {
                "outage": f"{NAMES[identity]} unavailable",
                "capacity": f"{NAMES[identity]} capacity reduced to 30",
                "demand": "Demand increased to 120",
                "price": f"{NAMES[identity]} price increased by 20%",
                "shortfall": "All supplier capacities reduced to 10",
            }
            deltas = []
            for plan, before in zip(output, original, strict=bool(output)):
                deltas.append(
                    {
                        "plan_id": plan["plan_id"],
                        "cost_change": str(
                            Decimal(plan["total_cost"]) - Decimal(before["total_cost"])
                        ),
                        "risk_change": str(
                            Decimal(plan["risk_exposure"]) - Decimal(before["risk_exposure"])
                        ),
                        "allocation_change": "; ".join(
                            f"{current['supplier_id']}: "
                            f"{previous['quantity']} → {current['quantity']}"
                            for current, previous in zip(
                                plan["allocations"], before["allocations"], strict=True
                            )
                        ),
                        "feasibility_change": "No: feasible in both cases",
                    }
                )
            scenarios[f"{operation}_{identity}"] = {
                "label": labels[operation],
                "quantity": data.required_quantity,
                "plans": output,
                "reasons": reasons,
                "deltas": deltas,
            }
    suppliers = []
    for supplier in base.suppliers:
        a = assessments[supplier.supplier_id]
        explanation = a["explanation"]
        features = explanation["features"]
        suppliers.append(
            {
                "supplier_id": supplier.supplier_id,
                "name": NAMES[supplier.supplier_id],
                "unit_price": str(supplier.unit_cost),
                "capacity": supplier.capacity,
                "minimum_quantity": 0,
                "commitment": "Eligible · illustrative commitment",
                "historical_indicator": f"{features['historical_adherence_before_decision']:.1%} / "
                f"{int(features['historical_completed_count'])} prior lines",
                "risk_score": a["ml_risk_score"],
                "predicted_class": "Schedule miss" if a["predicted_class"] else "On schedule",
                "source_status": "Synthetic terms / ML experiment",
                "color": COLORS[supplier.supplier_id],
                "explanation": [
                    f"{r['feature']} {r['operator']} {r['threshold']:.6g} "
                    f"(input {r['value_float32']:.6g})"
                    for r in explanation["rules_traversed"]
                ]
                + [
                    f"Leaf support: {explanation['leaf_sample_count']}; classes [on-time, miss] "
                    f"{explanation['leaf_class_counts_0_1']}",
                    f"Model: {a['model_version'][:12]} · synthetic context, quantity 100",
                    "Score is an uncalibrated leaf proportion; "
                    "predictive value is not established.",
                ],
            }
        )
    suppliers.append(
        {
            "supplier_id": "D",
            "name": "Baltic Parts",
            "unit_price": "9",
            "capacity": 100,
            "minimum_quantity": 20,
            "commitment": "Not admitted · commitment unavailable",
            "historical_indicator": "Unavailable",
            "risk_score": None,
            "predicted_class": "Withheld",
            "source_status": "Incomplete contextual offer",
            "color": "#6C7C88",
            "explanation": [
                "No accepted delivery commitment or usable risk assessment.",
                "Not in the admitted three-supplier optimizer input.",
            ],
        }
    )
    return {
        "fixture_version": "v2-cockpit-v1",
        "evidence_kind": "deterministic-synthetic",
        "case": {
            "case_id": "V2-DEMO-001",
            "version": "case-v1",
            "product": "DC-100 drive coupling",
            "quantity": 100,
            "uom": "Units",
            "currency": "EUR",
            "required_date": "21 Oct 2026",
            "max_suppliers": 2,
            "concentration_limit": "0.8",
            "allowed_premium": "0.05",
        },
        "suppliers": suppliers,
        "scenarios": scenarios,
        "limits": [
            "No live Odoo data or business actions",
            "Risk scores fixed at comparison quantity",
            "Scenario choices are bounded fixtures, not runtime optimization",
        ],
    }


if __name__ == "__main__":
    destination = ROOT / "docs/spikes/v2-reflex-frontend-fixture.json"
    destination.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {destination.name}")
