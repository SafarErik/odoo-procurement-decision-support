"""Assemble canonical decision input from validated facts and supplemental terms."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from decision_core import (
    DomainValidationError,
    PurchaseRequirement,
    StrategicProfile,
    SupplierOffer,
)

_SUPPORTED_RFQ_STATES = frozenset({"draft", "sent", "to approve"})


class DecisionInputAssemblyError(ValueError):
    """Stable fail-closed error raised before Decision Core evaluation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class SourceAttribution:
    """Source identity and observation time for one explicitly supplied value."""

    field_name: str
    source_type: str
    source_reference: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class SupplementalValue:
    """A supplied decimal value whose attribution does not imply objective truth."""

    value: Decimal
    attribution: SourceAttribution


@dataclass(frozen=True, slots=True)
class SupplementalOfferTerms:
    """Offer terms that the supported Odoo schema does not prove."""

    offer_id: str
    hard_minimum_order_quantity: SupplementalValue
    supplier_promised_lead_time_days: SupplementalValue


@dataclass(frozen=True, slots=True)
class OdooOrderLineFacts:
    """Read-only Odoo facts for one candidate quotation line."""

    line_id: str
    product_id: str
    uom_id: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    tax_ids: tuple[str, ...]
    currency_id: str
    company_id: str


@dataclass(frozen=True, slots=True)
class OdooComparisonOfferFacts:
    """Read-only Odoo facts for one RFQ in an explicit alternative group."""

    offer_id: str
    order_reference: str
    comparison_case_id: str
    supplier_id: str
    supplier_source_reference: str
    state: str
    currency_id: str
    company_id: str
    lines: tuple[OdooOrderLineFacts, ...]
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class OdooComparisonCaseFacts:
    """One explicitly grouped set of Odoo RFQs."""

    comparison_case_id: str
    offers: tuple[OdooComparisonOfferFacts, ...]
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class CanonicalDecisionInput:
    """The existing Decision Core inputs, grouped without changing their models."""

    requirement: PurchaseRequirement
    offers: tuple[SupplierOffer, ...]
    profile: StrategicProfile


@dataclass(frozen=True, slots=True)
class FieldProvenance:
    """Trace one canonical field to one observed source value."""

    canonical_path: str
    field_name: str
    source_type: str
    source_reference: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class ProvenanceManifest:
    """Application-layer trace data kept outside the Decision Core."""

    entries: tuple[FieldProvenance, ...]


@dataclass(frozen=True, slots=True)
class AssembledDecisionInput:
    """Canonical decision input and its separate provenance manifest."""

    canonical: CanonicalDecisionInput
    provenance: ProvenanceManifest


