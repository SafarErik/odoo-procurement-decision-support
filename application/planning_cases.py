"""T15 controlled composition, immutable scenarios and durable stored-only replay."""

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction
from typing import Protocol, Self
from uuid import UUID, uuid4

from application.decision_cases import RepositoryError
from application.decision_input_assembly import SourceAttribution
from application.planning_catalog import CatalogContext
from application.planning_history import (
    HISTORY_INPUT_KIND,
    capture_features,
)
from application.planning_input import PlanningFacts, assemble_planning_input, validate_source
from application.planning_serialization import (
    json_value,
    read_assessments,
    read_request,
    read_result,
    snapshot_json,
)
from application.procurement_planning import PlanningCommand, create_procurement_plans
from decision_core.planning.models import PlanningStatus
from decision_core.planning.rules import exact_decimal
from supplier_evaluation.contracts import ODOO_HISTORY, utc
from supplier_evaluation.planning_bridge import risk_inputs

SNAPSHOT_VERSION = "t15-controlled-planning-v1"


class PlanningCaseError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class PlanningCase:
    case_id: str
    created_at: datetime
    parent_id: str | None
    idempotency_key: str
    fingerprint: str
    snapshot: str  # Canonical JSON is deeply immutable; readers get a fresh value.

    @property
    def snapshot_hash(self) -> str:
        return hashlib.sha256(self.snapshot.encode()).hexdigest()


class PlanningRepository(Protocol):
    def lock(self, key: str) -> None: ...
    def by_key(self, key: str) -> PlanningCase | None: ...
    def get(self, case_id: str) -> PlanningCase | None: ...
    def add(self, case: PlanningCase) -> None: ...
    def list_saved(self, query) -> list[tuple]: ...
    def add_catalog(self, case_id: str, context: CatalogContext) -> None: ...
    def catalog_for(self, case_id: str) -> CatalogContext | None: ...


class PlanningUnitOfWork(Protocol):
    cases: PlanningRepository

    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type, exc, traceback) -> None: ...
    def commit(self) -> None: ...


@dataclass(frozen=True, slots=True)
class SupplierChange:
    supplier_id: str
    available: bool | None = None
    capacity: int | None = None
    unit_price: Decimal | None = None


@dataclass(frozen=True, slots=True)
class ScenarioDelta:
    kind: str
    source: SourceAttribution
    suppliers: tuple[SupplierChange, ...] = ()
    approved_quantity: int | None = None


def canonical_uuid(value: str) -> str:
    try:
        if str(UUID(value)) == value:
            return value
    except (ValueError, TypeError, AttributeError):
        pass
    raise PlanningCaseError("invalid_identity", "Supply a canonical UUID.")


def fingerprint(intent) -> str:
    return hashlib.sha256(snapshot_json(intent).encode()).hexdigest()


def normalize_planning_facts(facts):
    return replace(
        facts,
        policy=replace(facts.policy, epsilons=tuple(sorted(set(facts.policy.epsilons)))),
        suppliers=tuple(
            replace(s, receipts=tuple(sorted(s.receipts, key=lambda r: r.line_id)))
            for s in sorted(facts.suppliers, key=lambda s: s.terms.supplier_id)
        ),
    )


