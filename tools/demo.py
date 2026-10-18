"""One-command reproducible demonstration on the Odoo-history path.

    python -m tools.dev demo                  start Odoo and the planning DB, then run this
    python -m tools.demo [--group N]          run against already started services

Needs the seeded ``pdss_history_gen`` database, the trained history model and the
``.env`` settings (RUNBOOK §5). The tool starts its own API on 127.0.0.1:8010, runs the
HTTP flow of ``tools.t17_demo`` (open quotation group → case → plans → scenarios in
both directions incl. an infeasible one → approval and a separate No-award → HU and EN
PDF), then restarts the API with Odoo unreachable and no model configured and replays
everything from storage. It never writes to Odoo and never trains. The summary goes to
``docs/evidence/P4_DEMO_REPORT.json``; full responses and PDFs stay in ``.artifacts/demo``.
"""

import argparse
import json
import platform
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import httpx

from tools.dev import ROOT, _env
from tools.seed_odoo_history import REPRODUCTION_LAST_CUTOFF
from tools.t17_demo import BASE, checked, run_flow, verify_stored, write_json

PORT = 8010
ORIGIN = f"http://127.0.0.1:{PORT}"
# Replay settings: a closed local port instead of Odoo, and no model directory.
ISOLATED = {"ODOO_BASE_URL": "http://127.0.0.1:9", "SUPPLIER_HISTORY_MODEL_DIRECTORY": ""}
STORED_EVIDENCE = "docs/evidence/P4_DEMO_REPORT.json and docs/evidence/P4_MILP_EVALUATION.json"


def check_reproduction_window(now: datetime | None = None) -> None:
    """Live runs need seeded history inside the feature window; later runs use stored evidence."""
    if (now or datetime.now(UTC)) > REPRODUCTION_LAST_CUTOFF:
        raise RuntimeError(
            f"The seeded history supports live cutoffs up to "
            f"{REPRODUCTION_LAST_CUTOFF:%Y-%m-%d}; later live runs find no settled lines. "
            f"Use the stored evidence instead: {STORED_EVIDENCE}."
        )


@contextmanager
def api(env: dict[str, str], token: str, log: Path):
    """A dedicated uvicorn process for one phase of the demonstration."""
    with httpx.Client(base_url=ORIGIN, timeout=5) as probe:
        try:
            probe.get("/api/v1/health")
            raise RuntimeError(f"Port {PORT} is already in use; stop that process first.")
        except httpx.TransportError:
            pass
    command = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--port", str(PORT)]
    with log.open("a", encoding="utf-8") as output:
        process = subprocess.Popen(
            [*command, "--host", "127.0.0.1"], cwd=ROOT, env=env, stdout=output, stderr=output
        )
    try:
        with httpx.Client(
            base_url=ORIGIN, headers={"Authorization": f"Bearer {token}"}, timeout=60
        ) as client:
            for _ in range(60):
                try:
                    if client.get("/api/v1/health").status_code == 200:
                        break
                except httpx.TransportError:
                    time.sleep(0.5)
            else:
                raise RuntimeError(f"API did not start; see {log}.")
            yield client
    finally:
        process.terminate()
        process.wait(timeout=30)


def open_groups(client: httpx.Client, wait_seconds: float = 240) -> list[dict]:
    """Wait for Odoo (it may still be starting after odoo-up)."""
    deadline = time.monotonic() + wait_seconds
    while True:
        response = client.get("/api/v2/procurement/quotation-groups", params={"limit": 20})
        if response.status_code == 200:
            return [g for g in response.json()["items"] if g["selectable"]]
        if response.status_code != 503 or time.monotonic() > deadline:
            raise RuntimeError(f"Odoo quotation groups unavailable (HTTP {response.status_code}).")
        time.sleep(5)


def default_group(groups: list[dict]) -> dict:
    """The original four-supplier RFQ; otherwise the oldest selectable group."""
    if not groups:
        raise RuntimeError("No selectable open quotation group; seed pdss_history_gen first.")
    four = [g for g in groups if g["supplier_count"] == 4]
    return min(four or groups, key=lambda g: g["purchase_group_id"])


def git_revision() -> dict:
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip()

    return {"commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain"))}


def plans(snapshot: dict) -> list[dict]:
    result = snapshot["result"]
    found = [result["minimum_cost_plan"], *result["alternatives"]]
    return [
        {
            "label": "minimum_cost" if index == 0 else f"alternative_{index}",
            "allocations": {
                a["supplier_id"]: a["quantity"] for a in p["allocations"] if a["quantity"]
            },
            "total_cost": p["total_cost"],
            "risk_exposure": round(
                p["risk_exposure"]["numerator"] / p["risk_exposure"]["denominator"], 4
            ),
        }
        for index, p in enumerate(found)
        if p is not None
    ]


