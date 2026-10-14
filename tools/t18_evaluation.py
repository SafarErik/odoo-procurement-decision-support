"""Bounded synthetic HTTP evaluation; preparation/training is strictly offline."""

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import httpx
import pulp

from application.planning_serialization import json_value, read_request, read_result, snapshot_json
from decision_core.planning.rules import checked_plan
from supplier_evaluation.contracts import SYNTHETIC
from supplier_evaluation.dataset import SEED
from tools.t15_demo import BASE, local_url, prepare_assets, write_json

TARGETS = {
    "create": 5,
    "supplier_outage": 5,
    "capacity_reduction": 5,
    "demand_increase": 5,
    "price_increase": 5,
    "combined": 5,
    "infeasible": 5,
    "approval": 1,
    "stored_get": 1,
    "exact_replay": 1,
    "first_pdf": 3,
    "cached_pdf": 1,
}
CONTRACT = {
    "warmups": 2,
    "measured_runs": 30,
    "targets_seconds": TARGETS,
    "percentile": "nearest rank: ceil(0.95 * timed attempts); failures included",
    "scope": "sequential loopback HTTP; synthetic ML; not production SLAs",
}


def digest(value):
    return hashlib.sha256(snapshot_json(value).encode()).hexdigest()


def checkpoint(path, report):
    temporary = path.with_suffix(".tmp")
    write_json(temporary, report)
    temporary.replace(path)


def prepare(directory, supplier_count=3, epsilon_count=1):
    if directory.exists():
        raise ValueError("Use a new evaluation directory; existing owner artifacts are preserved.")
    if supplier_count not in (3, 5, 10) or epsilon_count not in (1, 3):
        raise ValueError("Use a supported supplier/epsilon workload.")
    started = perf_counter()
    directory.mkdir(parents=True)
    payload = prepare_assets(directory / "model", supplier_count=supplier_count)
    payload["policy"]["epsilons"] = ["0.1"] if epsilon_count == 1 else ["0.05", "0.1", "0.2"]
    write_json(directory / "create-request.json", payload)
    write_json(directory / "preparation.json", {"offline_seconds": perf_counter() - started})


def environment(directory, payload):
    root = Path(__file__).resolve().parents[1]
    cbc = Path(pulp.PULP_CBC_CMD().path)

    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True, text=True, timeout=10
        ).stdout.strip()

    return {
        "recorded_at": datetime.now(UTC).isoformat(),
        "git_sha": git("rev-parse", "HEAD"),
        "working_tree": git("status", "--porcelain"),
        "working_diff_sha256": hashlib.sha256(git("diff", "HEAD").encode()).hexdigest(),
        "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "fixture_helper_sha256": hashlib.sha256(
            (root / "tools/t15_demo.py").read_bytes()
        ).hexdigest(),
        "hardware": {
            "processor": platform.processor(),
            "architecture": platform.machine(),
            "logical_cpus": os.cpu_count(),
            "os": platform.platform(),
        },
        "python": platform.python_version(),
        "dependencies": {
            name: version(name)
            for name in (
                "fastapi",
                "httpx",
                "sqlalchemy",
                "psycopg",
                "pulp",
                "reportlab",
                "scikit-learn",
                "numpy",
                "scipy",
                "joblib",
                "threadpoolctl",
                "uvicorn",
            )
        },
        "cbc": {
            "sha256": hashlib.sha256(cbc.read_bytes()).hexdigest(),
            "version_output": subprocess.run(
                [str(cbc), "-version"], check=True, capture_output=True, text=True, timeout=10
            ).stdout.strip(),
        },
        "prepared_input_sha256": digest(payload),
        "dataset_seed": SEED,
        "policy_sha256": digest(payload["policy"]),
        "asset_sha256": {
            name: hashlib.sha256((directory / "model" / name).read_bytes()).hexdigest()
            for name in ("tree.joblib", "manifest.json", "dataset.json")
        },
        "model_manifest": json.loads(
            (directory / "model/manifest.json").read_text(encoding="utf-8")
        ),
        "preparation": json.loads((directory / "preparation.json").read_text(encoding="utf-8")),
        "timing_boundary": "HTTP request/response only; validation and evidence IO excluded",
        "warm_state": (
            "Protocol: two complete warm-up flows before measurement; failures are recorded. "
            "First PDF means a fresh artifact, not a cold process. Startup not measured."
        ),
    }