def validate_snapshot(case: PlanningCase) -> dict:
    """Decode stored contracts only; never infer, solve or read a model/upstream."""
    try:
        value = json.loads(case.snapshot)
        if set(value) != {
            "snapshot_version",
            "facts",
            "request",
            "assessments",
            "model_manifest",
            "risk_context",
            "solver",
            "result",
            "scenario",
            "comparison",
            "provenance",
        }:
            raise ValueError("Unknown snapshot shape.")
        if value["snapshot_version"] != SNAPSHOT_VERSION:
            raise ValueError("Unsupported snapshot version.")
        if (
            value["facts"].get("input_kind") != HISTORY_INPUT_KIND
            and value["facts"]["source_type"] != "t14_synthetic"
        ):
            raise ValueError("Legacy snapshots require their original synthetic source.")
        request = read_request(value["request"])
        assessments = read_assessments(value["assessments"])
        if {a.snapshot.context.supplier_id for a in assessments} != {
            s.supplier_id for s in request.suppliers
        }:
            raise ValueError("Incomplete stored assessments.")
        metadata = value["model_manifest"]["metadata"]
        if value["facts"].get("input_kind") == HISTORY_INPUT_KIND:
            from supplier_evaluation.qualified_odoo import qualification_metadata

            manifest = value["model_manifest"]
            facts = value["facts"]
            captured = capture_features(facts["history"])
            if (
                facts["source_type"] != ODOO_HISTORY
                or facts["input_kind"] != HISTORY_INPUT_KIND
                or metadata
                != qualification_metadata(
                    manifest["candidate_manifest"], manifest["compatibility_report"]
                )
                or metadata["domain"] != list(captured[0].context.domain)
                or manifest["artifact_sha256"] != manifest["candidate_manifest"]["artifact_sha256"]
                or snapshot_json(sorted(captured, key=lambda f: f.context.supplier_id))
                != snapshot_json(
                    [
                        a.snapshot
                        for a in sorted(assessments, key=lambda a: a.snapshot.context.supplier_id)
                    ]
                )
            ):
                raise ValueError("Stored Odoo source/model compatibility mismatch.")
        if re.fullmatch(r"[0-9a-f]{64}", value["model_manifest"]["artifact_sha256"]) is None:
            raise ValueError("Missing stored artifact hash.")
        if any(
            (a.model_id, a.training_id) != (metadata["model_id"], metadata["training_id"])
            for a in assessments
        ):
            raise ValueError("Stored model identity mismatch.")
        if not value["risk_context"]["controlled_fixture"] or not value["solver"]:
            raise ValueError("Missing controlled runtime evidence.")
        result = read_result(value["result"])
        for plan in (
            ()
            if result.minimum_cost_plan is None
            else (result.minimum_cost_plan, *result.alternatives)
        ):
            if (
                tuple(a.supplier_id for a in plan.allocations)
                != tuple(sorted(s.supplier_id for s in request.suppliers))
                or sum(a.quantity for a in plan.allocations)
                != request.requirement.approved_quantity
            ):
                raise ValueError("Invalid recorded allocation join or demand.")
        if (case.parent_id is None) != (value["scenario"] is None):
            raise ValueError("Invalid stored scenario lineage.")
        canonical_uuid(case.case_id)
        canonical_uuid(case.idempotency_key)
        utc(case.created_at)
        if re.fullmatch(r"[0-9a-f]{64}", case.fingerprint) is None:
            raise ValueError("Invalid stored caller fingerprint.")
        if case.parent_id is not None:
            canonical_uuid(case.parent_id)
        return value
    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        ArithmeticError,
    ) as error:
        raise RepositoryError(
            "invalid_persisted_case", "The stored planning snapshot is invalid."
        ) from error


def get_planning_case(uow: PlanningUnitOfWork, case_id: str) -> PlanningCase:
    canonical_uuid(case_id)
    with uow:
        case = uow.cases.get(case_id)
        if case is None:
            raise PlanningCaseError("planning_case_not_found", "The planning case does not exist.")
        validate_snapshot(case)
        return case


