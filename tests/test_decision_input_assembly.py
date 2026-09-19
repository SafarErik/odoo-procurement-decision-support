"""Fast tests for provenance-aware hybrid decision-input assembly."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from application.decision_input_assembly import (
    AssembledDecisionInput,
    DecisionInputAssemblyError,
    OdooComparisonCaseFacts,
    OdooComparisonOfferFacts,
    OdooOrderLineFacts,
    SourceAttribution,
    SupplementalOfferTerms,
    SupplementalValue,
    assemble_decision_input,
)
from application.decisions import evaluate_procurement_decision
from decision_core import PurchaseRequirement, StrategicProfile, SupplierOffer

OBSERVED_AT = datetime(2026, 9, 18, 8, 0, tzinfo=UTC)
CASE_ID = "odoo:purchase.order.group:501"


def _line(
    suffix: str,
    price: str,
    **changes: object,
) -> OdooOrderLineFacts:
    values: dict[str, object] = {
        "line_id": f"odoo:purchase.order.line:20{suffix}",
        "product_id": "odoo:product.product:42",
        "uom_id": "odoo:uom.uom:1",
        "quantity": Decimal("100"),
        "unit_price": Decimal(price),
        "discount": Decimal("0"),
        "tax_ids": (),
        "currency_id": "odoo:res.currency:2",
        "company_id": "odoo:res.company:1",
    }
    values.update(changes)
    return OdooOrderLineFacts(**values)  # type: ignore[arg-type]


def _offer(suffix: str, price: str, **changes: object) -> OdooComparisonOfferFacts:
    values: dict[str, object] = {
        "offer_id": f"odoo:purchase.order:10{suffix}",
        "order_reference": f"T6-RFQ-{suffix}",
        "comparison_case_id": CASE_ID,
        "supplier_id": f"odoo:res.partner:30{suffix}",
        "supplier_source_reference": f"odoo:res.partner:30{suffix}#commercial_partner_id",
        "state": "draft",
        "currency_id": "odoo:res.currency:2",
        "company_id": "odoo:res.company:1",
        "lines": (_line(suffix, price),),
        "observed_at": OBSERVED_AT,
    }
    values.update(changes)
    return OdooComparisonOfferFacts(**values)  # type: ignore[arg-type]


def _case() -> OdooComparisonCaseFacts:
    return OdooComparisonCaseFacts(
        comparison_case_id=CASE_ID,
        offers=(_offer("A", "10"), _offer("B", "12"), _offer("C", "9")),
        observed_at=OBSERVED_AT,
    )


def _attribution(field: str, suffix: str) -> SourceAttribution:
    return SourceAttribution(
        field_name=field,
        source_type="supplier_email",
        source_reference=f"mailbox:quote-{suffix}@example.test#2026-09-18",
        observed_at=OBSERVED_AT,
    )


def _terms(
    suffix: str,
    moq: str,
    lead_time: str,
) -> SupplementalOfferTerms:
    return SupplementalOfferTerms(
        offer_id=f"odoo:purchase.order:10{suffix}",
        hard_minimum_order_quantity=SupplementalValue(
            Decimal(moq), _attribution("minimum_order_quantity", suffix)
        ),
        supplier_promised_lead_time_days=SupplementalValue(
            Decimal(lead_time), _attribution("lead_time_days", suffix)
        ),
    )


def _supplements() -> tuple[SupplementalOfferTerms, ...]:
    return (_terms("C", "150", "8"), _terms("A", "50", "10"), _terms("B", "100", "5"))


def _profile_attribution() -> SourceAttribution:
    return SourceAttribution(
        field_name="strategic_profile",
        source_type="application_configuration",
        source_reference="profile:cost-focused:v1",
        observed_at=OBSERVED_AT,
    )


def _assemble(
    case: OdooComparisonCaseFacts | None = None,
    terms: tuple[SupplementalOfferTerms, ...] | None = None,
) -> AssembledDecisionInput:
    return assemble_decision_input(
        case or _case(),
        terms if terms is not None else _supplements(),
        StrategicProfile.cost_focused(),
        _profile_attribution(),
    )


def test_assembles_exact_canonical_reference_case_and_evaluates_unchanged() -> None:
    assembled = _assemble()

    assert assembled.canonical.requirement == PurchaseRequirement(CASE_ID, Decimal("100"))
    assert assembled.canonical.offers == (
        SupplierOffer(
            "odoo:purchase.order:10A",
            "odoo:res.partner:30A",
            Decimal("10"),
            Decimal("10"),
            Decimal("50"),
        ),
        SupplierOffer(
            "odoo:purchase.order:10B",
            "odoo:res.partner:30B",
            Decimal("12"),
            Decimal("5"),
            Decimal("100"),
        ),
        SupplierOffer(
            "odoo:purchase.order:10C",
            "odoo:res.partner:30C",
            Decimal("9"),
            Decimal("8"),
            Decimal("150"),
        ),
    )
    result = evaluate_procurement_decision(
        assembled.canonical.requirement,
        assembled.canonical.offers,
        assembled.canonical.profile,
    )
    assert [ranked.offer.offer_id for ranked in result.ranked_offers] == [
        "odoo:purchase.order:10A",
        "odoo:purchase.order:10B",
    ]
    assert [excluded.offer.offer_id for excluded in result.excluded_offers] == [
        "odoo:purchase.order:10C"
    ]


def test_manifest_traces_every_canonical_field_without_entering_decision_core() -> None:
    assembled = _assemble()
    paths = [entry.canonical_path for entry in assembled.provenance.entries]

    assert "requirement.requirement_id" in paths
    assert paths.count("requirement.requested_quantity") == 3
    assert {f"profile.{name}" for name in ("name", "unit_price_weight", "lead_time_weight")} <= set(
        paths
    )
    for offer in assembled.canonical.offers:
        prefix = f"offers[{offer.offer_id}]"
        assert {
            f"{prefix}.offer_id",
            f"{prefix}.supplier_id",
            f"{prefix}.unit_price",
            f"{prefix}.lead_time_days",
            f"{prefix}.minimum_order_quantity",
        } <= set(paths)
    assert not hasattr(assembled.canonical, "provenance")
    assert not hasattr(assembled.canonical.offers[0], "provenance")


def test_supplemental_join_is_by_stable_offer_identity_not_input_order() -> None:
    forward = _assemble()
    reversed_case = replace(_case(), offers=tuple(reversed(_case().offers)))
    reverse = _assemble(reversed_case, tuple(reversed(_supplements())))

    assert reverse.canonical == forward.canonical


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (
            lambda case: replace(case, comparison_case_id=""),
            "missing_comparison_case_identity",
        ),
        (
            lambda case: replace(
                case,
                offers=(replace(case.offers[0], comparison_case_id=""), *case.offers[1:]),
            ),
            "unstable_comparison_case_identity",
        ),
        (
            lambda case: replace(case, offers=case.offers[:2]),
            "insufficient_offers",
        ),
        (
            lambda case: replace(
                case,
                offers=(
                    case.offers[0],
                    replace(case.offers[1], offer_id=case.offers[0].offer_id),
                    case.offers[2],
                ),
            ),
            "duplicate_odoo_offer_identity",
        ),
        (
            lambda case: replace(
                case, offers=(replace(case.offers[0], lines=()), *case.offers[1:])
            ),
            "unsupported_order_line_count",
        ),
        (
            lambda case: replace(
                case,
                offers=(
                    replace(case.offers[0], lines=(case.offers[0].lines[0],) * 2),
                    *case.offers[1:],
                ),
            ),
            "unsupported_order_line_count",
        ),
        (
            lambda case: replace(
                case,
                offers=(replace(case.offers[0], state="purchase"), *case.offers[1:]),
            ),
            "unsupported_rfq_state",
        ),
        (
            lambda case: replace(
                case,
                offers=(
                    case.offers[0],
                    replace(
                        case.offers[1],
                        lines=(replace(case.offers[1].lines[0], product_id="other"),),
                    ),
                    case.offers[2],
                ),
            ),
            "inconsistent_product_variant",
        ),
        (
            lambda case: replace(
                case,
                offers=(
                    case.offers[0],
                    replace(
                        case.offers[1], lines=(replace(case.offers[1].lines[0], uom_id="other"),)
                    ),
                    case.offers[2],
                ),
            ),
            "inconsistent_uom",
        ),
        (
            lambda case: replace(
                case, offers=(replace(case.offers[0], currency_id="other"), *case.offers[1:])
            ),
            "inconsistent_currency",
        ),
        (
            lambda case: replace(
                case, offers=(replace(case.offers[0], company_id="other"), *case.offers[1:])
            ),
            "inconsistent_company",
        ),
        (
            lambda case: replace(
                case,
                offers=(
                    case.offers[0],
                    replace(
                        case.offers[1],
                        lines=(replace(case.offers[1].lines[0], quantity=Decimal("99")),),
                    ),
                    case.offers[2],
                ),
            ),
            "inconsistent_comparison_quantity",
        ),
        (
            lambda case: replace(
                case,
                offers=(
                    replace(
                        case.offers[0],
                        lines=(replace(case.offers[0].lines[0], discount=Decimal("1")),),
                    ),
                    *case.offers[1:],
                ),
            ),
            "unsupported_discount",
        ),
        (
            lambda case: replace(
                case,
                offers=(
                    replace(
                        case.offers[0],
                        lines=(replace(case.offers[0].lines[0], tax_ids=("tax:1",)),),
                    ),
                    *case.offers[1:],
                ),
            ),
            "unsupported_tax_semantics",
        ),
    ],
)
def test_odoo_supported_subset_invariants_fail_closed(mutate, expected_code: str) -> None:
    with pytest.raises(DecisionInputAssemblyError) as raised:
        _assemble(mutate(_case()))

    assert raised.value.code == expected_code


def test_missing_supplemental_terms_fail_closed() -> None:
    with pytest.raises(DecisionInputAssemblyError) as raised:
        _assemble(terms=_supplements()[:2])

    assert raised.value.code == "missing_supplemental_terms"


@pytest.mark.parametrize(
    ("field", "expected_code"),
    [
        ("hard_minimum_order_quantity", "missing_supplemental_moq"),
        ("supplier_promised_lead_time_days", "missing_supplemental_lead_time"),
    ],
)
def test_missing_mandatory_supplemental_value_fails_closed(field: str, expected_code: str) -> None:
    first = replace(_supplements()[0], **{field: None})

    with pytest.raises(DecisionInputAssemblyError) as raised:
        _assemble(terms=(first, *_supplements()[1:]))

    assert raised.value.code == expected_code


def test_duplicate_and_unknown_supplemental_identities_fail_closed() -> None:
    duplicate = (*_supplements(), _supplements()[0])
    with pytest.raises(DecisionInputAssemblyError) as raised:
        _assemble(terms=duplicate)
    assert raised.value.code == "duplicate_supplemental_offer_identity"

    unknown = replace(_supplements()[0], offer_id="odoo:purchase.order:unknown")
    with pytest.raises(DecisionInputAssemblyError) as raised:
        _assemble(terms=(unknown, *_supplements()[1:]))
    assert raised.value.code == "unknown_supplemental_offer_identity"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("minimum_order_quantity", Decimal("0")),
        ("lead_time_days", Decimal("-1")),
    ],
)
def test_invalid_supplemental_canonical_values_use_stable_error(field: str, value: Decimal) -> None:
    first = _supplements()[0]
    if field == "minimum_order_quantity":
        first = replace(
            first,
            hard_minimum_order_quantity=replace(first.hard_minimum_order_quantity, value=value),
        )
    else:
        first = replace(
            first,
            supplier_promised_lead_time_days=replace(
                first.supplier_promised_lead_time_days, value=value
            ),
        )

    with pytest.raises(DecisionInputAssemblyError) as raised:
        _assemble(terms=(first, *_supplements()[1:]))

    assert raised.value.code == "invalid_canonical_value"


@pytest.mark.parametrize(
    "attribution",
    [
        SourceAttribution("wrong", "supplier_email", "mail:1", OBSERVED_AT),
        SourceAttribution("minimum_order_quantity", "", "mail:1", OBSERVED_AT),
        SourceAttribution("minimum_order_quantity", "supplier_email", "", OBSERVED_AT),
        SourceAttribution(
            "minimum_order_quantity",
            "supplier_email",
            "mail:1",
            datetime(2026, 9, 18, 8, 0),
        ),
    ],
)
def test_invalid_supplemental_source_attribution_fails_closed(
    attribution: SourceAttribution,
) -> None:
    first = _supplements()[0]
    first = replace(
        first,
        hard_minimum_order_quantity=replace(
            first.hard_minimum_order_quantity,
            attribution=attribution,
        ),
    )

    with pytest.raises(DecisionInputAssemblyError) as raised:
        _assemble(terms=(first, *_supplements()[1:]))

    assert raised.value.code == "invalid_source_attribution"
