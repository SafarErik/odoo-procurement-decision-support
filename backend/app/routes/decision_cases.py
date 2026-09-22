"""Thin trusted-caller HTTP boundary for persisted decision cases."""

from datetime import UTC
from decimal import Decimal
from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from application.decision_case_orchestration import (
    CreateDecisionCaseCommand,
    HistorySelection,
    OrchestrationError,
    SupplierHistorySelection,
    create_decision_case,
)
from application.decision_case_serialization import (
    serialize_canonical_input,
    serialize_evaluation,
    serialize_provenance,
    serialize_scoring_policy,
)
from application.decision_cases import (
    DecisionCase,
    DecisionCaseError,
    HumanDecisionCommand,
    HumanDecisionOutcome,
    RepositoryError,
    get_decision_case,
    record_human_decision,
)
from application.decision_input_assembly import (
    SourceAttribution,
    SupplementalOfferTerms,
    SupplementalValue,
)
from backend.app.config import settings
from backend.app.decision_case_schemas import (
    DecisionCaseCreateRequest,
    DecisionCaseResponse,
    FinalDecisionRequest,
    HumanDecisionResponse,
    SourcedDecimalRequest,
)
from backend.app.dependencies import (
    get_comparison_case_reader,
    get_decision_unit_of_work,
    get_historical_performance_reader,
)

_bearer = HTTPBearer(auto_error=False)


def require_trusted_caller(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    """A shared PoC service secret proves possession only, never buyer identity."""
    configured = settings.t12_trusted_caller_token.get_secret_value()
    if not configured:
        raise HTTPException(
            503,
            detail={
                "code": "trusted_caller_unconfigured",
                "message": "The trusted-caller gate is unavailable.",
            },
        )
    if credentials is None or not compare_digest(credentials.credentials, configured):
        raise HTTPException(
            401,
            detail={"code": "unauthorized", "message": "A valid bearer token is required."},
            headers={"WWW-Authenticate": "Bearer"},
        )


router = APIRouter(
    prefix="/api/v1/procurement/decision-cases",
    tags=["decision-cases"],
    dependencies=[Depends(require_trusted_caller)],
)


def _source(value: SourcedDecimalRequest, field: str) -> SupplementalValue:
    return SupplementalValue(
        value=Decimal(value.value),
        attribution=SourceAttribution(
            field, value.source_type, value.source_reference, value.observed_at.astimezone(UTC)
        ),
    )


def _case_response(case: DecisionCase, replay: bool = False) -> DecisionCaseResponse:
    human = case.human_decision
    return DecisionCaseResponse(
        decision_case_id=case.decision_case_id,
        snapshot_version=case.snapshot_version,
        created_at=case.created_at,
        state=case.state.value,
        canonical_input=serialize_canonical_input(case.assembled_input.canonical),
        scoring_policy=serialize_scoring_policy(case.scoring_policy),
        evaluation=serialize_evaluation(case.evaluation),
        provenance=serialize_provenance(case.assembled_input.provenance),
        recommended_offer_id=case.recommended_offer_id,
        human_decision=(
            HumanDecisionResponse(
                outcome=human.outcome.value,
                selected_offer_id=human.selected_offer_id,
                rationale=human.rationale,
                decided_at=human.decided_at,
                actor_reference=human.actor_reference,
                idempotency_key=human.idempotency_key,
            )
            if human is not None
            else None
        ),
        idempotent_replay=replay,
    )


def _http_error(error: OrchestrationError | DecisionCaseError | RepositoryError) -> HTTPException:
    code = error.code
    if code in {
        "creation_idempotency_conflict",
        "idempotency_key_conflict",
        "decision_case_already_finalized",
    }:
        status_code = 409
    elif code == "decision_case_not_found":
        status_code = 404
    elif code in {
        "odoo_unavailable",
        "decision_case_persistence_failed",
        "repository_failure",
        "invalid_database_configuration",
    }:
        status_code = 503
    elif code in {"odoo_response_error", "invalid_comparison_response"}:
        status_code = 502
    else:
        status_code = 422
    message = (
        "Decision persistence is unavailable." if isinstance(error, RepositoryError) else str(error)
    )
    return HTTPException(status_code, detail={"code": code, "message": message})


def _unit_of_work():
    try:
        return get_decision_unit_of_work()
    except RepositoryError as error:
        raise _http_error(error) from error


@router.post(
    "",
    response_model=DecisionCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and store one evaluated decision case",
    description=(
        "Requires a shared PoC bearer secret. The secret does not authenticate "
        "actor_reference or an individual buyer."
    ),
    responses={
        200: {"model": DecisionCaseResponse},
        401: {"description": "Invalid bearer token"},
        409: {"description": "Creation key conflict"},
        422: {"description": "Invalid input"},
        502: {"description": "Invalid Odoo data"},
        503: {"description": "Dependency unavailable"},
    },
)
async def post_decision_case(
    request: DecisionCaseCreateRequest,
    response: Response,
    idempotency_key: Annotated[str, Header()],
) -> DecisionCaseResponse:
    terms = tuple(
        SupplementalOfferTerms(
            item.offer_id,
            _source(item.hard_minimum_order_quantity, "minimum_order_quantity"),
            _source(item.supplier_promised_lead_time_days, "lead_time_days"),
        )
        for item in request.supplemental_terms
    )
    history = None
    if request.history_selection is not None:
        history = HistorySelection(
            request.history_selection.window_end,
            tuple(
                SupplierHistorySelection(item.supplier_id, tuple(item.purchase_line_ids))
                for item in request.history_selection.suppliers
            ),
        )
    command = CreateDecisionCaseCommand(
        request.purchase_group_id, terms, request.scoring_policy_id, history, idempotency_key
    )
    try:
        created = await create_decision_case(
            command,
            comparison_reader=get_comparison_case_reader(),
            history_reader=get_historical_performance_reader(),
            unit_of_work=_unit_of_work(),
        )
    except (OrchestrationError, DecisionCaseError, RepositoryError) as error:
        raise _http_error(error) from error
    if created.replayed:
        response.status_code = 200
    return _case_response(created.decision_case, created.replayed)


@router.get(
    "/{decision_case_id}",
    response_model=DecisionCaseResponse,
    responses={
        401: {"description": "Invalid bearer token"},
        404: {"description": "Case not found"},
        503: {"description": "Persistence unavailable"},
    },
)
def retrieve_decision_case(decision_case_id: str) -> DecisionCaseResponse:
    try:
        case = get_decision_case(_unit_of_work(), decision_case_id)
    except (DecisionCaseError, RepositoryError) as error:
        raise _http_error(error) from error
    return _case_response(case)


@router.post(
    "/{decision_case_id}/final-decision",
    response_model=DecisionCaseResponse,
    responses={
        401: {"description": "Invalid bearer token"},
        404: {"description": "Case not found"},
        409: {"description": "Finalization conflict"},
        422: {"description": "Invalid human decision"},
        503: {"description": "Persistence unavailable"},
    },
)
def finalize_decision_case(
    decision_case_id: str,
    request: FinalDecisionRequest,
    idempotency_key: Annotated[str, Header()],
) -> DecisionCaseResponse:
    try:
        command = HumanDecisionCommand(
            outcome=HumanDecisionOutcome(request.outcome),
            selected_offer_id=request.selected_offer_id,
            rationale=request.rationale,
            decided_at=request.decided_at,
            actor_reference=request.actor_reference,
            idempotency_key=idempotency_key,
        )
        case = record_human_decision(_unit_of_work(), decision_case_id, command)
    except (DecisionCaseError, RepositoryError) as error:
        raise _http_error(error) from error
    return _case_response(case)