def verify_plan_case(case, parent_id, manifest, *, infeasible=False):
    snapshot = case["snapshot"]
    if case["parent_id"] != parent_id or case["snapshot_hash"] != digest(snapshot):
        raise ValueError("Planning identity or original-base lineage differs.")
    if snapshot["model_manifest"] != manifest or snapshot["facts"]["source_type"] != SYNTHETIC:
        raise ValueError("Backend model differs from the offline prepared artifact.")
    if snapshot["result"]["status"] != ("infeasible" if infeasible else "optimal"):
        raise ValueError("Controlled workload did not produce a complete optimal result.")
    request, result = read_request(snapshot["request"]), read_result(snapshot["result"])
    if infeasible:
        if (
            result.minimum_cost_plan is not None
            or result.alternatives
            or result.runs
            or request.requirement.approved_quantity <= sum(s.capacity for s in request.suppliers)
        ):
            raise ValueError("Controlled capacity shortfall was not recorded without a plan.")
        return
    minimum = result.minimum_cost_plan
    if minimum != checked_plan(request, minimum.allocations):
        raise ValueError("Minimum allocation or exact cost/exposure differs.")
    if tuple(r.epsilon for r in result.runs) != tuple(sorted(set(request.policy.epsilons))):
        raise ValueError("Requested epsilons were not completely evaluated.")
    plans = (minimum, *result.alternatives)
    if {r.plan_index for r in result.runs} - {0} != set(range(1, len(plans))):
        raise ValueError("Distinct alternatives have inconsistent run references.")
    for run in result.runs:
        plan = plans[run.plan_index]
        if (
            Fraction(plan.total_cost) > Fraction(minimum.total_cost) * (1 + Fraction(run.epsilon))
            or plan.risk_exposure > minimum.risk_exposure
        ):
            raise ValueError("Epsilon cost cap or exposure trade-off differs.")
    for index, plan in enumerate(result.alternatives, 1):
        epsilon = next(r.epsilon for r in result.runs if r.plan_index == index)
        if plan != checked_plan(request, plan.allocations, Fraction(minimum.total_cost), epsilon):
            raise ValueError("Alternative allocation or exact cost/exposure differs.")


def scenario_requests(payload):
    supplier = payload["suppliers"][0]["supplier_id"]
    changes = (
        ("supplier_outage", {"available": False}, None),
        ("capacity_reduction", {"capacity": 3}, None),
        ("demand_increase", {}, 12),
        ("price_increase", {"unit_price": "12"}, None),
        ("combined", {"capacity": 3, "unit_price": "12"}, 12),
        ("infeasible", {}, 1000),
    )
    return {
        name: {
            "kind": "demand_increase" if name == "infeasible" else name,
            "source": payload["requirement_source"],
            "suppliers": [{"supplier_id": supplier, **delta}] if delta else [],
            **({"approved_quantity": quantity} if quantity else {}),
        }
        for name, delta, quantity in changes
    }


