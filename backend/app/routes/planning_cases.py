"""Thin bounded planning API; Odoo is read only, never written; stored cases are immutable."""

import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.routing import APIRoute

from application.errors import RepositoryError
from application.planning_cases import (
    PlanningCaseError,
    case_origin,
    create_planning_case,
    get_planning_case,
    normalize_planning_facts,
)
from application.planning_decisions import (
    FinalizePlanningCommand,
    finalize_planning_case,
    retrieve_planning_case,
)
from application.planning_documents import approved_document
from application.planning_history import HISTORY_INPUT_KIND
from application.planning_library import library_query, list_planning_cases
from application.supplier_overview import supplier_overview
from backend.app.api_common import require_trusted_caller
from backend.app.config import settings
from backend.app.dependencies import (
    get_planning_unit_of_work,
    infer_odoo_history_features,
    planning_solver_factory,
    preview_odoo_history,
    render_approved_document,
    resolve_odoo_history_input,
)
from backend.app.planning_case_schemas import (
    OdooHistoryCreateRequest,
    PlanningCaseResponse,
    PlanningFinalDecisionRequest,
    ScenarioRequest,
)


class BoundedPlanningRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def bounded(request: Request):
            if request.method == "POST":
                body = bytearray()
                async for chunk in request.stream():
                    if len(body) + len(chunk) > 256 * 1024:
                        raise HTTPException(
                            413,
                            detail={
                                "code": "request_too_large",
                                "message": "Maximum request size is 256 KiB.",
                            },
                        )
                    body.extend(chunk)
                request._body = bytes(body)
            return await handler(request)

        return bounded


router = APIRouter(
    prefix="/api/v2/procurement/planning-cases",
    tags=["planning-cases"],
    dependencies=[Depends(require_trusted_caller)],
    route_class=BoundedPlanningRoute,
)


def _error(error):
    if isinstance(error, RepositoryError):
        raise HTTPException(
            503,
            detail={
                "code": "planning_dependency_unavailable",
                "message": "Planning persistence or runtime is unavailable.",
            },
        ) from error
    code = error.code if isinstance(error, PlanningCaseError) else "invalid_planning_input"
    status = {
        "planning_case_not_found": 404,
        "idempotency_key_conflict": 409,
        "planning_case_already_finalized": 409,
        "approved_content_hash_mismatch": 409,
        "odoo_history_unavailable": 503,
        "odoo_history_insufficient": 422,
        "odoo_history_model_incompatible": 503,
    }.get(code, 422)
    raise HTTPException(
        status, detail={"code": code, "message": "The planning request could not be accepted."}
    ) from error


def _library(request, parent_id=None):
    allowed = {"origin", "status", "q", "limit", "cursor"}
    try:
        if any(
            key not in allowed or len(request.query_params.getlist(key)) != 1
            for key in request.query_params
        ):
            raise ValueError("Unknown or repeated library parameter.")
        params = dict(request.query_params)
        if "limit" in params:
            if not params["limit"].isascii() or not params["limit"].isdecimal():
                raise ValueError("Invalid limit.")
            params["limit"] = int(params["limit"])
        query = library_query(settings.planning_library_company_id, parent_id=parent_id, **params)
        return list_planning_cases(get_planning_unit_of_work(), query)
    except RepositoryError as error:
        if error.code.startswith("invalid_"):
            raise HTTPException(
                503,
                detail={
                    "code": "invalid_library_data",
                    "message": "Saved library data failed validation.",
                },
            ) from error
        _error(error)
    except (PlanningCaseError, ValueError) as error:
        _error(error)


@router.get("")
def get_library(request: Request):
    return _library(request)


@router.get("/{case_id}/scenarios")
def get_saved_scenarios(case_id: str, request: Request):
    return _library(request, case_id)


def _response(case, replay=False, decision=None):
    return PlanningCaseResponse(
        case_id=case.case_id,
        created_at=case.created_at,
        parent_id=case.parent_id,
        snapshot_hash=case.snapshot_hash,
        snapshot=json.loads(case.snapshot),
        idempotent_replay=replay,
        final_decision=decision,
        origin=case_origin(json.loads(case.snapshot)["facts"]),
    )


def _creation_response(case, replay):
    # Recovering an old creation must also show any later saved human decision.
    decision = None
    if replay:
        case, decision = retrieve_planning_case(get_planning_unit_of_work(), case.case_id)
    return _response(case, replay, decision)


