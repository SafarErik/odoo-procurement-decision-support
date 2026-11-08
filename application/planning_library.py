"""Bounded stored-case discovery; no acquisition, inference or optimization."""

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from application.errors import PlanningCaseError, RepositoryError
from application.planning_cases import (
    SCENARIO_KINDS,
    canonical_uuid,
    fingerprint,
    validate_snapshot,
)
from application.planning_decisions import validate_final_decision


@dataclass(frozen=True, slots=True)
class LibraryQuery:
    company: str
    status: str = "all"
    q: str = ""
    limit: int = 20
    parent_id: str | None = None
    after: tuple[datetime, str] | None = None

    @property
    def context(self):
        return fingerprint([self.company, self.status, self.q, self.limit, self.parent_id])


def library_query(company, status="all", q="", limit=20, cursor=None, parent_id=None):
    if not isinstance(company, str) or not company.strip():
        raise RepositoryError("library_unconfigured", "Configure the library company first.")
    if (
        status not in {"all", "draft", "approved", "no_award"}
        or not isinstance(q, str)
        or len(q.strip()) > 80
        or type(limit) is not int
        or not 1 <= limit <= 50
    ):
        raise ValueError("Invalid library filters.")
    if parent_id is not None:
        canonical_uuid(parent_id)
    query = LibraryQuery(company.strip(), status, q.strip(), limit, parent_id)
    if cursor is None:
        return query
    try:
        if not isinstance(cursor, str) or not 1 <= len(cursor) <= 1024:
            raise ValueError("Invalid cursor length.")
        value = json.loads(base64.b64decode(cursor, altchars=b"-_", validate=True))
        if set(value) != {"context", "time", "id"} or value["context"] != query.context:
            raise ValueError("Cursor filters changed.")
        timestamp = datetime.fromisoformat(value["time"])
        if timestamp.tzinfo is None or timestamp.utcoffset() != UTC.utcoffset(timestamp):
            raise ValueError("Cursor time must be UTC.")
        return LibraryQuery(
            company.strip(),
            status,
            q.strip(),
            limit,
            parent_id,
            (timestamp, canonical_uuid(value["id"])),
        )
    except (ValueError, TypeError, KeyError, AttributeError, binascii.Error) as error:
        raise ValueError("Invalid library cursor.") from error


def case_summary(case, decision, company):
    """One library row for a stored case: context, cost, status and changed assumptions.

    Re-validates the stored case (and its decision) first; anything inconsistent raises
    ``RepositoryError("invalid_library_data")`` instead of showing a partial row.
    """
    try:
        snapshot = validate_snapshot(case)
        facts, requirement = snapshot["facts"], snapshot["request"]["requirement"]
        if facts["company_id"] != company:
            raise ValueError("Case company mismatch.")
        for field in ("product_id", "quantity_unit", "currency"):
            if not isinstance(requirement[field], str) or not requirement[field].strip():
                raise ValueError("Missing saved context.")
        date.fromisoformat(requirement["required_date"])
        outcome = "draft"
        if decision is not None:
            if case.parent_id is not None:
                raise ValueError("A scenario cannot have a decision.")
            saved = validate_final_decision(case, decision)
            outcome = "approved" if saved["audit"]["outcome"] == "approve" else "no_award"
        scenario = snapshot["scenario"]
        labels = dict(facts.get("labels", ()))
        minimum = snapshot["result"]["minimum_cost_plan"]
        return {
            "case_id": case.case_id,
            "parent_id": case.parent_id,
            "created_at": case.created_at.isoformat(),
            "company_id": company,
            "product_id": requirement["product_id"],
            # Odoo display name stored with the snapshot; the identity if Odoo gave none.
            "product_label": labels.get(requirement["product_id"], requirement["product_id"]),
            "unit_label": labels.get(requirement["quantity_unit"]),
            "minimum_cost": None if minimum is None else minimum["total_cost"],
            "approved_quantity": requirement["approved_quantity"],
            "quantity_unit": requirement["quantity_unit"],
            "currency": requirement["currency"],
            "required_date": requirement["required_date"],
            "planning_status": snapshot["result"]["status"],
            "decision_status": outcome,
            "source_kind": facts["input_kind"],
            # Same rule as the PDF notice: the history model records where its data came from.
            "data_origin": snapshot["model_manifest"]["metadata"]["data_origin"],
            "scenario_kind": None if scenario is None else scenario["kind"],
            "changed_assumptions": None if scenario is None else _scenario_changes(snapshot),
        }
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as error:
        raise RepositoryError("invalid_library_data", "Saved library data is invalid.") from error


def _scenario_changes(snapshot: dict) -> dict:
    """The scenario's changed demand and supplier fields, checked against its saved request."""
    scenario, request = snapshot["scenario"], snapshot["request"]
    if set(scenario) != {"kind", "source", "suppliers", "approved_quantity"}:
        raise ValueError("Invalid scenario shape.")
    if scenario["kind"] not in SCENARIO_KINDS:
        raise ValueError("Unknown scenario kind.")
    quantity = scenario["approved_quantity"]
    if quantity is not None and (
        type(quantity) is not int or quantity != request["requirement"]["approved_quantity"]
    ):
        raise ValueError("Scenario demand disagrees with saved request.")
    suppliers = {s["supplier_id"]: s for s in request["suppliers"]}
    changed = set()
    for change in scenario["suppliers"]:
        if set(change) != {"supplier_id", "available", "capacity", "unit_price"}:
            raise ValueError("Invalid supplier change shape.")
        identity = change["supplier_id"]
        if identity in changed or identity not in suppliers:
            raise ValueError("Invalid changed supplier identity.")
        changed.add(identity)
        for field in ("available", "capacity", "unit_price"):
            value = change[field]
            if value is None:
                continue
            if (
                (field == "available" and type(value) is not bool)
                or (field == "capacity" and (type(value) is not int or value < 0))
                or (
                    field == "unit_price"
                    and (
                        not isinstance(value, str)
                        or not Decimal(value).is_finite()
                        or Decimal(value) <= 0
                    )
                )
                or value != suppliers[identity][field]
            ):
                raise ValueError("Scenario change disagrees with saved request.")
    return {key: scenario[key] for key in ("approved_quantity", "suppliers")}


def list_planning_cases(uow, query):
    with uow:
        if query.parent_id is not None:
            parent = uow.cases.get(query.parent_id)
            if parent is None or validate_snapshot(parent)["facts"]["company_id"] != query.company:
                raise PlanningCaseError("planning_case_not_found", "Original case not found.")
            if parent.parent_id is not None:
                raise ValueError("Scenarios must be listed under an original base.")
            decision = uow.decisions.get(parent.case_id)
            if decision is not None:
                validate_final_decision(parent, decision)
        rows = uow.cases.list_saved(query)
        summaries = [case_summary(*row, query.company) for row in rows]
        cursor = None
        if len(summaries) > query.limit:
            last = summaries[query.limit - 1]
            cursor = base64.urlsafe_b64encode(
                json.dumps(
                    {
                        "context": query.context,
                        "time": last["created_at"],
                        "id": last["case_id"],
                    }
                ).encode()
            ).decode()
        return {"items": summaries[: query.limit], "next_cursor": cursor}