def _scenario_request(base: dict, delta: ScenarioDelta):
    request = read_request(base["request"])
    as_of = datetime.fromisoformat(base["facts"]["as_of"])
    validate_source(delta.source, "scenario_delta", as_of)
    if delta.kind not in {
        "supplier_outage",
        "capacity_reduction",
        "demand_increase",
        "price_increase",
        "combined",
    }:
        raise ValueError("Unsupported scenario kind.")
    changes = {s.supplier_id: s for s in delta.suppliers}
    if len(changes) != len(delta.suppliers) or set(changes) - {
        s.supplier_id for s in request.suppliers
    }:
        raise ValueError("Duplicate or unknown scenario supplier.")
    kinds, suppliers = set(), []
    for terms in request.suppliers:
        change = changes.get(terms.supplier_id)
        if change is None:
            suppliers.append(terms)
            continue
        replacements = {}
        if change.available is not None:
            if change.available is not False or not terms.available:
                raise ValueError("Outage must remove an available supplier.")
            replacements["available"] = False
            kinds.add("supplier_outage")
        if change.capacity is not None:
            if type(change.capacity) is not int or not 0 <= change.capacity < terms.capacity:
                raise ValueError("Capacity must be strictly reduced.")
            replacements["capacity"] = change.capacity
            kinds.add("capacity_reduction")
        if change.unit_price is not None:
            if (
                not isinstance(change.unit_price, Decimal)
                or not change.unit_price.is_finite()
                or change.unit_price <= terms.unit_price
            ):
                raise ValueError("Price must be strictly increased.")
            replacements["unit_price"] = change.unit_price
            kinds.add("price_increase")
        if not replacements:
            raise ValueError("Empty supplier disturbance.")
        suppliers.append(replace(terms, **replacements))
    requirement = request.requirement
    if delta.approved_quantity is not None:
        if (
            type(delta.approved_quantity) is not int
            or delta.approved_quantity <= requirement.approved_quantity
        ):
            raise ValueError("Scenario demand must be strictly increased.")
        requirement = replace(requirement, approved_quantity=delta.approved_quantity)
        kinds.add("demand_increase")
    if (delta.kind == "combined" and len(kinds) < 2) or (
        delta.kind != "combined" and kinds != {delta.kind}
    ):
        raise ValueError("Scenario kind must match its explicit disturbances.")
    return replace(
        request, requirement=requirement, suppliers=tuple(suppliers), risk_coefficients=None
    ), as_of


def _comparison(base: dict, result: dict) -> dict:
    left, right = base["result"]["minimum_cost_plan"], result["minimum_cost_plan"]
    comparison = {
        "base_status": base["result"]["status"],
        "scenario_status": result["status"],
        "minimum_cost": None,
        "meaning": "Total cost across explicit demand; not a like-for-like saving claim.",
    }
    if left is not None and right is not None:

        def fraction(value):
            return Fraction(value["numerator"], value["denominator"])

        comparison["minimum_cost"] = json_value(
            {
                "total_cost_delta": exact_decimal(
                    Fraction(Decimal(right["total_cost"])) - Fraction(Decimal(left["total_cost"]))
                ),
                "risk_exposure_delta": fraction(right["risk_exposure"])
                - fraction(left["risk_exposure"]),
                "base_allocations": left["allocations"],
                "scenario_allocations": right["allocations"],
            }
        )
    return comparison


def _scenario_provenance(base: dict, delta: ScenarioDelta) -> dict:
    paths = {}
    if delta.approved_quantity is not None:
        paths["request.requirement.approved_quantity"] = "approved_quantity"
    for change in delta.suppliers:
        for field in ("available", "capacity", "unit_price"):
            if getattr(change, field) is not None:
                paths[f"request.suppliers[{change.supplier_id}].{field}"] = field
    entries = [
        entry for entry in base["provenance"]["entries"] if entry["canonical_path"] not in paths
    ]
    entries.extend(
        {
            "canonical_path": path,
            "field_name": field,
            "source_type": delta.source.source_type,
            "source_reference": delta.source.source_reference,
            "observed_at": json_value(delta.source.observed_at),
        }
        for path, field in sorted(paths.items())
    )
    return {"entries": entries}


