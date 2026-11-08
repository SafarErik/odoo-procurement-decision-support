"""Odoo-history base cases, immutable scenarios and durable stored-only replay."""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction
from typing import Protocol, Self
from uuid import UUID, uuid4

from application.errors import PlanningCaseError, RepositoryError
from application.planning_history import capture_features, capture_origin
from application.planning_input import assemble_planning_input, validate_source
from application.planning_serialization import (
    is_sha256_hex,
    json_value,
    read_assessments,
    read_fraction,
    read_request,
    read_result,
    snapshot_json,
)
from application.procurement_planning import (
    PlanningCommand,
    create_procurement_plans,
    risk_inputs,
)
from application.provenance import SourceAttribution
from application.stored_contracts import HISTORY_INPUT_KIND, SNAPSHOT_VERSION
from decision_core.planning.models import PlanningRequest, PlanningStatus
from decision_core.planning.rules import exact_decimal
from supplier_evaluation.contracts import HISTORY_SOURCE, utc


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
    """Decode and cross-check a stored case; never infer, solve or read a model or Odoo.

    Returns the decoded snapshot. Anything unreadable or inconsistent raises
    ``RepositoryError("invalid_persisted_case")`` (HTTP 503) instead of showing it.
    """
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
        request = read_request(value["request"])
        assessments = read_assessments(value["assessments"])
        if {a.snapshot.context.supplier_id for a in assessments} != {
            s.supplier_id for s in request.suppliers
        }:
            raise ValueError("Incomplete stored assessments.")
        _check_model_evidence(value, assessments)
        _check_recorded_plans(value, request)
        _check_case_row(case, value)
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


def _check_model_evidence(value: dict, assessments) -> None:
    """The model metadata, the captured Odoo history and every assessment belong together."""
    # The model module owns its metadata contract; importing it loads scikit-learn,
    # so it is imported only when a stored snapshot is actually checked.
    from supplier_evaluation.history_model import check_manifest_metadata

    metadata, facts = value["model_manifest"]["metadata"], value["facts"]
    check_manifest_metadata(metadata)
    captured = capture_features(facts["history"])
    if (
        metadata["data_origin"] != capture_origin(facts["history"])
        or facts["source_type"] != HISTORY_SOURCE
        or facts["input_kind"] != HISTORY_INPUT_KIND
        or metadata["company_id"] != facts["company_id"]
        or snapshot_json(sorted(captured, key=lambda f: f.context.supplier_id))
        != snapshot_json(
            [a.snapshot for a in sorted(assessments, key=lambda a: a.snapshot.context.supplier_id)]
        )
    ):
        raise ValueError("Stored Odoo source/model compatibility mismatch.")
    if not is_sha256_hex(value["model_manifest"]["artifact_sha256"]):
        raise ValueError("Missing stored artifact hash.")
    if any(
        (a.model_id, a.training_id) != (metadata["model_id"], metadata["training_id"])
        for a in assessments
    ):
        raise ValueError("Stored model identity mismatch.")
    if not value["risk_context"]["controlled_fixture"] or not value["solver"]:
        raise ValueError("Missing controlled runtime evidence.")


def _check_recorded_plans(value: dict, request) -> None:
    """Every recorded plan lists each supplier once, in id order, and meets the demand."""
    result = read_result(value["result"])
    plans = (
        () if result.minimum_cost_plan is None else (result.minimum_cost_plan, *result.alternatives)
    )
    for plan in plans:
        if (
            tuple(a.supplier_id for a in plan.allocations)
            != tuple(sorted(s.supplier_id for s in request.suppliers))
            or sum(a.quantity for a in plan.allocations) != request.requirement.approved_quantity
        ):
            raise ValueError("Invalid recorded allocation join or demand.")


def _check_case_row(case: PlanningCase, value: dict) -> None:
    """Row identities are canonical and only a scenario has a parent and a scenario delta."""
    if (case.parent_id is None) != (value["scenario"] is None):
        raise ValueError("Invalid stored scenario lineage.")
    canonical_uuid(case.case_id)
    canonical_uuid(case.idempotency_key)
    utc(case.created_at)
    if not is_sha256_hex(case.fingerprint):
        raise ValueError("Invalid stored caller fingerprint.")
    if case.parent_id is not None:
        canonical_uuid(case.parent_id)


def get_planning_case(uow: PlanningUnitOfWork, case_id: str) -> PlanningCase:
    canonical_uuid(case_id)
    with uow:
        case = uow.cases.get(case_id)
        if case is None:
            raise PlanningCaseError("planning_case_not_found", "The planning case does not exist.")
        validate_snapshot(case)
        return case


# Order is the order the API lists them in validation errors.
SCENARIO_KINDS = ("supplier_outage", "capacity_change", "demand_change", "price_change", "combined")


