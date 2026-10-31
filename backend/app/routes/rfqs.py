"""Thin HTTP route for the open-RFQ application use case."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from application.rfqs import (
    ProcurementDataResponseError,
    ProcurementDataUnavailable,
    RfqReader,
    list_open_rfqs,
)
from backend.app.api_common import require_trusted_caller
from backend.app.dependencies import get_rfq_reader
from backend.app.schemas import MoneyResponse, RfqListResponse, RfqSummaryResponse

router = APIRouter(
    prefix="/api/v1/procurement",
    tags=["procurement"],
    dependencies=[Depends(require_trusted_caller)],
)


@router.get("/rfqs", response_model=RfqListResponse)
async def get_open_rfqs(
    reader: Annotated[RfqReader, Depends(get_rfq_reader)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> RfqListResponse:
    """Return recent open RFQs without leaking the upstream Odoo contract."""

    try:
        items = await list_open_rfqs(reader, limit)
    except ProcurementDataUnavailable as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "odoo_unavailable",
                "message": "RFQ data is unavailable.",
            },
        ) from error
    except ProcurementDataResponseError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "odoo_response_error",
                "message": "Odoo could not provide RFQ data.",
            },
        ) from error

    return RfqListResponse(
        items=[
            RfqSummaryResponse(
                source_id=item.source_id,
                reference=item.reference,
                vendor_name=item.vendor_name,
                order_date=item.order_date,
                status=item.status,
                total=MoneyResponse(
                    amount=format(item.total.amount, "f"),
                    currency=item.total.currency,
                ),
            )
            for item in items
        ],
        count=len(items),
        retrieved_at=datetime.now(UTC),
    )
