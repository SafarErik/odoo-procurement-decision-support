"""Thin bounded T15 API; controlled facts only, no Odoo writes or live promotion."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.routing import APIRoute

from application.decision_cases import RepositoryError
from application.planning_cases import (
    PlanningCaseError,
    create_planning_case,
    get_planning_case,
    normalize_planning_facts,
)
from backend.app.dependencies import (
    get_planning_unit_of_work,
    infer_planning_features,
    planning_solver_factory,
    resolve_odoo_planning_input,
)
from backend.app.planning_case_schemas import (
    OdooPlanningCreateRequest,
    PlanningCaseResponse,
    PlanningCreateRequest,
    ScenarioRequest,
)
from backend.app.routes.decision_cases import require_trusted_caller


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
    status = {"planning_case_not_found": 404, "idempotency_key_conflict": 409}.get(code, 422)
    raise HTTPException(
        status, detail={"code": code, "message": "The planning request could not be accepted."}
    ) from error


def _response(case, replay=False):
    return PlanningCaseResponse(
        case_id=case.case_id,
        created_at=case.created_at,
        parent_id=case.parent_id,
        snapshot_hash=case.snapshot_hash,
        snapshot=json.loads(case.snapshot),
        idempotent_replay=replay,
    )


@router.post("", response_model=PlanningCaseResponse, status_code=201)
def post_planning_case(
    request: PlanningCreateRequest, response: Response, idempotency_key: Annotated[str, Header()]
):
    try:
        case, replay = create_planning_case(
            get_planning_unit_of_work(),
            idempotency_key,
            facts=request.to_facts(),
            infer=infer_planning_features,
            solver_factory=planning_solver_factory,
        )
        response.status_code = 200 if replay else 201
        return _response(case, replay)
    except (PlanningCaseError, RepositoryError, ValueError) as error:
        _error(error)


@router.post("/from-odoo", response_model=PlanningCaseResponse, status_code=201)
def post_odoo_planning_case(
    request: OdooPlanningCreateRequest,
    response: Response,
    idempotency_key: Annotated[str, Header()],
):
    try:
        facts = normalize_planning_facts(request.controlled_input.to_facts())
        case, replay = create_planning_case(
            get_planning_unit_of_work(),
            idempotency_key,
            base_intent={"purchase_group_id": request.purchase_group_id, "facts": facts},
            load_base=lambda: resolve_odoo_planning_input(request.purchase_group_id, facts),
            infer=infer_planning_features,
            solver_factory=planning_solver_factory,
        )
        response.status_code = 200 if replay else 201
        return _response(case, replay)
    except (PlanningCaseError, RepositoryError, ValueError) as error:
        _error(error)


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
            infer=infer_planning_features,
            solver_factory=planning_solver_factory,
        )
        response.status_code = 200 if replay else 201
        return _response(case, replay)
    except (PlanningCaseError, RepositoryError, ValueError) as error:
        _error(error)


@router.get("/{case_id}", response_model=PlanningCaseResponse)
def get_case(case_id: str):
    try:
        return _response(get_planning_case(get_planning_unit_of_work(), case_id))
    except (PlanningCaseError, RepositoryError) as error:
        _error(error)