def verify_scenario(child, base, delta, manifest, *, infeasible=False):
    verify_plan_case(child, base["case_id"], manifest, infeasible=infeasible)
    left, right = base["snapshot"], child["snapshot"]
    if any(right[field] != left[field] for field in ("facts", "assessments", "model_manifest")):
        raise ValueError("Scenario changed original facts or saved synthetic assessments.")
    expected_request = deepcopy(left["request"])
    paths = {}
    if "approved_quantity" in delta:
        expected_request["requirement"]["approved_quantity"] = delta["approved_quantity"]
        paths["request.requirement.approved_quantity"] = "approved_quantity"
    for change in delta["suppliers"]:
        terms = next(
            s for s in expected_request["suppliers"] if s["supplier_id"] == change["supplier_id"]
        )
        for field, value in change.items():
            if field != "supplier_id":
                terms[field] = value
                paths[f"request.suppliers[{change['supplier_id']}].{field}"] = field
    source = {
        **delta["source"],
        "observed_at": json_value(datetime.fromisoformat(delta["source"]["observed_at"])),
    }
    expected_delta = {
        **delta,
        "source": {"field_name": "scenario_delta", **source},
        "approved_quantity": delta.get("approved_quantity"),
    }
    expected_delta["suppliers"] = [
        {"available": None, "capacity": None, "unit_price": None, **s} for s in delta["suppliers"]
    ]
    entries = [e for e in left["provenance"]["entries"] if e["canonical_path"] not in paths]
    entries += [
        {"canonical_path": path, "field_name": field, **source}
        for path, field in sorted(paths.items())
    ]
    if (
        right["request"] != expected_request
        or right["scenario"] != expected_delta
        or right["provenance"] != {"entries": entries}
    ):
        raise ValueError("Saved scenario delta, changed terms or immutable provenance differs.")
    comparison = right["comparison"]
    if (
        comparison["base_status"] != left["result"]["status"]
        or comparison["scenario_status"] != right["result"]["status"]
        or comparison["meaning"]
        != "Total cost across explicit demand; not a like-for-like saving claim."
    ):
        raise ValueError("Comparison outcome or changed-demand meaning differs.")
    if infeasible:
        expected_comparison = None
    else:
        minimum, changed = left["result"]["minimum_cost_plan"], right["result"]["minimum_cost_plan"]

        def exposure(plan):
            value = plan["risk_exposure"]
            return Fraction(value["numerator"], value["denominator"])

        expected_comparison = {
            "total_cost_delta": json_value(
                Decimal(changed["total_cost"]) - Decimal(minimum["total_cost"])
            ),
            "risk_exposure_delta": json_value(exposure(changed) - exposure(minimum)),
            "base_allocations": minimum["allocations"],
            "scenario_allocations": changed["allocations"],
        }
    if comparison["minimum_cost"] != expected_comparison:
        raise ValueError("Exact stored cost/exposure/allocation comparison differs.")


def same_case(actual, expected):
    if any(
        actual[field] != expected[field]
        for field in (
            "case_id",
            "created_at",
            "parent_id",
            "snapshot",
            "snapshot_hash",
            "final_decision",
        )
    ):
        raise ValueError("Stored case, approval, content identity or timestamp changed.")


def verify_pdf(response, content_hash, first=None):
    if (
        response.headers.get("content-type") != "application/pdf"
        or not response.headers.get("x-pdf-reference")
        or response.headers.get("x-approved-content-hash") != content_hash
        or response.headers.get("x-pdf-sha256") != hashlib.sha256(response.content).hexdigest()
        or not response.content.startswith(b"%PDF-")
        or (first is not None and response.content != first.content)
        or (
            first is not None
            and response.headers.get("x-pdf-reference") != first.headers.get("x-pdf-reference")
        )
    ):
        raise ValueError("PDF binding, bytes or stable document identity differs.")


def summarize(attempts):
    summary = {}
    for name, target in TARGETS.items():
        rows = [a["operations"][name] for a in attempts if a["phase"] == "measured"]
        times = sorted(r["seconds"] for r in rows if r.get("seconds") is not None)
        successes = sum(r["outcome"] == "success" for r in rows)
        p95 = times[math.ceil(0.95 * len(times)) - 1] if times else None
        summary[name] = {
            "planned": len(rows),
            "attempted": sum(r["outcome"] != "not_attempted" for r in rows),
            "successful": successes,
            "pending": sum(r["outcome"] == "pending" for r in rows),
            "not_attempted": sum(r["outcome"] == "not_attempted" for r in rows),
            "failed": sum(
                r["outcome"] in {"http_error", "transport_error", "validation_error"} for r in rows
            ),
            "unmeasured": len(rows) - len(times),
            "timed_samples": len(times),
            "median_seconds": statistics.median(times) if times else None,
            "p95_seconds": p95,
            "maximum_seconds": max(times) if times else None,
            "target_seconds": target,
            "latency_target_met": p95 <= target if p95 is not None else None,
            "gate": "PASS"
            if successes == CONTRACT["measured_runs"] and len(times) == successes and p95 <= target
            else "FAIL",
        }
    return summary