def assemble_decision_input(
    odoo_case: OdooComparisonCaseFacts,
    supplemental_terms: tuple[SupplementalOfferTerms, ...],
    profile: StrategicProfile,
    profile_attribution: SourceAttribution,
) -> AssembledDecisionInput:
    """Validate the T6 subset and assemble canonical input without scoring it."""

    _require_identifier(odoo_case.comparison_case_id, "missing_comparison_case_identity")
    _require_aware_time(odoo_case.observed_at, "invalid_odoo_observation_time")
    if len(odoo_case.offers) < 3:
        _fail("insufficient_offers", "A comparison case requires at least three RFQs.")

    offers_by_id: dict[str, OdooComparisonOfferFacts] = {}
    line_by_offer_id: dict[str, OdooOrderLineFacts] = {}
    for offer in odoo_case.offers:
        _require_identifier(offer.offer_id, "missing_offer_identity")
        if offer.offer_id in offers_by_id:
            _fail("duplicate_odoo_offer_identity", f"Duplicate Odoo offer: {offer.offer_id}.")
        offers_by_id[offer.offer_id] = offer
        _require_identifier(offer.order_reference, "missing_order_reference")
        _require_identifier(offer.supplier_id, "missing_supplier_identity")
        _require_identifier(offer.supplier_source_reference, "missing_supplier_source_reference")
        _require_identifier(offer.currency_id, "missing_currency_identity")
        _require_identifier(offer.company_id, "missing_company_identity")
        _require_aware_time(offer.observed_at, "invalid_odoo_observation_time")
        if offer.comparison_case_id != odoo_case.comparison_case_id:
            _fail(
                "unstable_comparison_case_identity",
                "Every RFQ must have the same explicit purchase_group_id.",
            )
        if offer.state not in _SUPPORTED_RFQ_STATES:
            _fail("unsupported_rfq_state", f"Unsupported RFQ state: {offer.state!r}.")
        if len(offer.lines) != 1:
            _fail(
                "unsupported_order_line_count",
                f"Offer {offer.offer_id} must contain exactly one supported order line.",
            )
        line = offer.lines[0]
        _validate_odoo_line(line)
        line_by_offer_id[offer.offer_id] = line

    supplemental_by_id: dict[str, SupplementalOfferTerms] = {}
    for terms in supplemental_terms:
        _require_identifier(terms.offer_id, "missing_supplemental_offer_identity")
        if terms.offer_id in supplemental_by_id:
            _fail(
                "duplicate_supplemental_offer_identity",
                f"Duplicate supplemental offer: {terms.offer_id}.",
            )
        supplemental_by_id[terms.offer_id] = terms

    unknown = sorted(supplemental_by_id.keys() - offers_by_id.keys())
    if unknown:
        _fail("unknown_supplemental_offer_identity", f"Unknown supplemental offers: {unknown}.")
    missing = sorted(offers_by_id.keys() - supplemental_by_id.keys())
    if missing:
        _fail("missing_supplemental_terms", f"Missing supplemental terms for: {missing}.")

    lines = tuple(line_by_offer_id.values())
    _require_common("product_variant", {line.product_id for line in lines})
    _require_common("uom", {line.uom_id for line in lines})
    _require_common("currency", {offer.currency_id for offer in odoo_case.offers})
    _require_common("company", {offer.company_id for offer in odoo_case.offers})
    _require_common("comparison_quantity", {line.quantity for line in lines})
    for offer in odoo_case.offers:
        line = line_by_offer_id[offer.offer_id]
        if line.currency_id != offer.currency_id:
            _fail("inconsistent_currency", "Order and line currency identities must match.")
        if line.company_id != offer.company_id:
            _fail("inconsistent_company", "Order and line company identities must match.")
        if line.discount != Decimal("0"):
            _fail("unsupported_discount", "The supported subset requires zero discount.")
        if line.tax_ids:
            _fail("unsupported_tax_semantics", "The supported subset requires no line taxes.")

    _validate_attribution(profile_attribution, "strategic_profile")
    requested_quantity = lines[0].quantity
    canonical_offers: list[SupplierOffer] = []
    provenance_entries: list[FieldProvenance] = []

    for offer_id in sorted(offers_by_id):
        offer = offers_by_id[offer_id]
        line = line_by_offer_id[offer_id]
        terms = supplemental_by_id[offer_id]
        _validate_supplemental_terms(terms)
        try:
            canonical_offer = SupplierOffer(
                offer_id=offer.offer_id,
                supplier_id=offer.supplier_id,
                unit_price=line.unit_price,
                lead_time_days=terms.supplier_promised_lead_time_days.value,
                minimum_order_quantity=terms.hard_minimum_order_quantity.value,
            )
        except DomainValidationError as error:
            _fail("invalid_canonical_value", str(error), error)
        canonical_offers.append(canonical_offer)
        provenance_entries.extend(_offer_provenance(offer, line, terms))

    try:
        requirement = PurchaseRequirement(
            requirement_id=odoo_case.comparison_case_id,
            requested_quantity=requested_quantity,
        )
    except DomainValidationError as error:
        _fail("invalid_canonical_value", str(error), error)

    group_reference = odoo_case.comparison_case_id
    provenance_entries.append(
        _provenance(
            "requirement.requirement_id",
            "purchase_group_id",
            "odoo_json2",
            group_reference,
            odoo_case.observed_at,
        )
    )
    for offer in sorted(odoo_case.offers, key=lambda item: item.offer_id):
        line = line_by_offer_id[offer.offer_id]
        provenance_entries.append(
            _provenance(
                "requirement.requested_quantity",
                "product_qty",
                "odoo_json2",
                f"{line.line_id}#product_qty",
                offer.observed_at,
            )
        )
    for field_name in ("name", "unit_price_weight", "lead_time_weight"):
        provenance_entries.append(
            _provenance(
                f"profile.{field_name}",
                field_name,
                profile_attribution.source_type,
                profile_attribution.source_reference,
                profile_attribution.observed_at,
            )
        )

    return AssembledDecisionInput(
        canonical=CanonicalDecisionInput(
            requirement=requirement,
            offers=tuple(canonical_offers),
            profile=profile,
        ),
        provenance=ProvenanceManifest(entries=tuple(provenance_entries)),
    )


