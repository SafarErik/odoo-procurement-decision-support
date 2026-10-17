"""Controlled V2 facts and field attribution; no live ERP access or ML loading."""

from dataclasses import asdict, dataclass
from datetime import datetime

from application.planning_history import capture_features
from application.provenance import FieldProvenance, ProvenanceManifest, SourceAttribution
from decision_core.planning.models import (
    PlanningPolicy,
    PlanningRequest,
    ProcurementRequirement,
    SupplierTerms,
)
from supplier_evaluation.contracts import (
    ODOO_HISTORY,
    SYNTHETIC,
    Context,
    LineEvidence,
    QuantityValidity,
    text_identity,
    utc,
)
from supplier_evaluation.history import prepare_history


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
    receipts: tuple[LineEvidence, ...]
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
    source_type: str = SYNTHETIC


@dataclass(frozen=True, slots=True)
class OdooHistoryPlanningFacts(PlanningFacts):
    history: str = ""


def assemble_planning_input(facts: PlanningFacts):
    """Derive T14 features from bounded receipts, retaining separate T6 attribution."""
    if not isinstance(facts, PlanningFacts) or facts.source_type not in {SYNTHETIC, ODOO_HISTORY}:
        raise ValueError("This increment accepts explicitly synthetic evidence only.")
    captured = {}
    if facts.source_type == ODOO_HISTORY:
        if not isinstance(facts, OdooHistoryPlanningFacts):
            raise ValueError("Typed backend-acquired history required.")
        captured = {f.context.supplier_id: f for f in capture_features(facts.history)}
        if set(captured) != {s.terms.supplier_id for s in facts.suppliers}:
            raise ValueError("Complete acquired supplier history required.")
    text_identity(facts.company_id)
    text_identity(facts.approval_reference)
    utc(facts.as_of)
    validate_source(facts.requirement_source, "requirement", facts.as_of)
    validate_source(facts.policy_source, "policy", facts.as_of)
    if not isinstance(facts.suppliers, tuple) or not 1 <= len(facts.suppliers) <= 10:
        raise ValueError("Supply 1-10 controlled suppliers.")
    if not 1 <= len(facts.policy.epsilons) <= 3:
        raise ValueError("Supply 1-3 explicit epsilon values.")
    offers, lines, features = set(), set(), []
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
        if any(line.line_id in lines for line in item.receipts):
            raise ValueError("Receipt identities must be unique across suppliers.")
        lines.update(line.line_id for line in item.receipts)
        feature = captured.get(item.terms.supplier_id)
        if feature is not None and (
            feature.context != context or item.receipts or feature.cutoff > facts.as_of
        ):
            raise ValueError("Captured history context/cutoff mismatch.")
        features.append(
            (
                feature
                if feature is not None
                else prepare_history(
                    context, facts.as_of, item.receipts, facts.source_type, item.history_reference
                ),
                item.score_quantities,
            )
        )
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
