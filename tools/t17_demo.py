"""Repeatable controlled hybrid acceptance; HTTP only, no Odoo writes or training."""

import argparse
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import httpx

from tools.t15_demo import BASE, local_url, write_json


def scenario_requests(payload):
    facts = payload["terms"] if "terms" in payload else payload["controlled_input"]
    supplier = facts["suppliers"][-1]["supplier_id"]
    source = facts["requirement_source"]
    changes = (
        ("supplier_outage", {"available": False}, None),
        ("capacity_reduction", {"capacity": 100}, None),
        ("demand_increase", {}, 250),
        ("price_increase", {"unit_price": "13"}, None),
        ("combined", {"capacity": 150, "unit_price": "10"}, 220),
        ("demand_increase", {}, 500),
    )
    return [
        {
            "kind": kind,
            "source": source,
            "suppliers": [{"supplier_id": supplier, **delta}] if delta else [],
            **({"approved_quantity": quantity} if quantity else {}),
        }
        for kind, delta, quantity in changes
    ]


def checked(response, status):
    if response.status_code != status:
        raise ValueError(f"Expected HTTP {status}, received {response.status_code}.")
    return response.json()


def download_pdf(client, case, path):
    decision = case["final_decision"]
    content_hash = decision["approved_content_hash"]
    url = f"{BASE}/{case['case_id']}/approved-pdf/{content_hash}"
    response = client.get(url, params={"download": "true"})
    digest = hashlib.sha256(response.content).hexdigest()
    if (
        response.status_code != 200
        or response.headers.get("content-type") != "application/pdf"
        or response.headers.get("x-approved-content-hash") != content_hash
        or response.headers.get("x-pdf-sha256") != digest
        or not response.content.startswith(b"%PDF-")
    ):
        raise ValueError("PDF retrieval/content identity failed.")
    if path.exists() and path.read_bytes() != response.content:
        raise ValueError("Retrieved PDF differs from the saved demonstration artifact.")
    path.write_bytes(response.content)
    return {"sha256": digest, "bytes": len(response.content), "content_hash": content_hash}


def run_flow(directory, client, actor, reason, no_award_reason, *, odoo_history=False):
    if not actor.strip() or not reason.strip() or not no_award_reason.strip():
        raise ValueError("Explicit demonstration actor and both outcome reasons are required.")
    if odoo_history:
        preview = checked(client.get(f"{BASE}/odoo-history/local-v1"), 200)
        if (
            preview["model_readiness"] != "ready"
            or preview["database"] != "procurement_v2_history_test_v1"
            or preview["origin"] != "controlled_synthetic"
            or [p["value"] for p in preview["history"]] != ["100.00", "66.67", "33.33"]
            or [p["sample_size"] for p in preview["history"]] != [3, 3, 3]
        ):
            raise ValueError("The controlled Odoo history profile is not ready.")
        payload = {k: preview[k] for k in ("profile_id", "profile_revision", "terms")}
    else:
        payload = json.loads((directory / "create-request.json").read_text(encoding="utf-8"))
    create_path = f"{BASE}/from-odoo-history" if odoo_history else f"{BASE}/from-odoo"
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / f"t17-run-{uuid4()}.json"
    report = {"request": payload, "operations": [], "scenarios": []}

    def post(path, body):
        operation = {"path": path, "payload": body, "key": str(uuid4())}
        report["operations"].append(operation)
        write_json(report_path, report)  # Persist exact intent before a possibly uncertain POST.
        started = perf_counter()
        response = client.post(path, json=body, headers={"Idempotency-Key": operation["key"]})
        operation.update(status=response.status_code, seconds=perf_counter() - started)
        write_json(report_path, report)
        return checked(response, 201)

    print(f"Evidence and exact replay intents: {report_path}")
    started = perf_counter()
    base = post(create_path, payload)
    report["base"] = base
    for delta in scenario_requests(payload):
        child = post(f"{BASE}/{base['case_id']}/scenarios", delta)
        if child["parent_id"] != base["case_id"]:
            raise ValueError("Scenario must target the original base.")
        report["scenarios"].append(child)
    if report["scenarios"][-1]["snapshot"]["result"]["status"] != "infeasible":
        raise ValueError("Controlled demand-500 case must be infeasible.")
    if not base["snapshot"]["result"]["alternatives"]:
        raise ValueError("A valid saved alternative is required for this demonstration.")
    no_award = post(create_path, payload)
    for name, case, outcome, index in (
        ("approved", base, "approve", 1),
        ("no_award", no_award, "no_award", None),
    ):
        report[name] = post(
            f"{BASE}/{case['case_id']}/final-decision",
            {
                "snapshot_hash": case["snapshot_hash"],
                "outcome": outcome,
                "plan_index": index,
                "actor_reference": actor,
                "rationale": reason if outcome == "approve" else no_award_reason,
                "demonstration_acknowledged": True,
            },
        )
    report["pdf"] = download_pdf(client, report["approved"], report_path.with_suffix(".pdf"))
    report["seconds"] = perf_counter() - started
    write_json(report_path, report)
    verify_stored(report_path, client)
    print(
        f"Complete controlled HTTP flow: {report['seconds']:.3f}s; browser acceptance is separate."
    )
    return report_path