def summary(raw: dict, group: dict, overview: dict, isolation: dict, seconds: float) -> dict:
    base = raw["base"]["snapshot"]
    manifest = base["model_manifest"]
    operations = raw["operations"]
    scenarios = []
    for operation, case in zip(operations[1:], raw["scenarios"], strict=False):
        snapshot = case["snapshot"]
        payload = operation["payload"]
        minimum = snapshot["comparison"]["minimum_cost"]
        scenarios.append(
            {
                "kind": payload["kind"],
                "approved_quantity": payload.get("approved_quantity"),
                "supplier_changes": payload["suppliers"],
                "status": snapshot["result"]["status"],
                "total_cost_delta": None if minimum is None else minimum["total_cost_delta"],
                "plans": plans(snapshot) if snapshot["result"]["minimum_cost_plan"] else [],
                "seconds": round(operation["seconds"], 3),
            }
        )
    approved = raw["approved"]["final_decision"]
    return {
        "report": "P4 one-command demonstration (Odoo-history path)",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "repository": git_revision(),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "data_notice": "Generated purchase history in the dedicated Odoo test database; "
        "values do not describe real suppliers.",
        "odoo_database": _env().get("ODOO_DATABASE"),
        "quotation_group": {
            "purchase_group_id": group["purchase_group_id"],
            "product": group["product_name"],
            "quantity": group["quantity"],
            "currency": group["currency"],
            "suppliers": {q["supplier_id"]: q["supplier_name"] for q in group["quotations"]},
        },
        "model": {
            "model_id": manifest["metadata"]["model_id"],
            "training_id": manifest["metadata"]["training_id"],
            "artifact_sha256": manifest["artifact_sha256"],
            "data_origin": manifest["metadata"].get("data_origin"),
        },
        "supplier_assessment": overview,
        "base_case": {
            "case_id": raw["base"]["case_id"],
            "status": base["result"]["status"],
            "policy": base["request"]["policy"],
            "approved_quantity": base["request"]["requirement"]["approved_quantity"],
            "plans": plans(base),
            "seconds": round(operations[0]["seconds"], 3),
        },
        "scenarios": scenarios,
        "decisions": {
            "approved": {
                "case_id": raw["approved"]["case_id"],
                "plan_index": approved["approved_content"]["plan_index"],
                "approved_content_hash": approved["approved_content_hash"],
            },
            "no_award": {
                "case_id": raw["no_award"]["case_id"],
                "outcome": raw["no_award"]["final_decision"]["audit"]["outcome"],
                "approved_pdf_denied": True,
            },
        },
        "pdf": raw["pdf"],
        "stored_replay": isolation,
        "flow_seconds": round(raw["seconds"], 3),
        "total_seconds": round(seconds, 3),
        "full_report": "kept locally under .artifacts/demo (contains every response)",
    }


def supplier_overview(client: httpx.Client, case_id: str) -> dict:
    return {
        language: checked(
            client.get(f"{BASE}/{case_id}/suppliers", params={"language": language}), 200
        )
        for language in ("hu", "en")
    }


def overview_summary(views: dict) -> list[dict]:
    return [
        {
            "supplier_id": row["supplier_id"],
            "supplier_name": row["supplier_name"],
            "class": row["assessment"]["class"],
            "score": row["assessment"]["score"],
            "summary_en": row["assessment"]["summary"],
            "unit_price": row["terms"]["unit_price"],
        }
        for row in views["en"]["suppliers"]
    ]


def run(args) -> Path:
    check_reproduction_window()
    env = _env()
    token = env.get("API_SERVICE_TOKEN", "")
    if not token:
        raise RuntimeError("Set API_SERVICE_TOKEN in .env.")
    args.directory.mkdir(parents=True, exist_ok=True)
    log = args.directory / "api.log"
    started = time.perf_counter()
    with api(env, token, log) as client:
        groups = open_groups(client)
        group = (
            next((g for g in groups if g["purchase_group_id"] == args.group), None)
            if args.group
            else default_group(groups)
        )
        if group is None:
            raise RuntimeError(f"Quotation group {args.group} is not open and selectable.")
        report_path = run_flow(
            args.directory,
            client,
            args.actor,
            args.reason,
            args.no_award_reason,
            odoo_history=group["purchase_group_id"],
        )
        raw = json.loads(report_path.read_text(encoding="utf-8"))
        views = supplier_overview(client, raw["base"]["case_id"])
    # Phase 2: the same stored cases with Odoo unreachable and no model configured.
    with api(env | ISOLATED, token, log) as client:
        preview = client.get(
            f"{BASE}/odoo-history/preview",
            params={"purchase_group_id": group["purchase_group_id"]},
        )
        if preview.status_code == 200:
            raise RuntimeError("Odoo is still reachable; the replay would not be isolated.")
        verify_stored(report_path, client)
        if supplier_overview(client, raw["base"]["case_id"]) != views:
            raise RuntimeError("Stored supplier overview changed without Odoo/model.")
    isolation = {
        "settings": {
            "ODOO_BASE_URL": ISOLATED["ODOO_BASE_URL"],
            "SUPPLIER_HISTORY_MODEL_DIRECTORY": "(empty: no model)",
        },
        "odoo_preview_status": preview.status_code,
        "checks": [
            "GET of every saved case equals the created snapshot, hash and decision",
            "exact retry of every POST is an idempotent stored replay (HTTP 200)",
            "HU and EN approved PDFs byte-identical to the first download",
            "supplier overview (HU, EN) identical",
            "No-award case has no approved PDF (HTTP 422)",
        ],
        "operations_replayed": len(raw["operations"]),
        "passed": True,
    }
    result = summary(raw, group, overview_summary(views), isolation, time.perf_counter() - started)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.report, result)
    print(f"Demonstration complete in {result['total_seconds']} s; summary: {args.report}")
    return args.report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", type=int, help="Odoo purchase group id (default: 4 suppliers)")
    parser.add_argument("--directory", type=Path, default=ROOT / ".artifacts" / "demo")
    parser.add_argument(
        "--report", type=Path, default=ROOT / "docs" / "evidence" / "P4_DEMO_REPORT.json"
    )
    parser.add_argument("--actor", default="Demonstration buyer")
    parser.add_argument(
        "--reason", default="Approve the lower-exposure alternative within the cost tolerance."
    )
    parser.add_argument(
        "--no-award-reason", default="Separate demonstration case: no purchase is authorized."
    )
    args = parser.parse_args(argv)
    try:
        run(args)
    except (RuntimeError, ValueError, KeyError, OSError, httpx.HTTPError) as error:
        print(f"Demonstration incomplete: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