def run_attempt(client, payload, manifest, attempt, save, pdf_path):
    operations = attempt["operations"]

    def measure(name, method, path, expected, check, body=None, key=None):
        row = operations[name]
        row.update(outcome="pending", method=method, path=path)
        if body is not None:
            row.update(payload=body, key=key or str(uuid4()))
        save()  # Preserve exact intent before a potentially uncertain write.
        started = perf_counter()
        try:
            response = client.request(
                method,
                path,
                json=body,
                headers={"Idempotency-Key": row["key"]} if body is not None else {},
            )
        except httpx.HTTPError as error:
            row.update(
                seconds=perf_counter() - started,
                outcome="transport_error",
                error_type=type(error).__name__,
                uncertain=method == "POST" or name == "first_pdf",
            )
            save()
            raise
        row.update(seconds=perf_counter() - started, http_status=response.status_code)
        if response.status_code != expected:
            row.update(
                outcome="http_error",
                uncertain=(method == "POST" or name == "first_pdf") and response.status_code >= 500,
            )
            try:
                detail = response.json().get("detail")
                if isinstance(detail, dict):
                    row["error_code"] = detail.get("code")
            except (ValueError, AttributeError):
                pass  # Status is still recorded for non-JSON dependency failures.
            save()
            raise ValueError("Unexpected HTTP status; no automatic retry.")
        try:
            if name.endswith("pdf"):
                row["document"] = {
                    "sha256": hashlib.sha256(response.content).hexdigest(),
                    "bytes": len(response.content),
                    "content_hash": response.headers.get("x-approved-content-hash"),
                    "reference": response.headers.get("x-pdf-reference"),
                }
            else:
                value = response.json()
                snapshot = value.get("snapshot", {})
                decision = value.get("final_decision")
                row["response"] = {
                    "case_id": value.get("case_id"),
                    "snapshot_hash": value.get("snapshot_hash"),
                    "created_at": value.get("created_at"),
                    "parent_id": value.get("parent_id"),
                    "idempotent_replay": value.get("idempotent_replay"),
                    "request_sha256": digest(snapshot.get("request")),
                    "result": snapshot.get("result"),
                    "solver": snapshot.get("solver"),
                    "scenario": snapshot.get("scenario"),
                    "comparison": snapshot.get("comparison"),
                    "provenance_sha256": digest(snapshot.get("provenance")),
                    "assessments_sha256": digest(snapshot.get("assessments")),
                    "requested_epsilons": snapshot.get("request", {})
                    .get("policy", {})
                    .get("epsilons"),
                    "distinct_alternatives": len(
                        snapshot.get("result", {}).get("alternatives", [])
                    ),
                    "final_decision": None
                    if decision is None
                    else {
                        "intent": decision.get("intent"),
                        "audit": decision.get("audit"),
                        "approved_content_hash": decision.get("approved_content_hash"),
                    },
                }
            check(response)
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            row.update(outcome="validation_error", error_type=type(error).__name__)
            save()
            raise
        row["outcome"] = "success"
        save()
        return response

    base = measure(
        "create", "POST", BASE, 201, lambda r: verify_plan_case(r.json(), None, manifest), payload
    ).json()
    for name, delta in scenario_requests(payload).items():
        measure(
            name,
            "POST",
            f"{BASE}/{base['case_id']}/scenarios",
            201,
            lambda r, delta=delta, name=name: verify_scenario(
                r.json(), base, delta, manifest, infeasible=name == "infeasible"
            ),
            delta,
        )
    intent = {
        "snapshot_hash": base["snapshot_hash"],
        "outcome": "approve",
        "plan_index": 0,
        "actor_reference": "T18 controlled evaluator",
        "rationale": "Explicitly approve the saved minimum-cost plan for technical evaluation.",
        "demonstration_acknowledged": True,
    }

    def approval(response):
        case = response.json()
        if case["snapshot"] != base["snapshot"] or case["snapshot_hash"] != base["snapshot_hash"]:
            raise ValueError("Approval changed original-base content.")
        decision = case["final_decision"]
        content = decision["approved_content"]
        if (
            decision["intent"] != intent
            or decision["approved_content_hash"] != digest(content)
            or content["selected_plan"] != base["snapshot"]["result"]["minimum_cost_plan"]
        ):
            raise ValueError("Approval intent, selected plan or approved-content identity differs.")

    approved = measure(
        "approval", "POST", f"{BASE}/{base['case_id']}/final-decision", 201, approval, intent
    ).json()
    measure(
        "stored_get",
        "GET",
        f"{BASE}/{base['case_id']}",
        200,
        lambda r: same_case(r.json(), approved),
    )

    def replay(response):
        value = response.json()
        same_case(value, approved)
        if value["idempotent_replay"] is not True:
            raise ValueError("Creation replay was not a stored exact replay.")

    measure("exact_replay", "POST", BASE, 200, replay, payload, operations["create"]["key"])
    content_hash = approved["final_decision"]["approved_content_hash"]
    url = f"{BASE}/{base['case_id']}/approved-pdf/{content_hash}?download=true"
    first = measure("first_pdf", "GET", url, 200, lambda r: verify_pdf(r, content_hash))
    pdf_path.write_bytes(first.content)
    measure("cached_pdf", "GET", url, 200, lambda r: verify_pdf(r, content_hash, first))