def _validate_odoo_line(line: OdooOrderLineFacts) -> None:
    for value, code in (
        (line.line_id, "missing_order_line_identity"),
        (line.product_id, "missing_product_identity"),
        (line.uom_id, "missing_uom_identity"),
        (line.currency_id, "missing_currency_identity"),
        (line.company_id, "missing_company_identity"),
    ):
        _require_identifier(value, code)
    for value in (line.quantity, line.unit_price, line.discount):
        if not isinstance(value, Decimal) or not value.is_finite():
            _fail("invalid_odoo_numeric_fact", "Odoo numeric facts must be finite Decimals.")


def _validate_supplemental_terms(terms: SupplementalOfferTerms) -> None:
    if not isinstance(terms.hard_minimum_order_quantity, SupplementalValue):
        _fail("missing_supplemental_moq", "Every offer requires an explicitly supplied hard MOQ.")
    if not isinstance(terms.supplier_promised_lead_time_days, SupplementalValue):
        _fail(
            "missing_supplemental_lead_time",
            "Every offer requires an explicitly supplied supplier-promised lead time.",
        )
    _validate_attribution(
        terms.hard_minimum_order_quantity.attribution,
        "minimum_order_quantity",
    )
    _validate_attribution(
        terms.supplier_promised_lead_time_days.attribution,
        "lead_time_days",
    )


def _validate_attribution(attribution: SourceAttribution, expected_field: str) -> None:
    if not isinstance(attribution, SourceAttribution):
        _fail("invalid_source_attribution", f"Missing attribution for {expected_field!r}.")
    if attribution.field_name != expected_field:
        _fail(
            "invalid_source_attribution",
            f"Expected attribution for {expected_field!r}.",
        )
    if (
        not isinstance(attribution.source_type, str)
        or not attribution.source_type.strip()
        or not isinstance(attribution.source_reference, str)
        or not attribution.source_reference.strip()
    ):
        _fail(
            "invalid_source_attribution",
            "Source type and source reference must be usable non-empty strings.",
        )
    _require_aware_time(attribution.observed_at, "invalid_source_attribution")


def _offer_provenance(
    offer: OdooComparisonOfferFacts,
    line: OdooOrderLineFacts,
    terms: SupplementalOfferTerms,
) -> tuple[FieldProvenance, ...]:
    prefix = f"offers[{offer.offer_id}]"
    return (
        _provenance(f"{prefix}.offer_id", "id", "odoo_json2", offer.offer_id, offer.observed_at),
        _provenance(
            f"{prefix}.supplier_id",
            "commercial_partner_id",
            "odoo_json2",
            offer.supplier_source_reference,
            offer.observed_at,
        ),
        _provenance(
            f"{prefix}.unit_price",
            "price_unit",
            "odoo_json2",
            f"{line.line_id}#price_unit",
            offer.observed_at,
        ),
        _from_attribution(
            f"{prefix}.lead_time_days",
            terms.supplier_promised_lead_time_days.attribution,
        ),
        _from_attribution(
            f"{prefix}.minimum_order_quantity",
            terms.hard_minimum_order_quantity.attribution,
        ),
    )


def _from_attribution(path: str, attribution: SourceAttribution) -> FieldProvenance:
    return _provenance(
        path,
        attribution.field_name,
        attribution.source_type,
        attribution.source_reference,
        attribution.observed_at,
    )


def _provenance(
    path: str,
    field_name: str,
    source_type: str,
    source_reference: str,
    observed_at: datetime,
) -> FieldProvenance:
    return FieldProvenance(path, field_name, source_type, source_reference, observed_at)


def _require_common(name: str, values: set[object]) -> None:
    if len(values) != 1:
        _fail(f"inconsistent_{name}", f"All RFQs must use one common {name.replace('_', ' ')}.")


def _require_identifier(value: str, code: str) -> None:
    if not isinstance(value, str) or not value.strip():
        _fail(code, "A mandatory stable identity is missing.")


def _require_aware_time(value: datetime, code: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _fail(code, "Observation times must be timezone-aware datetimes.")


def _fail(code: str, message: str, cause: Exception | None = None) -> None:
    error = DecisionInputAssemblyError(code, message)
    if cause is None:
        raise error
    raise error from cause