@router.post("/{case_id}/scenarios", response_model=PlanningCaseResponse, status_code=201)
def post_scenario(
    case_id: str,
    request: ScenarioRequest,
    response: Response,
    idempotency_key: Annotated[str, Header()],
):
    try:
        case, replay = create_planning_case(
            get_planning_unit_of_work(),
            idempotency_key,
            parent_id=case_id,
            delta=request.to_delta(),
            infer=infer_odoo_history_features,  # never called: scenarios reuse saved scores
            solver_factory=planning_solver_factory,
        )
        response.status_code = 200 if replay else 201
        return _response(case, replay)
    except (PlanningCaseError, RepositoryError, ValueError) as error:
        _error(error)


@router.get("/odoo-history/preview")
def get_odoo_history_preview(purchase_group_id: Annotated[int, Query(gt=0)]):
    try:
        return preview_odoo_history(purchase_group_id)
    except (PlanningCaseError, RepositoryError, ValueError) as error:
        _error(error)


@router.post("/from-odoo-history", response_model=PlanningCaseResponse, status_code=201)
def post_odoo_history_case(
    request: OdooHistoryCreateRequest, response: Response, idempotency_key: Annotated[str, Header()]
):
    try:
        facts = normalize_planning_facts(request.terms.to_facts())
        intent = {"purchase_group_id": request.purchase_group_id, "facts": facts}
        case, replay = create_planning_case(
            get_planning_unit_of_work(),
            idempotency_key,
            base_intent=intent,
            base_kind=HISTORY_INPUT_KIND,
            load_base=lambda: resolve_odoo_history_input(request.purchase_group_id, facts),
            infer=infer_odoo_history_features,
            solver_factory=planning_solver_factory,
        )
        response.status_code = 200 if replay else 201
        return _creation_response(case, replay)
    except (PlanningCaseError, RepositoryError, ValueError) as error:
        _error(error)


@router.get("/{case_id}/suppliers")
def get_supplier_overview(case_id: str, language: Annotated[Literal["hu", "en"], Query()] = "hu"):
    """Stored-only supplier KPIs, assessment and readable tree path; no Odoo or model."""
    try:
        case = get_planning_case(get_planning_unit_of_work(), case_id)
        return {"case_id": case.case_id} | supplier_overview(json.loads(case.snapshot), language)
    except (PlanningCaseError, RepositoryError) as error:
        _error(error)


@router.get("/{case_id}", response_model=PlanningCaseResponse)
def get_case(case_id: str):
    try:
        case, decision = retrieve_planning_case(get_planning_unit_of_work(), case_id)
        return _response(case, decision=decision)
    except (PlanningCaseError, RepositoryError) as error:
        _error(error)


@router.post("/{case_id}/final-decision", response_model=PlanningCaseResponse, status_code=201)
def post_final_decision(
    case_id: str,
    request: PlanningFinalDecisionRequest,
    response: Response,
    idempotency_key: Annotated[str, Header()],
):
    try:
        case, decision, replay = finalize_planning_case(
            get_planning_unit_of_work(),
            case_id,
            idempotency_key,
            FinalizePlanningCommand(**request.model_dump()),
        )
        response.status_code = 200 if replay else 201
        return _response(case, replay, decision)
    except (PlanningCaseError, RepositoryError, ValueError) as error:
        _error(error)


@router.get("/{case_id}/approved-pdf/{content_hash}")
def get_approved_pdf(
    case_id: str,
    content_hash: str,
    download: bool = False,
    language: Annotated[Literal["hu", "en"], Query()] = "hu",
    kind: Annotated[Literal["plan", "audit"], Query()] = "plan",
):
    """Approved plan or its audit appendix in the UI language; one stored artifact each."""
    try:
        document = approved_document(
            get_planning_unit_of_work(),
            case_id,
            content_hash,
            render_approved_document,
            language,
            kind,
        )
        disposition = "attachment" if download else "inline"
        return Response(
            document.pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'{disposition}; filename="{document.filename}"',
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff",
                "X-Approved-Content-Hash": document.content_hash,
                "X-Content-Version": document.content_version,
                "X-PDF-Reference": document.reference,
                "X-PDF-SHA256": document.pdf_hash,
                "Content-Language": document.language,
                "X-Document-Kind": document.kind,
            },
        )
    except RepositoryError as error:
        raise HTTPException(
            503,
            detail={
                "code": "approved_pdf_unavailable",
                "message": "The approved PDF is unavailable; approval remains saved.",
            },
        ) from error
    except (PlanningCaseError, ValueError) as error:
        _error(error)
