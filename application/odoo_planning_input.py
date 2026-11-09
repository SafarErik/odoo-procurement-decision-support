"""Quotation assembly with separate ERP and buyer-supplied provenance; no ML or I/O."""

from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime

from application.odoo_quotations import OdooComparisonCaseFacts
from application.planning_history import capture_features
from application.planning_input import OdooHistoryPlanningFacts, PlanningFacts, validate_source
from application.provenance import FieldProvenance, ProvenanceManifest, SourceAttribution
from decision_core.planning.models import (
    MinimumOrder,
    PlanningPolicy,
    PlanningRequest,
    ProcurementRequirement,
    QuantityRange,
    SupplierTerms,
    decimal,
    identity,
    require,
)
from supplier_evaluation.contracts import utc

# Provenance source type of every value read from Odoo's JSON-2 API (stored in snapshots).
ODOO_JSON2_SOURCE = "odoo_json2"


@dataclass(frozen=True, slots=True)
class SupplementalPlanningTerms:
    offer_id: str
    capacity: int
    available: bool
    minimum_order: MinimumOrder
    price_quantities: QuantityRange
    delivery_quantities: QuantityRange
    promised_date: date
    source: SourceAttribution


@dataclass(frozen=True, slots=True)
class OdooPlanningCommand:
    approved_quantity: int
    required_date: date
    approval_reference: str
    requirement_source: SourceAttribution
    policy: PlanningPolicy
    policy_source: SourceAttribution
    supplemental_terms: tuple[SupplementalPlanningTerms, ...]
    as_of: datetime


def assemble_odoo_planning_input(
    case: OdooComparisonCaseFacts,
    command: OdooPlanningCommand,
    *,
    currency_id: str,
    currency_code: str,
    currency_source: SourceAttribution,
) -> tuple[PlanningRequest, ProvenanceManifest]:
    """Build the planning request from an Odoo quotation group plus the buyer's terms.

    Prices, product, unit, company and suppliers come from the Odoo quotations; demand,
    date, policy and per-supplier terms (capacity, MOQ, ranges, promised date) come from
    the buyer's command, each with its own source. The quotation quantity is never used
    as demand. Every request field gets a provenance entry saying where it came from.
    Currency identity and code must already be resolved by the trusted Odoo reader.
    Business violations raise ``InvalidPlanningInput`` with a specific code. A timestamp
    that is not UTC, a missing or misnamed source attribution, or a source observed after
    the cutoff raise a plain ``ValueError`` without a code.
    """
    terms = _check_group_and_sources(case, command, currency_id, currency_source)
    suppliers, entries, contexts = [], [], set()
    seen_offers, seen_suppliers, seen_lines = set(), set(), set()
    offers = tuple(sorted(case.offers, key=lambda item: item.offer_id))
    for offer in offers:
        line = _checked_offer_line(offer, case, command)
        require(
            offer.offer_id not in seen_offers
            and offer.supplier_id not in seen_suppliers
            and line.line_id not in seen_lines,
            "duplicate_quotation",
            "Stable offers, suppliers and lines must be unique.",
        )
        seen_offers.add(offer.offer_id)
        seen_suppliers.add(offer.supplier_id)
        seen_lines.add(line.line_id)
        require(
            line.company_id == offer.company_id
            and line.currency_id == offer.currency_id == currency_id
            and line.discount == 0
            and not line.tax_ids,
            "unsupported_quotation_context",
            "Matching company/currency, zero discount and no taxes required.",
        )
        contexts.add((offer.company_id, line.product_id, line.uom_id))
        extra = terms[offer.offer_id]
        validate_source(extra.source, "commercial_terms", command.as_of)
        supplier = SupplierTerms(
            offer.supplier_id,
            line.product_id,
            line.uom_id,
            currency_code,
            line.unit_price,
            extra.capacity,
            extra.available,
            extra.minimum_order,
            extra.price_quantities,
            extra.delivery_quantities,
            extra.promised_date,
        )
        suppliers.append(supplier)
        entries += _supplier_provenance(supplier, offer, line, extra.source, currency_source)
    require(len(contexts) == 1, "context_mismatch", "One company/product/unit required.")
    company, product, unit = contexts.pop()
    identity(company, "company")
    requirement = ProcurementRequirement(
        product, command.approved_quantity, unit, currency_code, command.required_date
    )
    entries += _requirement_provenance(case, command, offers[0], currency_source)
    return PlanningRequest(
        requirement, tuple(sorted(suppliers, key=lambda s: s.supplier_id)), command.policy, None
    ), ProvenanceManifest(tuple(entries))


