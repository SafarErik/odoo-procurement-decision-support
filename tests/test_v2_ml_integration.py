"""Explicit score injection without historical KPI reinterpretation."""

from decimal import Decimal

import pytest

pytest.importorskip("pulp")

from tools.v2_optimization.models import (  # noqa: E402
    ProcurementOptimizationInput,
    Status,
    Supplier,
    SupplierRiskScore,
)
from tools.v2_optimization.solver import optimize  # noqa: E402


def data():
    return ProcurementOptimizationInput(
        100,
        (
            Supplier("A", Decimal("10"), 60),
            Supplier("B", Decimal("10.5"), 80),
            Supplier("C", Decimal("11"), 100),
        ),
        2,
        Decimal("0.8"),
    )


def test_explicit_score_changes_allocation_without_fabricated_history():
    scores = tuple(
        SupplierRiskScore(identity, score)
        for identity, score in (("A", Decimal("0.8")), ("B", Decimal("0.3")), ("C", Decimal("0.1")))
    )
    minimum = optimize(data(), risk_scores=scores)
    constrained = optimize(data(), risk_scores=scores, epsilon=Decimal("0.05"))
    assert minimum.status == constrained.status == Status.OPTIMAL
    assert minimum.plan.total_cost == Decimal("1020")
    assert constrained.plan.total_cost <= minimum.plan.total_cost * Decimal("1.05")
    assert constrained.plan.risk_proxy < minimum.plan.risk_proxy
    assert constrained.plan.risk_basis == "supplied_score"
    assert optimize(data(), epsilon=Decimal("0.05")).status == Status.HISTORY_UNAVAILABLE
    assert optimize(data()).plan.risk_proxy is None
    assert optimize(data(), risk_scores=tuple(reversed(scores))) == minimum


@pytest.mark.parametrize(
    "scores",
    [
        (),
        (SupplierRiskScore("A", Decimal("0.1")),) * 3,
        (SupplierRiskScore("unknown", Decimal("0.1")),),
    ],
)
def test_missing_duplicate_unknown_external_scores_are_rejected(scores):
    with pytest.raises(ValueError, match="exactly one"):
        optimize(data(), risk_scores=scores)


@pytest.mark.parametrize(
    "score", [Decimal("NaN"), Decimal("-0.1"), Decimal("1.1"), Decimal("0.12345"), 0.2]
)
def test_external_risk_precision_and_range_fail_closed(score):
    with pytest.raises(ValueError):
        SupplierRiskScore("A", score)


def test_actual_tree_scores_flow_through_experimental_bridge():
    pytest.importorskip("sklearn")
    from tools.v2_ml_risk.experiments import run

    result = run()
    assert result["ml_to_milp"]["allocation_changed"]
    assert result["ml_to_milp"]["risk_aware"]["risk_basis"] == "supplied_score"
    assert all(
        a["model_version"] == result["model_version"] for a in result["integration_assessments"]
    )
