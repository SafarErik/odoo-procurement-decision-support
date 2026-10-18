"""Read-only Odoo quotation facts for one explicit comparison group."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


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
    # Odoo display names (identity -> name) read with the facts; for documents only.
    labels: tuple[tuple[str, str], ...] = ()


class ComparisonCaseReader(Protocol):
    async def read_comparison_case(self, purchase_group_id: int) -> OdooComparisonCaseFacts: ...

    async def read_currency_code(self, currency_id: str) -> tuple[str, datetime]: ...


# --- Open quotation-group selection (P2): bounded summaries, no case assembly ---

OPEN_QUOTATION_STATES = frozenset({"draft", "sent", "to approve"})
MAX_LISTED_GROUPS = 20


@dataclass(frozen=True, slots=True)
class QuotationLineSummary:
    product_id: str
    product_name: str
    uom_id: str
    uom_name: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    taxed: bool


@dataclass(frozen=True, slots=True)
class QuotationSummary:
    offer_id: str
    reference: str
    supplier_id: str
    supplier_name: str
    state: str
    company_id: str
    currency_id: str
    currency_code: str
    order_date: datetime
    lines: tuple[QuotationLineSummary, ...]


@dataclass(frozen=True, slots=True)
class QuotationGroupSummary:
    purchase_group_id: int
    name: str
    quotations: tuple[QuotationSummary, ...]


@dataclass(frozen=True, slots=True)
class QuotationGroupListing:
    company_id: str
    groups: tuple[QuotationGroupSummary, ...]
    truncated: bool
    observed_at: datetime


class QuotationGroupLister(Protocol):
    async def list_quotation_groups(self, company_id: str, limit: int) -> QuotationGroupListing: ...


def selection_issue(group: QuotationGroupSummary) -> str | None:
    """Why a group cannot become a planning case; mirrors the case-assembly contract."""
    quotations = group.quotations
    if not 3 <= len(quotations) <= 10:
        return "unsupported_offer_count"
    if any(q.state not in OPEN_QUOTATION_STATES for q in quotations):
        return "not_all_open"
    if any(len(q.lines) != 1 for q in quotations):
        return "not_single_line"
    if len({q.supplier_id for q in quotations}) != len(quotations):
        return "duplicate_supplier"
    if (
        len(
            {
                (q.company_id, q.currency_id, q.lines[0].product_id, q.lines[0].uom_id)
                for q in quotations
            }
        )
        != 1
    ):
        return "mixed_context"
    if any(q.lines[0].discount != 0 or q.lines[0].taxed for q in quotations):
        return "discount_or_tax"
    return None


async def list_open_quotation_groups(
    reader: QuotationGroupLister, company_id: str, limit: int
) -> QuotationGroupListing:
    """Bounded, company-scoped, read-only listing of Odoo quotation groups."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LISTED_GROUPS:
        raise ValueError(f"limit must be between 1 and {MAX_LISTED_GROUPS}")
    listing = await reader.list_quotation_groups(company_id, limit)
    if listing.company_id != company_id or any(
        q.company_id != company_id for g in listing.groups for q in g.quotations
    ):
        raise ValueError("The reader returned quotations of another company.")
    return listing
