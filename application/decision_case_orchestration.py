"""T12 coordination of bounded reads, evaluation, and atomic case creation."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol, Self
from uuid import UUID, uuid4

from application.decision_cases import (
    SNAPSHOT_VERSION,
    DecisionCase,
    DecisionCaseError,
    DecisionCaseRepository,
    RepositoryError,
    _validate_evaluation_consistency,
)
from application.decision_input_assembly import (
    DecisionInputAssemblyError,
    OdooComparisonCaseFacts,
    SourceAttribution,
    SupplementalOfferTerms,
    SupplementalValue,
    assemble_decision_input,
    attach_historical_performance,
)
from application.decisions import (
    evaluate_procurement_decision,
    evaluate_procurement_decision_with_history,
)
from application.historical_performance import (
    MAX_HISTORY_RESULTS,
    OBSERVATION_WINDOW,
    HistoricalPerformanceError,
    HistoricalPerformancePort,
    HistoricalPerformanceQuery,
    acquire_historical_performance,
)
from application.rfqs import ProcurementDataResponseError, ProcurementDataUnavailable
from decision_core import DomainValidationError, HistoricalScoringProfile, StrategicProfile

_LINE_ID = re.compile(r"odoo:purchase\.order\.line:[1-9][0-9]*\Z")
_SUPPLIER_ID = re.compile(r"odoo:res\.partner:[1-9][0-9]*\Z")


class OrchestrationError(ValueError):
    """Stable, safe application error for T12 callers."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class SupplierHistorySelection:
    supplier_id: str
    purchase_line_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HistorySelection:
    window_end: datetime
    suppliers: tuple[SupplierHistorySelection, ...]


@dataclass(frozen=True, slots=True)
class CreateDecisionCaseCommand:
    purchase_group_id: int
    supplemental_terms: tuple[SupplementalOfferTerms, ...]
    scoring_policy_id: str
    history_selection: HistorySelection | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class DecisionCaseCreationResult:
    decision_case: DecisionCase
    replayed: bool


class ComparisonCaseReader(Protocol):
    async def read_comparison_case(self, purchase_group_id: int) -> OdooComparisonCaseFacts: ...


class CreationRepository(Protocol):
    def lock(self, key: str) -> None: ...
    def get(self, key: str) -> tuple[str, str] | None: ...
    def add(self, key: str, fingerprint: str, case_id: str) -> None: ...


class CreationUnitOfWork(Protocol):
    cases: DecisionCaseRepository
    creations: CreationRepository

    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...
    def commit(self) -> None: ...


def resolve_policy(policy_id: str) -> StrategicProfile | HistoricalScoringProfile:
    factories = {
        "cost-focused": StrategicProfile.cost_focused,
        "urgent": StrategicProfile.urgent,
        "balanced": StrategicProfile.balanced,
        "cost_focused_history_v1": HistoricalScoringProfile.cost_focused_history_v1,
        "urgent_history_v1": HistoricalScoringProfile.urgent_history_v1,
        "risk_averse_history_v1": HistoricalScoringProfile.risk_averse_history_v1,
    }
    if policy_id not in factories:
        raise OrchestrationError("unsupported_scoring_policy", "The scoring policy is unsupported.")
    return factories[policy_id]()


