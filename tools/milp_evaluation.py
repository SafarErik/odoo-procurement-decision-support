"""MILP/API evaluation on the Odoo-history path (P4).

    python -m tools.milp_evaluation [--repetitions 30] [--warmups 2]

Needs Odoo with the seeded ``pdss_history_gen`` database including the evaluation
groups (``python -m tools.seed_odoo_history groups``), the trained history model and the
disposable test planning database (``TEST_DATABASE_URL``, RUNBOOK §6). Measured cases
are written there, never into the development planning database. The tool starts its
own API on 127.0.0.1:8010 and never writes to Odoo or trains.

Two parts, written to ``docs/evidence/P4_MILP_EVALUATION.json``:

1. HTTP latency per workload (open group with 4/5/10 suppliers × 1/3 epsilons):
   create (Odoo read + inference + MILP + storage), scenario (MILP + storage), exact
   retry (stored replay) and GET; warm-up runs are excluded; median, nearest-rank p95
   and maximum of the measured runs.
2. Solver correctness and time in-process on each stored request: Σx = Q, bounds,
   supplier count, concentration, cost; the minimum-cost plan and every ε alternative
   equal an exhaustive reference optimum computed from the raw input; repeated and
   supplier-permuted solves are identical; infeasible variants are reported as such.

Local timings describe this machine only; they are not a service-level agreement.
"""

import argparse
import json
import math
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from application.planning_serialization import read_request
from decision_core.planning.models import MinimumOrder, PlanningStatus
from decision_core.planning.planner import plan_procurement
from optimization_adapter.pulp_cbc import PulpCbcSolver
from tools.demo import api, check_reproduction_window, git_revision
from tools.dev import ROOT, _env
from tools.t17_demo import BASE, checked, write_json

SIZES = (4, 5, 10)
EPSILONS = {1: ("0.2",), 3: ("0.05", "0.1", "0.2")}
GROUPS_FILE = ROOT / ".artifacts" / "seed" / "evaluation_groups.json"
LOOPBACK = {"localhost", "127.0.0.1", "::1"}


# --- Statistics ----------------------------------------------------------------------