def verify_stored(report_path, client):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    cases = {
        c["case_id"]: c for c in (report["approved"], report["no_award"], *report["scenarios"])
    }
    for case in cases.values():
        stored = checked(client.get(f"{BASE}/{case['case_id']}"), 200)
        if any(
            stored[field] != case[field]
            for field in ("snapshot", "snapshot_hash", "final_decision")
        ):
            raise ValueError("Stored case or human decision changed.")
    for operation in report["operations"]:
        replay = checked(
            client.post(
                operation["path"],
                json=operation["payload"],
                headers={"Idempotency-Key": operation["key"]},
            ),
            200,
        )
        if not replay["idempotent_replay"]:
            raise ValueError("Exact retry was not a stored replay.")
        expected = cases.get(replay["case_id"])
        if expected is None or any(
            replay[field] != expected[field]
            for field in ("snapshot", "snapshot_hash", "final_decision")
        ):
            raise ValueError("Exact retry changed the saved case or decision.")
    if download_pdf(client, report["approved"], report_path.with_suffix(".pdf")) != report["pdf"]:
        raise ValueError("Approved PDF identity changed.")
    denied = client.get(f"{BASE}/{report['no_award']['case_id']}/approved-pdf/" + "0" * 64)
    if denied.status_code != 422:
        raise ValueError("No-award unexpectedly permits an approved PDF.")
    print("Stored cases, exact retries and identical PDF verified; No-award PDF denied.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "reopen"))
    parser.add_argument("--directory", type=Path, default=Path(".artifacts/t15-odoo-demo"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--actor")
    parser.add_argument("--reason")
    parser.add_argument("--no-award-reason")
    parser.add_argument(
        "--odoo-history",
        action="store_true",
        help="Acquire the fixed local history preview; never prepare or train a model.",
    )
    parser.add_argument("--base-url", type=local_url, default="http://127.0.0.1:8000")
    args = parser.parse_args()
    if args.command == "run" and (not args.actor or not args.reason or not args.no_award_reason):
        parser.error("run requires --actor, --reason and --no-award-reason for the demonstration.")
    if args.command == "reopen" and not args.report:
        parser.error("reopen requires the saved --report path.")
    token = os.getenv("API_SERVICE_TOKEN", "")
    if not token or not token.isascii():
        parser.error("Export an ASCII API_SERVICE_TOKEN; it is never saved in the report.")
    try:
        with httpx.Client(
            base_url=args.base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=45,
            follow_redirects=False,
        ) as client:
            if args.command == "run":
                run_flow(
                    args.directory,
                    client,
                    args.actor,
                    args.reason,
                    args.no_award_reason,
                    odoo_history=args.odoo_history,
                )
            else:
                verify_stored(args.report, client)
    except (OSError, ValueError, KeyError, httpx.HTTPError) as error:
        parser.exit(
            1, f"T17 demonstration incomplete ({type(error).__name__}); inspect saved intents.\n"
        )


if __name__ == "__main__":
    main()