def _check_group_and_sources(case, command, currency_id, currency_source) -> dict:
    """Group, cutoff, offer count and sources are valid; return the buyer terms by offer id."""
    require(isinstance(case, OdooComparisonCaseFacts), "invalid_case", "Typed case required.")
    utc(command.as_of)
    utc(case.observed_at)
    require(case.observed_at <= command.as_of, "future_source", "Case is after cutoff.")
    identity(case.comparison_case_id, "comparison group")
    identity(command.approval_reference, "approval reference")
    require(
        isinstance(case.offers, tuple) and 3 <= len(case.offers) <= 10,
        "unsupported_offer_count",
        "Supply 3-10 grouped quotations.",
    )
    for source, field in (
        (command.requirement_source, "requirement"),
        (command.policy_source, "policy"),
        (currency_source, "currency"),
    ):
        validate_source(source, field, command.as_of)
    require(
        currency_source.source_type == ODOO_JSON2_SOURCE
        and currency_source.source_reference == f"{currency_id}#name",
        "invalid_currency_source",
        "Resolve the exact Odoo currency code; do not convert or infer it.",
    )
    terms = {item.offer_id: item for item in command.supplemental_terms}
    require(
        len(terms) == len(command.supplemental_terms)
        and set(terms) == {offer.offer_id for offer in case.offers},
        "invalid_terms_join",
        "Exactly one attributed term set per offer required.",
    )
    return terms


def _checked_offer_line(offer, case, command):
    """An open quotation of this group, observed before the cutoff, with exactly one line;
    return that line."""
    for value in (offer.offer_id, offer.supplier_id, offer.supplier_source_reference):
        identity(value, "offer/supplier identity")
    utc(offer.observed_at)
    require(offer.observed_at <= command.as_of, "future_source", "Offer is after cutoff.")
    require(
        offer.comparison_case_id == case.comparison_case_id
        and offer.state in {"draft", "sent", "to approve"}
        and len(offer.lines) == 1,
        "unsupported_quotation",
        "One supported line in the exact open comparison group required.",
    )
    line = offer.lines[0]
    identity(line.line_id, "quotation line")
    decimal(line.quantity, "quotation quantity", positive=True)
    return line


def _entry(path: str, field: str, source: SourceAttribution) -> FieldProvenance:
    return FieldProvenance(
        path, field, source.source_type, source.source_reference, source.observed_at
    )


def _odoo(field: str, reference: str, observed_at: datetime) -> SourceAttribution:
    """A value read from Odoo's JSON-2 API at ``reference`` (record id and field)."""
    return SourceAttribution(field, ODOO_JSON2_SOURCE, reference, observed_at)


def _supplier_provenance(supplier, offer, line, terms_source, currency_source) -> list:
    """Buyer terms from the buyer's source; identity, price, product and unit from Odoo."""
    prefix = f"request.suppliers[{supplier.supplier_id}]"
    entries = [
        _entry(f"{prefix}.{field}", field, terms_source)
        for field in (
            "capacity",
            "available",
            "minimum_order",
            "price_quantities",
            "delivery_quantities",
            "promised_date",
        )
    ]
    for field, reference in (
        ("supplier_id", offer.supplier_source_reference),
        ("unit_price", f"{line.line_id}#price_unit"),
        ("product_id", f"{line.line_id}#product_id"),
        ("quantity_unit", f"{line.line_id}#product_uom_id"),
    ):
        entries.append(
            _entry(f"{prefix}.{field}", field, _odoo(field, reference, offer.observed_at))
        )
    entries.append(_entry(f"{prefix}.currency", "currency", currency_source))
    return entries