def nearest_rank(values, quantile: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def describe(seconds) -> dict:
    return {
        "n": len(seconds),
        "median_ms": round(statistics.median(seconds) * 1000, 1),
        "p95_ms": round(nearest_rank(seconds, 0.95) * 1000, 1),
        "max_ms": round(max(seconds) * 1000, 1),
        "min_ms": round(min(seconds) * 1000, 1),
    }


# --- Exhaustive reference optimum (independent of the core bounds and solver) ---------


def _scale(values) -> tuple[list[int], int]:
    fractions = [Fraction(v) for v in values]
    unit = math.lcm(*(f.denominator for f in fractions))
    return [int(f * unit) for f in fractions], unit


def _ranges(request) -> list[tuple[int, int]]:
    """Positive-use range per supplier (sorted by id) straight from the input facts."""
    q = request.requirement.approved_quantity
    limit = request.policy.concentration_limit
    cap = q if limit is None else math.floor(Fraction(limit) * q)
    out = []
    for s in sorted(request.suppliers, key=lambda s: s.supplier_id):
        low = max(
            1,
            s.minimum_order.quantity or 1,
            s.price_quantities.minimum,
            s.delivery_quantities.minimum,
        )
        high = min(s.capacity, cap, s.price_quantities.maximum, s.delivery_quantities.maximum)
        if not s.available or s.promised_date > request.requirement.required_date:
            high = 0
        out.append((low, high) if low <= high else (1, 0))
    return out


def _vectors(request):
    """Every integer allocation that meets demand, the supplier count and all ranges."""
    q = request.requirement.approved_quantity
    ranges = _ranges(request)
    usable = [i for i, (low, high) in enumerate(ranges) if low <= high]
    for count in range(1, min(request.policy.max_suppliers, len(usable)) + 1):
        for chosen in combinations(usable, count):

            def fill(position, left, partial, chosen=chosen):
                index = chosen[position]
                low, high = ranges[index]
                if position == len(chosen) - 1:
                    if low <= left <= high:
                        yield (*partial, (index, left))
                    return
                rest_low = sum(ranges[i][0] for i in chosen[position + 1 :])
                rest_high = sum(ranges[i][1] for i in chosen[position + 1 :])
                for x in range(max(low, left - rest_high), min(high, left - rest_low) + 1):
                    yield from fill(position + 1, left - x, (*partial, (index, x)))

            for picked in fill(0, q, ()):
                vector = [0] * len(ranges)
                for index, x in picked:
                    vector[index] = x
                yield tuple(vector)


def reference_plans(request) -> dict:
    """Minimum cost, then per ε: minimum exposure within (1+ε)·C*, then cost, then the
    lexicographically largest quantities in supplier-id order (the documented tie-break).
    The balanced reference minimises the largest quantity within its allowance without
    exceeding the minimum plan's exposure, then exposure, cost and the same tie-break."""
    suppliers = sorted(request.suppliers, key=lambda s: s.supplier_id)
    prices, _ = _scale([s.unit_price for s in suppliers])
    scores = {c.supplier_id: c.value for c in request.risk_coefficients or ()}
    risks, _ = _scale([scores.get(s.supplier_id, Decimal(0)) for s in suppliers])

    def cost(v):
        return sum(p * x for p, x in zip(prices, v, strict=True))

    def risk(v):
        return sum(r * x for r, x in zip(risks, v, strict=True))

    # Streamed twice instead of stored: 10 suppliers with K = 3 give millions of vectors.
    minimum = min(_vectors(request), key=lambda v: (cost(v), tuple(-x for x in v)), default=None)
    if minimum is None:
        return {"minimum": None}
    plans = {"minimum": minimum}
    bounds = {
        str(e): Fraction(cost(minimum)) * (1 + Fraction(e)) for e in set(request.policy.epsilons)
    }
    best = {name: None for name in bounds}
    diversification = request.policy.diversification_epsilon
    if diversification is not None:
        best["diversified"] = None
        balanced_bound = Fraction(cost(minimum)) * (1 + Fraction(diversification))
    for v in _vectors(request):
        c = cost(v)
        key = (risk(v), c, tuple(-x for x in v))
        for name, bound in bounds.items():
            if c <= bound and (best[name] is None or key < best[name][0]):
                best[name] = (key, v)
        if diversification is not None and c <= balanced_bound and key[0] <= risk(minimum):
            balanced = (max(v), *key)
            if best["diversified"] is None or balanced < best["diversified"][0]:
                best["diversified"] = (balanced, v)
    plans |= {name: value[1] for name, value in best.items()}
    return plans


# --- Invariants on a solver result ------------------------------------------------------


def quantities(plan) -> tuple[int, ...]:
    return tuple(a.quantity for a in sorted(plan.allocations, key=lambda a: a.supplier_id))


def check_result(request, result, expected) -> list[str]:
    """Empty list when every invariant holds."""
    failures = []
    if expected["minimum"] is None:
        if result.status is not PlanningStatus.INFEASIBLE:
            failures.append(f"reference infeasible, solver {result.status.value}")
        return failures
    if result.status is not PlanningStatus.OPTIMAL:
        return [f"reference feasible, solver {result.status.value}"]
    q = request.requirement.approved_quantity
    ranges = _ranges(request)
    suppliers = sorted(request.suppliers, key=lambda s: s.supplier_id)
    plans = (result.minimum_cost_plan, *result.alternatives)
    for index, plan in enumerate(plans):
        x = quantities(plan)
        if sum(x) != q:
            failures.append(f"plan {index}: Σx = {sum(x)} ≠ Q = {q}")
        if sum(v > 0 for v in x) > request.policy.max_suppliers:
            failures.append(f"plan {index}: supplier count above K")
        if any(v and not low <= v <= high for v, (low, high) in zip(x, ranges, strict=True)):
            failures.append(f"plan {index}: allocation outside a supplier range")
        recomputed = sum(s.unit_price * v for s, v in zip(suppliers, x, strict=True))
        if recomputed != plan.total_cost:
            failures.append(f"plan {index}: recorded cost {plan.total_cost} ≠ {recomputed}")
    if quantities(result.minimum_cost_plan) != expected["minimum"]:
        failures.append("minimum-cost plan differs from the reference optimum")
    for run in result.runs:
        plan = plans[run.plan_index] if run.plan_index is not None else None
        name = "diversified" if run.kind == "diversified" else str(run.epsilon)
        if plan is None or quantities(plan) != expected[name]:
            failures.append(f"{name} ε={run.epsilon}: alternative differs from the reference")
    return failures


# --- In-process solver time and determinism --------------------------------------------


def timed_solve(request) -> tuple[object, float, int]:
    solver = PulpCbcSolver()
    runs = 0
    inner = solver._run

    def counted(*args, **kwargs):
        nonlocal runs
        runs += 1
        return inner(*args, **kwargs)

    solver._run = counted
    started = time.perf_counter()
    result = plan_procurement(request, solver)
    return result, time.perf_counter() - started, runs


def solver_check(name, request, repetitions, warmups, seed=0) -> dict:
    results, seconds, runs = [], [], set()
    for index in range(warmups + repetitions):
        result, elapsed, count = timed_solve(request)
        if index >= warmups:
            results.append(result)
            seconds.append(elapsed)
            runs.add(count)
    shuffled = list(request.suppliers)
    random.Random(seed).shuffle(shuffled)
    permuted, _, _ = timed_solve(replace(request, suppliers=tuple(shuffled)))
    expected = reference_plans(request)
    failures = check_result(request, results[0], expected)
    first = results[0]
    return {
        "variant": name,
        "suppliers": len(request.suppliers),
        "approved_quantity": request.requirement.approved_quantity,
        "max_suppliers": request.policy.max_suppliers,
        "epsilons": [str(e) for e in request.policy.epsilons],
        "diversification_epsilon": None
        if request.policy.diversification_epsilon is None
        else str(request.policy.diversification_epsilon),
        "status": first.status.value,
        "explanations": sorted({e.code for e in first.explanations}),
        "minimum_cost_quantities": None
        if first.minimum_cost_plan is None
        else dict(
            zip(
                sorted(s.supplier_id for s in request.suppliers),
                quantities(first.minimum_cost_plan),
                strict=True,
            )
        ),
        "distinct_alternatives": len(first.alternatives),
        "reference_feasible": expected["minimum"] is not None,
        "reference_match": not failures,
        "failures": failures,
        "repeated_identical": all(r == first for r in results),
        "permutation_identical": permuted == first,
        "cbc_runs_per_solve": sorted(runs),
        "solve_time": describe(seconds),
    }


def variants(request):
    """The stored request plus controlled variants for ties, K and infeasibility."""
    q = request.requirement.approved_quantity
    cheapest = min(s.unit_price for s in request.suppliers)
    yield "stored_request", request
    yield "max_suppliers_3", replace(request, policy=replace(request.policy, max_suppliers=3))
    yield (
        "equal_prices_tie_break",
        replace(
            request, suppliers=tuple(replace(s, unit_price=cheapest) for s in request.suppliers)
        ),
    )
    yield (
        "max_suppliers_1_infeasible",
        replace(request, policy=replace(request.policy, max_suppliers=1)),
    )
    yield (
        "moq_combination_infeasible",
        replace(
            request,
            suppliers=tuple(
                replace(s, minimum_order=MinimumOrder(q // 2 + 1)) for s in request.suppliers
            ),
        ),
    )
    yield (
        "demand_x5_infeasible",
        replace(request, requirement=replace(request.requirement, approved_quantity=q * 5)),
    )


# --- HTTP latency ------------------------------------------------------------------------


def measure_workload(client, group_id, terms, epsilons, repetitions, warmups) -> dict:
    terms = deepcopy(terms)
    terms["policy"]["epsilons"] = list(epsilons)
    payload = {"purchase_group_id": group_id, "terms": terms}
    last = terms["suppliers"][-1]
    price = Decimal(last["unit_price"])
    delta = {
        "kind": "price_change",
        "source": terms["requirement_source"],
        "suppliers": [
            {
                "supplier_id": last["supplier_id"],
                "unit_price": str((price * Decimal("0.9")).quantize(price)),
            }
        ],
    }
    samples = {"create": [], "scenario": [], "exact_retry": [], "get": []}
    allocations, first = set(), None

    def timed(call, status):
        started = time.perf_counter()
        response = call()
        elapsed = time.perf_counter() - started
        return checked(response, status), elapsed

    for index in range(warmups + repetitions):
        key = str(uuid4())
        create = f"{BASE}/from-odoo-history"
        case, t_create = timed(
            lambda key=key: client.post(create, json=payload, headers={"Idempotency-Key": key}),
            201,
        )
        scenario, t_scenario = timed(
            lambda case=case: client.post(
                f"{BASE}/{case['case_id']}/scenarios",
                json=delta,
                headers={"Idempotency-Key": str(uuid4())},
            ),
            201,
        )
        # A price cut keeps the request feasible, so only an optimal result counts as a sample.
        status = scenario["snapshot"]["result"]["status"]
        if status != PlanningStatus.OPTIMAL.value:
            raise ValueError(f"Price-change scenario returned {status}, expected optimal.")
        replay, t_retry = timed(
            lambda key=key: client.post(create, json=payload, headers={"Idempotency-Key": key}),
            200,
        )
        stored, t_get = timed(lambda case=case: client.get(f"{BASE}/{case['case_id']}"), 200)
        if not replay["idempotent_replay"] or {
            replay["snapshot_hash"],
            stored["snapshot_hash"],
        } != {case["snapshot_hash"]}:
            raise ValueError("Stored replay or GET differs from the created case.")
        if index >= warmups:
            for name, value in (
                ("create", t_create),
                ("scenario", t_scenario),
                ("exact_retry", t_retry),
                ("get", t_get),
            ):
                samples[name].append(value)
            minimum = case["snapshot"]["result"]["minimum_cost_plan"]
            allocations.add(
                None
                if minimum is None
                else tuple((a["supplier_id"], a["quantity"]) for a in minimum["allocations"])
            )
        first = first or case
    infeasible = checked(
        client.post(
            f"{BASE}/{first['case_id']}/scenarios",
            json={
                "kind": "demand_change",
                "source": terms["requirement_source"],
                "suppliers": [],
                "approved_quantity": terms["requirement"]["approved_quantity"] * 5,
            },
            headers={"Idempotency-Key": str(uuid4())},
        ),
        201,
    )
    return {
        "suppliers": len(terms["suppliers"]),
        "epsilons": list(epsilons),
        "latency": {name: describe(values) for name, values in samples.items()},
        "raw_ms": {name: [round(v * 1000, 1) for v in values] for name, values in samples.items()},
        "distinct_minimum_cost_allocations": len(allocations),
        "infeasible_scenario_status": infeasible["snapshot"]["result"]["status"],
        "base": first,
    }


def environment() -> dict:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "services": "Odoo 19 and PostgreSQL 16 in Podman on the same machine; API: one "
        "uvicorn worker on 127.0.0.1, client on the same machine",
    }


def database_identity(url: str) -> tuple:
    """Host (loopback names equal), port and database name of a SQLAlchemy URL."""
    try:
        parsed = make_url(url)
    except ArgumentError as error:
        raise RuntimeError(
            "TEST_DATABASE_URL or DECISION_DATABASE_URL is not a valid URL."
        ) from error
    host = parsed.host or "localhost"
    return ("localhost" if host in LOOPBACK else host, parsed.port or 5432, parsed.database)


def seeded_groups() -> dict[int, int]:
    """Quotation group ids of the seeded workloads, written by ``seed_odoo_history groups``.

    The listing shows only the newest open groups and carries no seed tag, so it cannot
    identify the evaluation groups."""
    if not GROUPS_FILE.exists():
        raise RuntimeError("Run 'python -m tools.seed_odoo_history groups' first.")
    stored = json.loads(GROUPS_FILE.read_text(encoding="utf-8"))
    return {int(size): int(group) for size, group in stored.items()}


def run(args) -> dict:
    check_reproduction_window()
    env = _env()
    token, database = env.get("API_SERVICE_TOKEN", ""), env.get("TEST_DATABASE_URL", "")
    if not token or not database:
        raise RuntimeError("Set API_SERVICE_TOKEN and TEST_DATABASE_URL (RUNBOOK §6).")
    development = env.get("DECISION_DATABASE_URL", "")
    if development and database_identity(development) == database_identity(database):
        raise RuntimeError(
            "TEST_DATABASE_URL points at the development planning database; "
            "use the disposable test database (RUNBOOK §6)."
        )
    test_env = env | {"DECISION_DATABASE_URL": database}
    migrated = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, env=test_env, check=False
    )
    if migrated.returncode:
        raise RuntimeError("Migrating the disposable test database failed.")
    args.directory.mkdir(parents=True, exist_ok=True)
    workloads, correctness = [], []
    groups = seeded_groups()
    missing = [size for size in SIZES if size not in groups]
    if missing:
        raise RuntimeError(f"No seeded group with {missing} suppliers; run seed groups.")
    with api(test_env, token, args.directory / "evaluation-api.log") as client:
        for size in SIZES:
            group_id = groups[size]
            preview = checked(
                client.get(f"{BASE}/odoo-history/preview", params={"purchase_group_id": group_id}),
                200,
            )
            if len(preview["terms"]["suppliers"]) != size:
                raise RuntimeError(f"Group {group_id} does not have {size} suppliers.")
            for count, epsilons in EPSILONS.items():
                print(f"Workload: {size} suppliers, {count} epsilon(s)", flush=True)
                measured = measure_workload(
                    client,
                    group_id,
                    preview["terms"],
                    epsilons,
                    args.repetitions,
                    args.warmups,
                )
                base = measured.pop("base")
                measured["purchase_group_id"] = group_id
                measured["solver_runtime"] = base["snapshot"]["solver"].get("runtime")
                workloads.append(measured)
                request = read_request(base["snapshot"]["request"])
                for name, variant in variants(request):
                    if count == 3 or name == "stored_request":
                        check = solver_check(name, variant, args.repetitions, args.warmups)
                        check["workload"] = f"{size} suppliers / {count} epsilon(s)"
                        correctness.append(check)
    passed = all(
        c["reference_match"] and c["repeated_identical"] and c["permutation_identical"]
        for c in correctness
    ) and all(w["infeasible_scenario_status"] == "infeasible" for w in workloads)
    return {
        "report": "P4 MILP/API evaluation (Odoo-history path)",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "repository": git_revision(),
        "environment": environment(),
        "protocol": {
            "workloads": f"open quotation groups with {list(SIZES)} suppliers × epsilon sets "
            f"{[list(v) for v in EPSILONS.values()]}; buyer default terms from the preview "
            "(K = 2, concentration 0.8, capacity ⌈0.6·Q⌉ per supplier)",
            "warmups": args.warmups,
            "repetitions": args.repetitions,
            "percentile": "nearest rank: the ⌈0.95·n⌉-th sorted value",
            "operations": {
                "create": "POST from-odoo-history: Odoo quotation + history read, inference, "
                "MILP, storage",
                "scenario": "POST scenarios (price −10 % for the last supplier): MILP + storage",
                "exact_retry": "same POST with the same Idempotency-Key: stored replay",
                "get": "GET the stored case",
                "solve_time": "in-process plan_procurement on the stored request (all CBC runs "
                "incl. ε alternatives and tie-break), same configuration as the API",
            },
            "reference_optimum": "exhaustive enumeration of every integer allocation from the "
            "raw input, independent of the core bounds and the solver",
            "database": "disposable test planning database (not the development library)",
        },
        "data_notice": "Generated purchase history and buyer default terms; timings describe "
        "this machine only and are not a service-level agreement.",
        "passed": passed,
        "workloads": workloads,
        "correctness": correctness,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--directory", type=Path, default=ROOT / ".artifacts" / "evaluation")
    parser.add_argument(
        "--report", type=Path, default=ROOT / "docs" / "evidence" / "P4_MILP_EVALUATION.json"
    )
    args = parser.parse_args(argv)
    try:
        report = run(args)
    except (RuntimeError, ValueError, KeyError, OSError, httpx.HTTPError) as error:
        print(f"Evaluation incomplete: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    write_json(args.report, report)
    print(f"{'PASSED' if report['passed'] else 'FAILED'}; report: {args.report}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