def create_planning_case(
    uow: PlanningUnitOfWork,
    key: str,
    *,
    facts: PlanningFacts | None = None,
    parent_id: str | None = None,
    delta: ScenarioDelta | None = None,
    infer: Callable,
    solver_factory: Callable,
    base_intent: dict | None = None,
    load_base: Callable | None = None,
    catalog_context: CatalogContext | None = None,
    base_kind: str = "odoo_quotations_synthetic_history",
) -> tuple[PlanningCase, bool]:
    """One locked transaction contains computation and immutable key/case insertion."""
    canonical_uuid(key)
    loaded_base = base_intent is not None and load_base is not None
    if base_kind not in {"odoo_quotations_synthetic_history", HISTORY_INPUT_KIND}:
        raise ValueError("Unsupported creation path.")
    if catalog_context is not None:
        if parent_id is not None or not isinstance(catalog_context, CatalogContext):
            raise ValueError("Only base creation accepts catalog context.")
        catalog_context.validate(from_odoo=loaded_base)
    if (
        sum((facts is not None, parent_id is not None, loaded_base)) != 1
        or (base_intent is None) != (load_base is None)
        or (parent_id is None) != (delta is None)
    ):
        raise PlanningCaseError("invalid_planning_input", "Supply a base input or one scenario.")
    if parent_id is not None:
        canonical_uuid(parent_id)
        intent = {
            "operation": "scenario",
            "parent_id": parent_id,
            "delta": replace(
                delta, suppliers=tuple(sorted(delta.suppliers, key=lambda s: s.supplier_id))
            ),
        }
    elif loaded_base:
        intent = {"operation": base_kind, "input": base_intent}
    else:
        normalized = normalize_planning_facts(facts)
        intent = {"operation": "base", "facts": normalized}
    if catalog_context is not None:
        intent["catalog_context"] = catalog_context
    request_hash = fingerprint(intent)
    with uow:
        uow.cases.lock(key)
        previous = uow.cases.by_key(key)
        if previous is not None:
            if previous.fingerprint != request_hash:
                raise PlanningCaseError(
                    "idempotency_key_conflict", "The key belongs to different caller intent."
                )
            validate_snapshot(previous)
            return previous, True
        try:
            base = None
            if parent_id is None:
                extra_provenance = None
                if loaded_base:
                    normalized, extra_provenance = load_base()
                request, features, provenance = assemble_planning_input(normalized)
                if extra_provenance is not None:
                    overrides = {e.canonical_path: e for e in extra_provenance.entries}
                    if len(overrides) != len(extra_provenance.entries):
                        raise ValueError("Duplicate prepared provenance paths.")
                    entries = {e.canonical_path: e for e in provenance.entries}
                    entries.update(overrides)
                    provenance = type(provenance)(tuple(entries[k] for k in sorted(entries)))
                assessments, manifest = infer(features)
                as_of, company = normalized.as_of, normalized.company_id
                snapshot = {
                    "facts": json_value(normalized),
                    "model_manifest": manifest,
                    "provenance": json_value(provenance),
                }
                if loaded_base:
                    snapshot["facts"]["input_kind"] = base_kind
                    snapshot["facts"]["comparison_case_id"] = (
                        f"odoo:purchase.order.group:{base_intent['purchase_group_id']}"
                    )
            else:
                parent = uow.cases.get(parent_id)
                if parent is None:
                    raise PlanningCaseError(
                        "planning_case_not_found", "The base planning case does not exist."
                    )
                if parent.parent_id is not None:
                    raise ValueError("This slice creates scenarios from a base case only.")
                base = validate_snapshot(parent)
                request, as_of = _scenario_request(base, delta)
                company = base["facts"]["company_id"]
                assessments = read_assessments(base["assessments"])
                snapshot = {
                    "facts": base["facts"],
                    "model_manifest": base["model_manifest"],
                    "provenance": _scenario_provenance(base, delta),
                }
            coefficients, context = risk_inputs(
                request, assessments, company_id=company, as_of=as_of
            )
            request = replace(request, risk_coefficients=coefficients)
            solver, evidence = solver_factory()
            result = create_procurement_plans(PlanningCommand(request, context), solver)
            if result.status is PlanningStatus.INVALID_INPUT:
                raise ValueError(
                    "The planning input violates the supported numerical/business contract."
                )
            encoded_result = json_value(result)
            snapshot.update(
                snapshot_version=SNAPSHOT_VERSION,
                request=json_value(request),
                assessments=json_value(assessments),
                risk_context=json_value(context),
                solver=evidence,
                result=encoded_result,
                scenario=json_value(delta),
                comparison=None if base is None else _comparison(base, encoded_result),
            )
            case = PlanningCase(
                str(uuid4()),
                datetime.now(UTC),
                parent_id,
                key,
                request_hash,
                snapshot_json(snapshot),
            )
            validate_snapshot(case)
            uow.cases.add(case)
            if catalog_context is not None:
                uow.cases.add_catalog(case.case_id, catalog_context)
            uow.commit()
            return case, False
        except (ValueError, TypeError, OverflowError) as error:
            if isinstance(error, PlanningCaseError):
                raise
            raise PlanningCaseError(
                "invalid_planning_input", "Controlled input, evidence or validity is incompatible."
            ) from error