def _requirement_provenance(case, command, first_offer, currency_source) -> list:
    """Demand, date, policy and approval from the buyer; product, unit, company from Odoo."""
    line_id, observed_at = first_offer.lines[0].line_id, first_offer.observed_at
    entries = [
        _entry(f"request.requirement.{field}", field, command.requirement_source)
        for field in ("approved_quantity", "required_date")
    ]
    for field, reference in (("product_id", "product_id"), ("quantity_unit", "product_uom_id")):
        entries.append(
            _entry(
                f"request.requirement.{field}",
                field,
                _odoo(field, f"{line_id}#{reference}", observed_at),
            )
        )
    entries.append(_entry("request.requirement.currency", "currency", currency_source))
    entries += [
        _entry(f"request.policy.{field}", field, command.policy_source)
        for field in asdict(command.policy)
    ]
    entries += [
        _entry(f"facts.{field}", field, command.requirement_source)
        for field in ("approval_reference", "as_of")
    ]
    company = _odoo("company_id", f"{first_offer.offer_id}#company_id", observed_at)
    entries.append(_entry("facts.company_id", "company_id", company))
    group = _odoo("purchase_group_id", case.comparison_case_id, case.observed_at)
    entries.append(_entry("facts.comparison_case_id", "purchase_group_id", group))
    return entries


def bind_controlled_odoo_input(case, facts: PlanningFacts, currency_code, currency_observed_at):
    """Bind live quotations while preserving each controlled history source."""
    as_of = datetime.now(UTC)
    require(facts.as_of <= as_of, "future_cutoff", "Live input cannot use a future cutoff.")
    currency_id = case.offers[0].currency_id if case.offers else ""
    command = OdooPlanningCommand(
        facts.requirement.approved_quantity,
        facts.requirement.required_date,
        facts.approval_reference,
        facts.requirement_source,
        facts.policy,
        facts.policy_source,
        tuple(
            SupplementalPlanningTerms(
                s.offer_id,
                s.terms.capacity,
                s.terms.available,
                s.terms.minimum_order,
                s.terms.price_quantities,
                s.terms.delivery_quantities,
                s.terms.promised_date,
                s.source,
            )
            for s in facts.suppliers
        ),
        as_of,
    )
    request, provenance = assemble_odoo_planning_input(
        case,
        command,
        currency_id=currency_id,
        currency_code=currency_code,
        currency_source=SourceAttribution(
            "currency", ODOO_JSON2_SOURCE, f"{currency_id}#name", currency_observed_at
        ),
    )
    observed = {s.supplier_id: s for s in request.suppliers}
    require(
        facts.company_id == case.offers[0].company_id
        and facts.requirement == request.requirement
        and len(facts.suppliers) == len(observed)
        and all(
            s.terms.supplier_id in observed and s.terms == observed[s.terms.supplier_id]
            for s in facts.suppliers
        ),
        "quotation_changed",
        "Caller expectations must match the independently read quotation context and price.",
    )
    clock = SourceAttribution("as_of", "application_clock", "odoo-input-assembly-completed", as_of)
    entries = [e for e in provenance.entries if e.canonical_path != "facts.as_of"]
    entries.append(
        FieldProvenance(
            "facts.as_of", "as_of", clock.source_type, clock.source_reference, clock.observed_at
        )
    )
    history_times = (
        {f.context.supplier_id: f.evidence_available_at for f in capture_features(facts.history)}
        if isinstance(facts, OdooHistoryPlanningFacts)
        else {}
    )
    for supplier in facts.suppliers:
        entries.append(
            FieldProvenance(
                f"facts.suppliers[{supplier.terms.supplier_id}].receipts",
                "receipts",
                facts.source_type,
                supplier.history_reference,
                history_times.get(supplier.terms.supplier_id, facts.as_of),
            )
        )
    return replace(facts, as_of=as_of, requirement=request.requirement), ProvenanceManifest(
        tuple(entries)
    )


def bind_odoo_history_input(captured, facts: OdooHistoryPlanningFacts):
    """Attach a capture (from ``capture_odoo_history``) to the buyer's facts and bind quotes."""
    case, code, observed, capture = captured
    references = {f.context.supplier_id: f.source_reference for f in capture_features(capture)}
    facts = replace(
        facts,
        history=capture,
        labels=case.labels,
        suppliers=tuple(
            replace(s, history_reference=references.get(s.terms.supplier_id, s.history_reference))
            for s in facts.suppliers
        ),
    )
    return bind_controlled_odoo_input(case, facts, code, observed)
