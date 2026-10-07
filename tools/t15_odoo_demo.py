"""Controlled live quotations + synthetic ML demonstration; no Odoo writes/history import."""

import argparse
import asyncio
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from application.odoo_planning_input import bind_controlled_odoo_input
from backend.app.dependencies import get_comparison_case_reader
from backend.app.planning_case_schemas import PlanningCreateRequest
from tools.t15_demo import BASE, local_url, prepare_assets, run_demo, write_json


def prepare_odoo_assets(directory, case, currency_code, currency_observed_at):
    """Train a new genuine synthetic artifact in the selected quotation domain offline."""
    if len(case.offers) != 3:
        raise ValueError("This demonstration requires exactly three fixture quotations.")
    offers = sorted(case.offers, key=lambda o: o.offer_id)
    line = offers[0].lines[0]
    payload = prepare_assets(
        directory / "model", domain=(offers[0].company_id, line.product_id, line.uom_id)
    )
    now = datetime.now(UTC)
    deadline = (now + timedelta(days=7)).date().isoformat()
    payload["as_of"] = now.isoformat()
    payload["approval_reference"] = "controlled-demand-200-v1"
    payload["requirement"].update(
        approved_quantity=200, currency=currency_code, required_date=deadline
    )
    payload["policy"]["epsilons"] = ["0.2"]
    source = {
        "source_type": "controlled_business_terms",
        "source_reference": "t15-odoo-demo-v1",
        "observed_at": now.isoformat(),
    }
    payload["requirement_source"] = source.copy()
    payload["policy_source"] = source.copy()
    # Explicitly simulated profiles: A lower, B middle, C higher exposure. Not Odoo receipts.
    payload["suppliers"].reverse()
    for supplier, offer, capacity, moq in zip(
        payload["suppliers"], offers, (120, 100, 160), (50, 100, 150), strict=True
    ):
        profile = supplier["supplier_id"]
        supplier.update(
            supplier_id=offer.supplier_id,
            offer_id=offer.offer_id,
            unit_price=str(offer.lines[0].unit_price),
            capacity=capacity,
            minimum_order_quantity=moq,
            promised_date=deadline,
            source=source.copy(),
            history_reference=f"t14_synthetic:{profile}:simulated-profile-for:{offer.supplier_id}",
        )
    facts = PlanningCreateRequest.model_validate(payload).to_facts()
    bind_controlled_odoo_input(case, facts, currency_code, currency_observed_at)
    request = {
        "purchase_group_id": int(case.comparison_case_id.rsplit(":", 1)[1]),
        "controlled_input": payload,
    }
    scenario = {
        "kind": "supplier_outage",
        "source": source.copy(),
        "suppliers": [{"supplier_id": offers[2].supplier_id, "available": False}],
    }
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "create-request.json", request)
    write_json(directory / "scenario-request.json", scenario)
    print(f"Prepared Odoo quotations and separately synthetic ML evidence: {directory}")
    print("Controlled Q=200, capacities=120/100/160, hard MOQ=50/100/150, epsilon=20%.")
    print("Prices and identities are re-read by the backend; changed expectations fail closed.")
    return request, scenario


async def prepare(directory, group_id):
    reader = get_comparison_case_reader()
    case = await reader.read_comparison_case(group_id)
    if not case.offers:
        raise ValueError("Missing selected fixture quotations.")
    code, observed_at = await reader.read_currency_code(case.offers[0].currency_id)
    return prepare_odoo_assets(directory, case, code, observed_at)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--group-id", type=int, default=2)
    parser.add_argument("--directory", type=Path, default=Path(".artifacts/t15-odoo-demo"))
    parser.add_argument("--base-url", type=local_url, default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            asyncio.run(prepare(args.directory, args.group_id))
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
                run_demo(args.directory, client, create_path=f"{BASE}/from-odoo")
    except Exception as error:
        parser.exit(
            1,
            f"Odoo demo incomplete ({type(error).__name__}); inspect local evidence.\n",
        )


if __name__ == "__main__":
    main()
