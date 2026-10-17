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


class ComparisonCaseReader(Protocol):
    async def read_comparison_case(self, purchase_group_id: int) -> OdooComparisonCaseFacts: ...

    async def read_currency_code(self, currency_id: str) -> tuple[str, datetime]: ...
