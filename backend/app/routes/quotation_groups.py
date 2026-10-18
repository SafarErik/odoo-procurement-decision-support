"""Thin route: open Odoo quotation groups a buyer can turn into a planning case."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from application.odoo_quotations import (
    MAX_LISTED_GROUPS,
    list_open_quotation_groups,
    selection_issue,
)
from application.rfqs import ProcurementDataResponseError, ProcurementDataUnavailable
from backend.app import dependencies
from backend.app.api_common import require_trusted_caller
from backend.app.config import settings
from backend.app.schemas import (
    QuotationGroupListResponse,
    QuotationGroupResponse,
    QuotationLineResponse,
    QuotationResponse,
)

router = APIRouter(
    prefix="/api/v2/procurement/quotation-groups",
    tags=["quotation-groups"],
    dependencies=[Depends(require_trusted_caller)],
)


def _group(group) -> QuotationGroupResponse:
    issue = selection_issue(group)
    first = group.quotations[0]
    line = first.lines[0] if first.lines else None
    return QuotationGroupResponse(
        purchase_group_id=group.purchase_group_id,
        name=group.name,
        product_id=None if line is None else line.product_id,
        product_name=None if line is None else line.product_name,
        quantity=None if line is None else format(line.quantity, "f"),
        uom_name=None if line is None else line.uom_name,
        currency=first.currency_code,
        supplier_count=len({q.supplier_id for q in group.quotations}),
        latest_order_date=max(q.order_date for q in group.quotations),
        selectable=issue is None,
        issue=issue,
        quotations=[
            QuotationResponse(
                offer_id=q.offer_id,
                reference=q.reference,
                supplier_id=q.supplier_id,
                supplier_name=q.supplier_name,
                state=q.state,
                order_date=q.order_date,
                lines=[
                    QuotationLineResponse(
                        product_id=x.product_id,
                        product_name=x.product_name,
                        uom_id=x.uom_id,
                        uom_name=x.uom_name,
                        quantity=format(x.quantity, "f"),
                        unit_price=format(x.unit_price, "f"),
                    )
                    for x in q.lines
                ],
            )
            for q in group.quotations
        ],
    )


@router.get("", response_model=QuotationGroupListResponse)
async def get_quotation_groups(
    limit: Annotated[int, Query(ge=1, le=MAX_LISTED_GROUPS)] = 10,
) -> QuotationGroupListResponse:
    """Newest open groups of the configured company; nothing is stored or written."""
    company = settings.planning_library_company_id
    if not company.startswith("odoo:res.company:"):
        raise HTTPException(
            503,
            detail={
                "code": "quotation_groups_unconfigured",
                "message": "Set PLANNING_LIBRARY_COMPANY_ID to the Odoo company.",
            },
        )
    try:
        listing = await list_open_quotation_groups(
            dependencies.get_comparison_case_reader(), company, limit
        )
    except ProcurementDataUnavailable as error:
        raise HTTPException(
            503, detail={"code": "odoo_unavailable", "message": "Odoo is unavailable."}
        ) from error
    except (ProcurementDataResponseError, ValueError) as error:
        raise HTTPException(
            502,
            detail={"code": "odoo_response_error", "message": "Odoo returned invalid data."},
        ) from error
    items = [_group(g) for g in listing.groups if g.quotations]
    return QuotationGroupListResponse(
        company_id=listing.company_id,
        items=items,
        count=len(items),
        truncated=listing.truncated,
        retrieved_at=listing.observed_at,
    )
