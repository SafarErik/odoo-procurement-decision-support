"""Planning facts and field attribution; no live ERP access or ML loading."""

from dataclasses import asdict, dataclass
from datetime import datetime

from application.planning_history import capture_features
from application.provenance import FieldProvenance, ProvenanceManifest, SourceAttribution
from application.stored_contracts import SCORE_QUANTITIES_REFERENCE
from decision_core.planning.models import (
    PlanningPolicy,
    PlanningRequest,
    ProcurementRequirement,
    SupplierTerms,
)
from supplier_evaluation.contracts import (
    HISTORY_SOURCE,
    Context,
    LineEvidence,
    QuantityValidity,
    text_identity,
    utc,
)

MAX_SUPPLIERS = 10
MAX_EPSILONS = 3
# Order quantities every supplier assessment is declared valid for: a controlled proxy,
# not evidence that the score holds at every quantity.
SCORE_QUANTITIES = QuantityValidity(1, 1000, SCORE_QUANTITIES_REFERENCE)


def validate_source(source: SourceAttribution, field: str, as_of: datetime) -> None:
    if not isinstance(source, SourceAttribution) or source.field_name != field:
        raise ValueError("Explicit field attribution required.")
    text_identity(source.source_type)
    text_identity(source.source_reference)
    utc(source.observed_at)
    if source.observed_at > as_of:
        raise ValueError("Source attribution is after the simulation cutoff.")


@dataclass(frozen=True, slots=True)
class SupplierFacts:
    offer_id: str
    terms: SupplierTerms
    source: SourceAttribution
    receipts: tuple[LineEvidence, ...]  # always empty: history comes from the capture
    history_reference: str
    score_quantities: QuantityValidity


@dataclass(frozen=True, slots=True)
class PlanningFacts:
    company_id: str
    as_of: datetime
    requirement: ProcurementRequirement
    approval_reference: str
    requirement_source: SourceAttribution
    policy: PlanningPolicy
    policy_source: SourceAttribution
    suppliers: tuple[SupplierFacts, ...]
    source_type: str = HISTORY_SOURCE


@dataclass(frozen=True, slots=True)
class OdooHistoryPlanningFacts(PlanningFacts):
    history: str = ""
    # Odoo display names captured at creation (identity -> name); never used in planning.
    labels: tuple[tuple[str, str], ...] = ()


def assemble_planning_input(facts: PlanningFacts):
    """Pair captured Odoo history features with the buyer terms and their attribution."""
    if not isinstance(facts, OdooHistoryPlanningFacts) or facts.source_type != HISTORY_SOURCE:
        raise ValueError("Typed backend-acquired Odoo history required.")
    captured = {f.context.supplier_id: f for f in capture_features(facts.history)}
    if set(captured) != {s.terms.supplier_id for s in facts.suppliers}:
        raise ValueError("Complete acquired supplier history required.")
    text_identity(facts.company_id)
    text_identity(facts.approval_reference)
    utc(facts.as_of)
    validate_source(facts.requirement_source, "requirement", facts.as_of)
    validate_source(facts.policy_source, "policy", facts.as_of)
    if not isinstance(facts.suppliers, tuple) or not 1 <= len(facts.suppliers) <= MAX_SUPPLIERS:
        raise ValueError(f"Supply 1-{MAX_SUPPLIERS} controlled suppliers.")
    if not 1 <= len(facts.policy.epsilons) <= MAX_EPSILONS:
        raise ValueError(f"Supply 1-{MAX_EPSILONS} explicit epsilon values.")
    offers, features = set(), []
    for item in sorted(facts.suppliers, key=lambda s: s.terms.supplier_id):
        text_identity(item.offer_id)
        text_identity(item.history_reference)
        if item.offer_id in offers:
            raise ValueError("Duplicate offer identity.")
        offers.add(item.offer_id)
        validate_source(item.source, "commercial_terms", facts.as_of)
        context = Context(
            item.terms.supplier_id,
            facts.company_id,
            facts.requirement.product_id,
            facts.requirement.quantity_unit,
        )
        feature = captured[item.terms.supplier_id]
        if feature.context != context or item.receipts or feature.cutoff > facts.as_of:
            raise ValueError("Captured history context/cutoff mismatch.")
        features.append((feature, item.score_quantities))
    request = PlanningRequest(
        facts.requirement,
        tuple(s.terms for s in sorted(facts.suppliers, key=lambda s: s.terms.supplier_id)),
        facts.policy,
        None,
    )
    provenance = []

    def attribute(path, fields, source):
        provenance.extend(
            FieldProvenance(
                f"{path}.{name}",
                name,
                source.source_type,
                source.source_reference,
                source.observed_at,
            )
            for name in fields
        )

    attribute("request.requirement", asdict(facts.requirement), facts.requirement_source)
    attribute("facts", ("company_id", "as_of", "approval_reference"), facts.requirement_source)
    attribute("request.policy", asdict(facts.policy), facts.policy_source)
    for item in sorted(facts.suppliers, key=lambda s: s.terms.supplier_id):
        attribute(f"request.suppliers[{item.terms.supplier_id}]", asdict(item.terms), item.source)
    return request, tuple(features), ProvenanceManifest(tuple(provenance))