def evaluate(directory, client):
    payload = json.loads((directory / "create-request.json").read_text(encoding="utf-8"))
    suppliers, epsilons = len(payload["suppliers"]), payload["policy"]["epsilons"]
    if suppliers not in (3, 5, 10) or epsilons not in (["0.1"], ["0.05", "0.1", "0.2"]):
        raise ValueError("Use a prepared supported supplier/epsilon workload.")
    report_path = directory / f"evaluation-{uuid4()}.json"
    report = {
        "contract": {**CONTRACT, "suppliers": suppliers, "epsilons": epsilons},
        "environment": environment(directory, payload),
        "attempts": [
            {
                "phase": phase,
                "index": i + 1,
                "operations": {
                    name: {"outcome": "not_attempted", "seconds": None} for name in TARGETS
                },
            }
            for phase, count in (
                ("warmup", CONTRACT["warmups"]),
                ("measured", CONTRACT["measured_runs"]),
            )
            for i in range(count)
        ],
    }

    def save():
        report["summary"] = summarize(report["attempts"])
        checkpoint(report_path, report)

    save()
    print(f"Raw outcomes and exact intents: {report_path}")
    for ordinal, attempt in enumerate(report["attempts"]):
        try:
            run_attempt(
                client,
                payload,
                report["environment"]["model_manifest"],
                attempt,
                save,
                report_path.with_name(f"{report_path.stem}-{ordinal + 1}.pdf"),
            )
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
            if any(r.get("uncertain") for r in attempt["operations"].values()):
                report["stopped"] = (
                    "Uncertain write/artifact outcome; inspect exact intent before recovery. "
                    "Remaining operations were not attempted."
                )
                save()
                break
            if attempt["phase"] == "warmup":
                report["stopped"] = "Warm-up failed; measured operations were not attempted."
                save()
                break
        succeeded = sum(r["outcome"] == "success" for r in attempt["operations"].values())
        print(
            f"{attempt['phase']} {attempt['index']}: "
            f"{succeeded}/{len(TARGETS)} successful operations"
        )
    save()
    return report_path, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument(
        "--suppliers", type=int, choices=(3, 5, 10), default=3, help="Offline preparation only"
    )
    parser.add_argument(
        "--epsilon-count", type=int, choices=(1, 3), default=1, help="Offline preparation only"
    )
    parser.add_argument("--base-url", type=local_url, default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare(args.directory, args.suppliers, args.epsilon_count)
            return
        token = os.getenv("T12_TRUSTED_CALLER_TOKEN", "")
        if not token or not token.isascii():
            parser.error("Export an ASCII T12_TRUSTED_CALLER_TOKEN; it is never recorded.")
        with httpx.Client(
            base_url=args.base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=45,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            path, report = evaluate(args.directory, client)
        print(f"Summary and raw evidence: {path}")
        if any(row["gate"] != "PASS" for row in report["summary"].values()) or any(
            row["outcome"] != "success"
            for a in report["attempts"]
            if a["phase"] == "warmup"
            for row in a["operations"].values()
        ):
            parser.exit(
                1,
                "Evaluation contains failed/incomplete outcomes or missed targets; "
                "inspect report.\n",
            )
    except (OSError, ValueError, subprocess.SubprocessError, httpx.HTTPError) as error:
        parser.exit(
            1,
            f"Evaluation incomplete ({type(error).__name__}); inspect evidence. "
            "No automatic retry.\n",
        )


if __name__ == "__main__":
    main()
