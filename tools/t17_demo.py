"""Repeatable Odoo-history acceptance flow; HTTP only, no Odoo writes or training."""

import argparse
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import httpx

BASE = "/api/v2/procurement/planning-cases"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def local_url(value):
    url = httpx.URL(value)
    if (
        url.scheme != "http"
        or url.host not in {"127.0.0.1", "localhost", "::1"}
        or url.userinfo
        or url.path != "/"
        or url.query
        or url.fragment
    ):
        raise argparse.ArgumentTypeError("Use an HTTP loopback origin, e.g. http://127.0.0.1:8000.")
    return str(url)


def scenario_requests(payload):
    """Changes relative to the read quotation; the last one must be infeasible."""
    facts = payload["terms"]
    supplier = facts["suppliers"][-1]["supplier_id"]
    source = facts["requirement_source"]
    terms = facts["suppliers"][-1]
    price, capacity = Decimal(terms["unit_price"]), terms["capacity"]
    demand = facts["requirement"]["approved_quantity"]
    changes = (
        ("supplier_outage", {"available": False}, None),
        ("capacity_change", {"capacity": capacity * 5 // 6}, None),
        ("capacity_change", {"capacity": capacity * 2}, None),
        ("demand_change", {}, demand + demand // 4),
        ("demand_change", {}, max(1, demand * 3 // 4)),
        ("price_change", {"unit_price": str((price * Decimal("1.3")).quantize(price))}, None),
        ("price_change", {"unit_price": str((price * Decimal("0.8")).quantize(price))}, None),
        (
            "combined",
            {"capacity": capacity * 5 // 6, "unit_price": str(price + 1)},
            demand + 20,
        ),
        ("demand_change", {}, demand * 5),
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


def run_flow(directory, client, actor, reason, no_award_reason, *, odoo_history):
    if not actor.strip() or not reason.strip() or not no_award_reason.strip():
        raise ValueError("Explicit demonstration actor and both outcome reasons are required.")
    preview = checked(
        client.get(f"{BASE}/odoo-history/preview", params={"purchase_group_id": odoo_history}),
        200,
    )
    if preview["model_readiness"] != "ready":
        raise ValueError("The Odoo-history supplier model is not ready.")
    payload = {"purchase_group_id": odoo_history, "terms": preview["terms"]}
    create_path = f"{BASE}/from-odoo-history"
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
        raise ValueError("The five-fold demand case must be infeasible.")
    # Approve the lower-exposure alternative when the scores produced one.
    approved_index = 1 if base["snapshot"]["result"]["alternatives"] else 0
    no_award = post(create_path, payload)
    for name, case, outcome, index in (
        ("approved", base, "approve", approved_index),
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
    parser.add_argument("--directory", type=Path, default=Path(".artifacts/t17-demo"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--actor")
    parser.add_argument("--reason")
    parser.add_argument("--no-award-reason")
    parser.add_argument(
        "--odoo-history",
        type=int,
        metavar="PURCHASE_GROUP_ID",
        help="Odoo quotation group (see GET /api/v2/procurement/quotation-groups); never trains.",
    )
    parser.add_argument("--base-url", type=local_url, default="http://127.0.0.1:8000")
    args = parser.parse_args()
    if args.command == "run" and (not args.actor or not args.reason or not args.no_award_reason):
        parser.error("run requires --actor, --reason and --no-award-reason for the demonstration.")
    if args.command == "run" and not args.odoo_history:
        parser.error("run requires --odoo-history PURCHASE_GROUP_ID.")
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