def _scenario_request(base: dict, delta: ScenarioDelta):
    """Apply explicit what-if changes; capacity, demand and price may move either way."""
    request = read_request(base["request"])
    as_of = datetime.fromisoformat(base["facts"]["as_of"])
    validate_source(delta.source, "scenario_delta", as_of)
    if delta.kind not in SCENARIO_KINDS:
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
            if (
                type(change.capacity) is not int
                or change.capacity < 0
                or change.capacity == terms.capacity
            ):
                raise ValueError("Capacity must change to a different non-negative integer.")
            replacements["capacity"] = change.capacity
            kinds.add("capacity_change")
        if change.unit_price is not None:
            if (
                not isinstance(change.unit_price, Decimal)
                or not change.unit_price.is_finite()
                or change.unit_price <= 0
                or change.unit_price == terms.unit_price
            ):
                raise ValueError("Price must change to a different positive decimal.")
            replacements["unit_price"] = change.unit_price
            kinds.add("price_change")
        if not replacements:
            raise ValueError("Empty supplier disturbance.")
        suppliers.append(replace(terms, **replacements))
    requirement = request.requirement
    if delta.approved_quantity is not None:
        if (
            type(delta.approved_quantity) is not int
            or delta.approved_quantity < 1
            or delta.approved_quantity == requirement.approved_quantity
        ):
            raise ValueError("Scenario demand must change to a different positive integer.")
        requirement = replace(requirement, approved_quantity=delta.approved_quantity)
        kinds.add("demand_change")
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
        comparison["minimum_cost"] = json_value(
            {
                "total_cost_delta": exact_decimal(
                    Fraction(Decimal(right["total_cost"])) - Fraction(Decimal(left["total_cost"]))
                ),
                "risk_exposure_delta": read_fraction(right["risk_exposure"])
                - read_fraction(left["risk_exposure"]),
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
    parent_id: str | None = None,
    delta: ScenarioDelta | None = None,
    infer: Callable,
    solver_factory: Callable,
    base_intent: dict | None = None,
    load_base: Callable | None = None,
) -> tuple[PlanningCase, bool]:
    """Create a base case or a scenario in one locked transaction; return (case, replayed).

    A base comes from an Odoo quotation group with Odoo purchase history (``load_base``,
    called only when the key is new); a scenario applies ``delta`` to a stored base
    ``parent_id`` and reuses its saved assessments. Repeating a key with the same request
    returns the stored case unchanged (``replayed`` True) without reading Odoo, scoring
    or solving again; the same key with a different request is a conflict.
    """
    canonical_uuid(key)
    loaded_base = base_intent is not None and load_base is not None
    if (
        (parent_id is not None) == loaded_base
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
    else:
        intent = {"operation": HISTORY_INPUT_KIND, "input": base_intent}
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
            if parent_id is None:
                inputs = _base_inputs(load_base, infer, base_intent)
            else:
                inputs = _scenario_inputs(uow, parent_id, delta)
            snapshot = _planned_snapshot(inputs, delta, solver_factory)
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
            uow.commit()
            return case, False
        except (ValueError, TypeError, OverflowError) as error:
            if isinstance(error, PlanningCaseError):
                raise
            raise PlanningCaseError(
                "invalid_planning_input", "Controlled input, evidence or validity is incompatible."
            ) from error


@dataclass(frozen=True, slots=True)
class _CaseInputs:
    """What a new case plans from; ``base`` is the parent snapshot of a scenario."""

    request: PlanningRequest
    assessments: tuple
    as_of: datetime
    company_id: str
    snapshot: dict  # facts, model_manifest and provenance so far
    base: dict | None


def _base_inputs(load_base: Callable, infer: Callable, base_intent: dict) -> _CaseInputs:
    """Read Odoo (via ``load_base``), assemble the request and score every supplier."""
    normalized, extra_provenance = load_base()
    request, features, provenance = assemble_planning_input(normalized)
    if extra_provenance is not None:
        # Field sources recorded while binding the Odoo quotations replace the generic ones.
        overrides = {e.canonical_path: e for e in extra_provenance.entries}
        if len(overrides) != len(extra_provenance.entries):
            raise ValueError("Duplicate prepared provenance paths.")
        entries = {e.canonical_path: e for e in provenance.entries}
        entries.update(overrides)
        provenance = type(provenance)(tuple(entries[k] for k in sorted(entries)))
    assessments, manifest = infer(features)
    snapshot = {
        "facts": json_value(normalized),
        "model_manifest": manifest,
        "provenance": json_value(provenance),
    }
    snapshot["facts"]["input_kind"] = HISTORY_INPUT_KIND
    snapshot["facts"]["comparison_case_id"] = (
        f"odoo:purchase.order.group:{base_intent['purchase_group_id']}"
    )
    return _CaseInputs(
        request, assessments, normalized.as_of, normalized.company_id, snapshot, None
    )


def _scenario_inputs(uow, parent_id: str, delta: ScenarioDelta) -> _CaseInputs:
    """Load the stored base, apply the changes and reuse its saved assessments."""
    parent = uow.cases.get(parent_id)
    if parent is None:
        raise PlanningCaseError("planning_case_not_found", "The base planning case does not exist.")
    if parent.parent_id is not None:
        raise ValueError("This slice creates scenarios from a base case only.")
    base = validate_snapshot(parent)
    request, as_of = _scenario_request(base, delta)
    snapshot = {
        "facts": base["facts"],
        "model_manifest": base["model_manifest"],
        "provenance": _scenario_provenance(base, delta),
    }
    return _CaseInputs(
        request,
        read_assessments(base["assessments"]),
        as_of,
        base["facts"]["company_id"],
        snapshot,
        base,
    )


def _planned_snapshot(inputs: _CaseInputs, delta, solver_factory: Callable) -> dict:
    """Attach risk coefficients, run the MILP and complete the snapshot to be stored."""
    coefficients, context = risk_inputs(
        inputs.request, inputs.assessments, company_id=inputs.company_id, as_of=inputs.as_of
    )
    request = replace(inputs.request, risk_coefficients=coefficients)
    solver, evidence = solver_factory()
    result = create_procurement_plans(PlanningCommand(request, context), solver)
    if result.status is PlanningStatus.INVALID_INPUT:
        raise ValueError("The planning input violates the supported numerical/business contract.")
    encoded_result = json_value(result)
    return inputs.snapshot | {
        "snapshot_version": SNAPSHOT_VERSION,
        "request": json_value(request),
        "assessments": json_value(inputs.assessments),
        "risk_context": json_value(context),
        "solver": evidence,
        "result": encoded_result,
        "scenario": json_value(delta),
        "comparison": None if inputs.base is None else _comparison(inputs.base, encoded_result),
    }