def _utc(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise OrchestrationError("invalid_timestamp", "An explicit UTC timestamp is required.")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decimal(value: Decimal) -> str:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise OrchestrationError("invalid_supplemental_value", "A finite decimal is required.")
    return format(value.normalize(), "f")


def _uuid(value: str) -> None:
    try:
        if str(UUID(value)) != value:
            raise ValueError
    except (ValueError, TypeError, AttributeError) as error:
        raise OrchestrationError(
            "invalid_idempotency_key", "A canonical UUID key is required."
        ) from error


def request_fingerprint(command: CreateDecisionCaseCommand) -> str:
    """Hash only normalized caller intent, before any live data read."""
    _uuid(command.idempotency_key)
    if (
        isinstance(command.purchase_group_id, bool)
        or not isinstance(command.purchase_group_id, int)
        or command.purchase_group_id <= 0
    ):
        raise OrchestrationError(
            "invalid_comparison_selection", "A positive purchase_group_id is required."
        )
    resolve_policy(command.scoring_policy_id)
    terms = []
    seen = set()
    for item in command.supplemental_terms:
        if not isinstance(item, SupplementalOfferTerms):
            raise OrchestrationError(
                "invalid_supplemental_mapping", "Supplemental offer terms must be typed."
            )
        if not isinstance(item.offer_id, str) or not item.offer_id.strip() or item.offer_id in seen:
            raise OrchestrationError(
                "invalid_supplemental_mapping", "Offer identities must be unique and non-empty."
            )
        seen.add(item.offer_id)
        values = []
        for supplied, expected in (
            (item.hard_minimum_order_quantity, "minimum_order_quantity"),
            (item.supplier_promised_lead_time_days, "lead_time_days"),
        ):
            if not isinstance(supplied, SupplementalValue):
                raise OrchestrationError(
                    "invalid_supplemental_mapping", "Every offer requires both supplied values."
                )
            attribution = supplied.attribution
            if (
                not isinstance(attribution, SourceAttribution)
                or attribution.field_name != expected
                or not attribution.source_type.strip()
                or not attribution.source_reference.strip()
            ):
                raise OrchestrationError(
                    "invalid_source_attribution", "Supplemental source attribution is invalid."
                )
            values.append(
                {
                    "value": _decimal(supplied.value),
                    "source_type": attribution.source_type,
                    "source_reference": attribution.source_reference,
                    "observed_at": _utc(attribution.observed_at),
                }
            )
        terms.append({"offer_id": item.offer_id, "moq": values[0], "lead_time": values[1]})
    if not terms:
        raise OrchestrationError(
            "invalid_supplemental_mapping", "Supplemental offer terms are required."
        )
    history = None
    if command.history_selection is not None:
        selection = command.history_selection
        if not isinstance(selection, HistorySelection):
            raise OrchestrationError(
                "invalid_history_selection", "History selection must be typed."
            )
        suppliers = []
        seen_suppliers = set()
        seen_lines = set()
        for item in selection.suppliers:
            if (
                not isinstance(item, SupplierHistorySelection)
                or not isinstance(item.supplier_id, str)
                or not _SUPPLIER_ID.fullmatch(item.supplier_id)
                or item.supplier_id in seen_suppliers
            ):
                raise OrchestrationError(
                    "invalid_history_selection",
                    "History supplier identities must be unique and stable.",
                )
            seen_suppliers.add(item.supplier_id)
            if (
                not item.purchase_line_ids
                or len(set(item.purchase_line_ids)) != len(item.purchase_line_ids)
                or any(
                    not isinstance(line, str) or not _LINE_ID.fullmatch(line)
                    for line in item.purchase_line_ids
                )
            ):
                raise OrchestrationError(
                    "invalid_history_selection",
                    "Exact unique Odoo purchase-line identities are required.",
                )
            if seen_lines.intersection(item.purchase_line_ids):
                raise OrchestrationError(
                    "invalid_history_selection", "Purchase-line identities cannot span suppliers."
                )
            seen_lines.update(item.purchase_line_ids)
            suppliers.append(
                {
                    "supplier_id": item.supplier_id,
                    "purchase_line_ids": sorted(item.purchase_line_ids),
                }
            )
        if not suppliers:
            raise OrchestrationError(
                "invalid_history_selection", "History supplier selections are required."
            )
        history = {
            "window_end": _utc(selection.window_end),
            "suppliers": sorted(suppliers, key=lambda item: item["supplier_id"]),
        }
    payload = {
        "purchase_group_id": command.purchase_group_id,
        "scoring_policy_id": command.scoring_policy_id,
        "supplemental_terms": sorted(terms, key=lambda item: item["offer_id"]),
        "history_selection": history,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


async def create_decision_case(
    command: CreateDecisionCaseCommand,
    *,
    comparison_reader: ComparisonCaseReader,
    history_reader: HistoricalPerformancePort,
    unit_of_work: CreationUnitOfWork,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    new_id: Callable[[], str] = lambda: str(uuid4()),
) -> DecisionCaseCreationResult:
    fingerprint = request_fingerprint(command)
    policy = resolve_policy(command.scoring_policy_id)
    try:
        with unit_of_work:
            unit_of_work.creations.lock(command.idempotency_key)
            existing = unit_of_work.creations.get(command.idempotency_key)
            if existing is not None:
                prior_fingerprint, prior_case_id = existing
                if prior_fingerprint != fingerprint:
                    raise OrchestrationError(
                        "creation_idempotency_conflict",
                        "The key was used with a different request.",
                    )
                prior = unit_of_work.cases.get(prior_case_id)
                if prior is None:
                    raise OrchestrationError(
                        "decision_case_persistence_failed", "The recorded case is unavailable."
                    )
                return DecisionCaseCreationResult(prior, True)
            facts = await comparison_reader.read_comparison_case(command.purchase_group_id)
            if facts.comparison_case_id != f"odoo:purchase.order.group:{command.purchase_group_id}":
                raise OrchestrationError(
                    "invalid_comparison_response",
                    "The comparison identity differs from the selection.",
                )
            created_at = clock()
            if (
                created_at.tzinfo is None
                or created_at.utcoffset() is None
                or created_at.utcoffset().total_seconds() != 0
            ):
                raise OrchestrationError("invalid_timestamp", "The server clock must return UTC.")
            fallback = (
                policy.fallback_profile if isinstance(policy, HistoricalScoringProfile) else policy
            )
            assembled = assemble_decision_input(
                facts,
                command.supplemental_terms,
                fallback,
                SourceAttribution(
                    "strategic_profile", "application_policy", command.scoring_policy_id, created_at
                ),
            )
            if command.history_selection is not None:
                selected = command.history_selection
                supplier_ids = {offer.supplier_id for offer in assembled.canonical.offers}
                if {item.supplier_id for item in selected.suppliers} != supplier_ids:
                    raise OrchestrationError(
                        "invalid_history_selection",
                        "History must select every comparison supplier exactly once.",
                    )
                company_ids = {offer.company_id for offer in facts.offers}
                if len(company_ids) != 1:
                    raise OrchestrationError(
                        "invalid_comparison_response", "Comparison companies differ."
                    )
                end = selected.window_end.astimezone(UTC)
                queries = tuple(
                    HistoricalPerformanceQuery(
                        item.supplier_id,
                        next(iter(company_ids)),
                        item.purchase_line_ids,
                        end - OBSERVATION_WINDOW,
                        end,
                        MAX_HISTORY_RESULTS,
                    )
                    for item in selected.suppliers
                )
                history = await acquire_historical_performance(history_reader, queries)
                assembled = attach_historical_performance(assembled, history)
            canonical = assembled.canonical
            evaluation = (
                evaluate_procurement_decision_with_history(canonical, policy)
                if isinstance(policy, HistoricalScoringProfile)
                else evaluate_procurement_decision(canonical.requirement, canonical.offers, policy)
            )
            decision_case = DecisionCase(
                new_id(), SNAPSHOT_VERSION, created_at, assembled, policy, evaluation
            )
            _validate_evaluation_consistency(decision_case)
            unit_of_work.cases.add(decision_case)
            unit_of_work.creations.add(
                command.idempotency_key, fingerprint, decision_case.decision_case_id
            )
            unit_of_work.commit()
            return DecisionCaseCreationResult(decision_case, False)
    except (OrchestrationError, DecisionCaseError):
        raise
    except ProcurementDataUnavailable as error:
        raise OrchestrationError("odoo_unavailable", "Odoo data is unavailable.") from error
    except ProcurementDataResponseError as error:
        raise OrchestrationError("odoo_response_error", "Odoo returned invalid data.") from error
    except RepositoryError as error:
        raise OrchestrationError(
            "decision_case_persistence_failed", "Decision persistence is unavailable."
        ) from error
    except (DecisionInputAssemblyError, HistoricalPerformanceError, DomainValidationError) as error:
        raise OrchestrationError(
            getattr(error, "code", "invalid_decision_input"), "Decision input is invalid."
        ) from error
