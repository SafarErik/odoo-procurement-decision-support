"""Reproducible synthetic experiments; run from the repository, no services needed."""

import json
import platform
import subprocess
from dataclasses import asdict, replace
from decimal import Decimal
from statistics import median
from time import perf_counter
from unittest.mock import patch

import pulp

from tools.v2_optimization import solver as optimization_solver
from tools.v2_optimization.models import (
    PriceTier,
    ProcurementOptimizationInput,
    Supplier,
)
from tools.v2_optimization.solver import optimize


def baseline() -> ProcurementOptimizationInput:
    return ProcurementOptimizationInput(
        required_quantity=100,
        suppliers=(
            Supplier("A", Decimal("10"), 60, historical_adherence=Decimal("0.60"), sample_size=20),
            Supplier(
                "B", Decimal("10.50"), 80, historical_adherence=Decimal("0.95"), sample_size=20
            ),
            Supplier("C", Decimal("11"), 100, historical_adherence=Decimal("0.99"), sample_size=20),
        ),
        max_suppliers=2,
        concentration_limit=Decimal("0.80"),
    )


def experiments() -> dict:
    data = baseline()
    original = optimize(data)
    assert original.plan is not None
    plans = {str(e): optimize(data, epsilon=e) for e in map(Decimal, ("0", "0.02", "0.05", "0.10"))}
    suppliers = data.suppliers
    scenarios = {
        "supplier_A_unavailable": replace(
            data, suppliers=(replace(suppliers[0], available=False), *suppliers[1:])
        ),
        "supplier_A_capacity_30": replace(
            data, suppliers=(replace(suppliers[0], capacity=30), *suppliers[1:])
        ),
        "demand_120": replace(data, required_quantity=120),
        "supplier_A_price_11_50": replace(
            data, suppliers=(replace(suppliers[0], unit_cost=Decimal("11.50")), *suppliers[1:])
        ),
    }
    comparisons = {}
    for name, case in scenarios.items():
        result = optimize(case)
        plan = result.plan
        comparisons[name] = {
            "result": asdict(result),
            "feasibility_changed": result.status != original.status,
            "cost_difference": plan.total_cost - original.plan.total_cost if plan else None,
            "allocation_difference": {
                supplier_id: quantity - dict(original.plan.allocations)[supplier_id]
                for supplier_id, quantity in plan.allocations
            }
            if plan
            else None,
            "risk_proxy_difference": plan.risk_proxy - original.plan.risk_proxy
            if plan and plan.risk_proxy is not None and original.plan.risk_proxy is not None
            else None,
        }
    tier_supplier = Supplier(
        "A",
        Decimal("1000"),
        1000,
        price_tiers=(PriceTier(1, Decimal("1000")), PriceTier(500, Decimal("920"))),
    )
    tiers = {
        str(demand): asdict(
            optimize(
                ProcurementOptimizationInput(
                    demand, (tier_supplier, Supplier("B", Decimal("950"), 1000)), 1
                )
            )
        )
        for demand in (499, 500, 600)
    }
    performance = []
    for count in (3, 10, 25, 50):
        case = ProcurementOptimizationInput(
            1000,
            tuple(
                Supplier(
                    f"S{i:02}", Decimal("10") + Decimal("0.17") * i, (1500 + count - 1) // count
                )
                for i in range(count)
            ),
            count,
        )
        elapsed = []
        baseline_phase_ms = []
        allocations = []
        for _ in range(3):
            phase_times = []
            run_phase = optimization_solver._run

            def measured_phase(problem, solver):
                phase_start = perf_counter()
                status = run_phase(problem, solver)
                phase_times.append((perf_counter() - phase_start) * 1000)
                return status

            with patch.object(optimization_solver, "_run", measured_phase):
                start = perf_counter()
                result = optimize(case)
                elapsed.append((perf_counter() - start) * 1000)
            baseline_phase_ms.append(phase_times[0])
            assert result.plan is not None, result
            allocations.append(result.plan.allocations)
        assert allocations[0] == allocations[1] == allocations[2]
        performance.append(
            {
                "supplier_count": count,
                "solve_ms": elapsed,
                "median_ms": median(elapsed),
                "minimum_cost_phase_ms": baseline_phase_ms,
                "minimum_cost_phase_median_ms": median(baseline_phase_ms),
                "identical_allocations": True,
                "total_cost": result.plan.total_cost,
                "solve_phases": count + 1,
            }
        )
    cbc_version_output = subprocess.run(
        [pulp.PULP_CBC_CMD().path, "-stop"], check=True, capture_output=True, text=True
    ).stdout
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "pulp": pulp.__version__,
        "cbc_version": next(
            line for line in cbc_version_output.splitlines() if line.startswith("Version:")
        ),
        "solver_settings": {
            "threads": 1,
            "randomSeed": 1,
            "randomCbcSeed": 1,
            "gapRel": 0,
            "gapAbs": 0,
            "per_phase_seconds": 10,
        },
        "input": asdict(data),
        "minimum_cost": asdict(original),
        "epsilon_plans": {key: asdict(value) for key, value in plans.items()},
        "unique_epsilon_allocations": len(
            {value.plan.allocations for value in plans.values() if value.plan}
        ),
        "what_if": comparisons,
        "infeasible": asdict(optimize(replace(data, required_quantity=300))),
        "all_units_tiers": tiers,
        "performance": performance,
    }


if __name__ == "__main__":
    print(json.dumps(experiments(), indent=2, default=str))
