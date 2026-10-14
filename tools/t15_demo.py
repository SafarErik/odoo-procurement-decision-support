"""Repository-local controlled T15 preparation and HTTP demonstration; no Odoo access."""

import argparse
import json
import os
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import httpx

from supplier_evaluation.artifacts import save_model
from supplier_evaluation.contracts import SYNTHETIC, QuantityValidity
from supplier_evaluation.dataset import (
    BOUNDARY,
    EXTRACTED_AT,
    generate_dataset,
    prepare_dataset,
    save_dataset,
)
from supplier_evaluation.model import train

BASE = "/api/v2/procurement/planning-cases"


def prepare_assets(directory, *, domain=None, supplier_count=3):
    if supplier_count not in (3, 5, 10):
        raise ValueError("Controlled workloads support 3, 5 or 10 suppliers.")
    rows = generate_dataset() if domain is None else generate_dataset(domain=domain)
    split = prepare_dataset(rows, boundary=BOUNDARY, extracted_at=EXTRACTED_AT)
    model = train(split)
    save_model(model, directory)
    save_dataset(directory / "dataset.json", rows)
    assessments = sorted(
        (
            model.infer(e.snapshot, QuantityValidity(1, 1000, "controlled-proxy-v1"))
            for e in split.test
        ),
        key=lambda a: (a.score, a.snapshot.context.supplier_id),
    )
    chosen = (assessments[-1], assessments[len(assessments) // 2], assessments[0])
    chosen += tuple(a for a in assessments if a not in chosen)[: supplier_count - 3]
    context, cutoff = chosen[0].snapshot.context, chosen[0].snapshot.cutoff
    deadline = (cutoff + timedelta(days=7)).date().isoformat()
    source = {
        "source_type": "controlled_business_terms",
        "source_reference": "t15-demo-v1",
        "observed_at": cutoff.isoformat(),
    }
    payload = {
        "source_type": SYNTHETIC,
        "company_id": context.company_id,
        "as_of": cutoff.isoformat(),
        "approval_reference": "controlled-demand-10-v1",
        "requirement": {
            "product_id": context.product_id,
            "approved_quantity": 10,
            "quantity_unit": context.quantity_unit,
            "currency": "EUR",
            "required_date": deadline,
        },
        "requirement_source": source.copy(),
        "policy_source": source.copy(),
        "policy": {"max_suppliers": 2, "concentration_limit": "0.8", "epsilons": ["0.1"]},
        "suppliers": [],
    }
    by_context = {row.context: row for row in rows if row.cutoff == cutoff}
    prices = ("10", "10.5", "11") + tuple(
        str(Decimal("11.5") + Decimal("0.5") * i) for i in range(supplier_count - 3)
    )
    capacities = (6, 8, 10) + (10,) * (supplier_count - 3)
    for a, price, capacity in zip(chosen, prices, capacities, strict=True):
        row = by_context[a.snapshot.context]
        payload["suppliers"].append(
            {
                "supplier_id": row.context.supplier_id,
                "offer_id": "offer:" + row.context.supplier_id,
                "unit_price": price,
                "capacity": capacity,
                "available": True,
                "minimum_order_quantity": None,
                "price_quantities": {"minimum": 1, "maximum": 1000},
                "delivery_quantities": {"minimum": 1, "maximum": 1000},
                "promised_date": deadline,
                "source": source.copy(),
                "history_reference": row.source_reference,
                "score_quantities": {
                    "minimum": 1,
                    "maximum": 1000,
                    "reference": "controlled-proxy-v1",
                },
                "receipts": [
                    {
                        "line_id": line.line_id,
                        "expected_arrival": line.expected_arrival.isoformat(),
                        "completed_at": line.completed_at.isoformat(),
                        "available_at": line.available_at.isoformat(),
                    }
                    for line in row.history
                ],
            }
        )
    return payload


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def prepare_demo(directory):
    directory.mkdir(parents=True, exist_ok=True)
    payload = prepare_assets(directory / "model")
    scenario = {
        "kind": "supplier_outage",
        "source": payload["requirement_source"].copy(),
        "suppliers": [{"supplier_id": payload["suppliers"][0]["supplier_id"], "available": False}],
    }
    write_json(directory / "create-request.json", payload)
    write_json(directory / "scenario-request.json", scenario)
    print(f"Prepared synthetic model and matched requests in {directory}")
    print(f"Simulation as_of: {payload['as_of']} (keep this date; this is synthetic evidence)")
    return payload


def run_demo(directory, client, *, create_path=BASE):
    payload = json.loads((directory / "create-request.json").read_text(encoding="utf-8"))
    delta = json.loads((directory / "scenario-request.json").read_text(encoding="utf-8"))
    record = {"base_key": str(uuid4()), "scenario_key": str(uuid4())}
    report_path = directory / f"run-{record['base_key']}.json"
    write_json(report_path, record)  # Keep keys for manual exact replay after an uncertain POST.
    print(f"Run evidence and replay keys: {report_path}")

    def accepted(response, status):
        if response.status_code != status:
            print(f"Expected HTTP {status}, received {response.status_code}; check API settings.")
            raise ValueError(f"Expected HTTP {status}, received {response.status_code}.")
        return response.json()

    base = accepted(
        client.post(create_path, json=payload, headers={"Idempotency-Key": record["base_key"]}), 201
    )
    record["base"] = base
    write_json(report_path, record)
    scenario = accepted(
        client.post(
            f"{BASE}/{base['case_id']}/scenarios",
            json=delta,
            headers={"Idempotency-Key": record["scenario_key"]},
        ),
        201,
    )
    record["scenario"] = scenario
    write_json(report_path, record)
    if scenario["parent_id"] != base["case_id"]:
        raise ValueError("Scenario lineage differs from the created base.")
    for case in (base, scenario):
        stored = accepted(client.get(f"{BASE}/{case['case_id']}"), 200)
        if stored != case:
            raise ValueError("Stored retrieval differs from its created case.")
    replay = accepted(
        client.post(create_path, json=payload, headers={"Idempotency-Key": record["base_key"]}), 200
    )
    if (
        not replay["idempotent_replay"]
        or replay["case_id"] != base["case_id"]
        or replay["snapshot"] != base["snapshot"]
        or replay["snapshot_hash"] != base["snapshot_hash"]
    ):
        raise ValueError("Exact replay differs from the base snapshot.")
    record["stored_retrieval_and_replay_verified"] = True
    write_json(report_path, record)
    for label, case in (("Base", base), ("Supplier outage", scenario)):
        result = case["snapshot"]["result"]
        print(f"{label}: {result['status']}; case {case['case_id']}")
        for kind, plans in (
            ("minimum", [result["minimum_cost_plan"]]),
            ("alternative", result["alternatives"]),
        ):
            for plan in plans:
                if plan is not None:
                    quantities = ", ".join(
                        f"{a['supplier_id']}={a['quantity']}" for a in plan["allocations"]
                    )
                    currency = case["snapshot"]["request"]["requirement"]["currency"]
                    print(f"  {kind}: {currency} {plan['total_cost']}; allocation {quantities}")
    print("Stored base/child retrieval and exact replay match; parent snapshot unchanged.")
    return record


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--directory", type=Path, default=Path(".artifacts/t15-demo"))
    parser.add_argument("--base-url", type=local_url, default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare_demo(args.directory)
        else:
            token = os.getenv("T12_TRUSTED_CALLER_TOKEN", "")
            if not token or not token.isascii():
                parser.error("Export a local ASCII T12_TRUSTED_CALLER_TOKEN before run.")
            with httpx.Client(
                base_url=args.base_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=45,
                follow_redirects=False,
            ) as client:
                run_demo(args.directory, client)
    except (OSError, ValueError, httpx.HTTPError) as error:
        parser.exit(
            1,
            f"Demo did not complete ({type(error).__name__}). Inspect the run evidence; "
            "POSTs are not retried automatically.\n",
        )


if __name__ == "__main__":
    main()
