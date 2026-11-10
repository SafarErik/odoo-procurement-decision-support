"""Planning cases resource: read one case, save a case, a scenario or the final decision."""

import json

from frontend.api import http
from frontend.api.case_view import PlanningDisplay, map_case
from frontend.api.parsing import is_uuid, required_string
from frontend.config import settings
from frontend.i18n import tr

# Stable marker the state compares against; the shown text is localized separately.
FINAL_DECISION_CONFLICT = "decision_conflict"


def from_odoo_history_url() -> str:
    """POST target that captures Odoo history and saves a new base case."""
    return settings.planning_cases_url + "/from-odoo-history"


def scenarios_url(base_id: str) -> str:
    """Scenarios of base case ``base_id`` (POST saves one, GET lists them)."""
    return f"{settings.planning_cases_url}/{base_id}/scenarios"


def final_decision_url(case_id: str) -> str:
    """POST target that records the one human decision on ``case_id``."""
    return f"{settings.planning_cases_url}/{case_id}/final-decision"


_STATUS_ERRORS = {
    401: "err_rejected",
    403: "err_rejected",
    404: "err_base_missing",
    409: "err_key_conflict",
    422: "err_rejected_inputs",
    413: "err_too_large",
}
_HISTORY_ERRORS = {
    "odoo_history_insufficient": "err_history_insufficient",
    "odoo_history_unavailable": "err_history_unavailable",
    "odoo_history_model_incompatible": "err_history_model",
}


def _rejection(url: str, response, lang: str) -> str | None:
    """Buyer-facing text when the backend definitely refused the request, else None."""
    status = response.status_code
    if url.endswith("/from-odoo-history") and status in (409, 422, 503):
        # FastAPI's own request validation answers 422 with a list-shaped detail; a proxy
        # may answer with no JSON at all. Either way the status decides below.
        try:
            body = response.json()
        except ValueError:
            body = None
        detail = body.get("detail") if isinstance(body, dict) else None
        code = detail.get("code") if isinstance(detail, dict) else None
        if code in _HISTORY_ERRORS:
            return tr(_HISTORY_ERRORS[code], lang)
    if status in _STATUS_ERRORS:
        if url.endswith("/final-decision") and status in (409, 422):
            return FINAL_DECISION_CONFLICT if status == 409 else tr("err_decision_rejected", lang)
        if status == 422 and url.endswith("/from-odoo-history"):
            return tr("err_odoo_changed", lang)
        return tr(_STATUS_ERRORS[status], lang)
    if 400 <= status < 500:  # any other client error is a definite rejection
        return tr("err_rejected_inputs", lang)
    return None


def _check_saved(url: str, payload: dict, key: str, data: dict, case_id: str, display) -> None:
    """Raise ValueError unless the saved case answers exactly this request."""
    if url.endswith("/final-decision"):
        intent = dict(payload)
        intent["actor_reference"] = intent["actor_reference"].strip()
        intent["rationale"] = (intent.get("rationale") or "").strip() or None
        if (
            case_id != url.split("/")[-2]
            or data["final_decision"]["intent"] != intent
            or data["final_decision"]["idempotency_key"] != key
        ):
            raise ValueError("Final decision response does not match pending intent")
    if url.endswith("/scenarios") and display.details["parent_id"] != url.split("/")[-2]:
        raise ValueError("Unexpected parent")
    if not url.endswith("/scenarios") and data["parent_id"] is not None:
        raise ValueError("Unexpected base")
    if url.endswith("/from-odoo-history"):
        facts = data["snapshot"]["facts"]
        capture = json.loads(facts["history"])
        if (
            facts["input_kind"] != "odoo_quotations_odoo_history"
            or facts["comparison_case_id"]
            != f"odoo:purchase.order.group:{payload['purchase_group_id']}"
            or capture["evidence"]["version"] != "odoo-purchase-history-capture-v2"
        ):
            raise ValueError("Unexpected Odoo history capture.")


async def submit_planning_request(
    url: str, payload: dict, key: str, *, lang: str = "en"
) -> tuple[PlanningDisplay | None, str, bool]:
    """One explicit POST to a ``*_url()`` target; never retried automatically.

    Returns ``(case, error, uncertain)``. ``uncertain`` means the save may have happened:
    the caller keeps the exact intent and key so the buyer can resend the same request.
    """
    if not is_uuid(key):
        return None, tr("err_key", lang), False
    try:
        response = await http.send(
            "POST",
            url,
            json=payload,
            headers={"Idempotency-Key": key},
            timeout=http.LONG_TIMEOUT,
        )
        rejection = _rejection(url, response, lang)
        if rejection is not None:
            return None, rejection, False
        if response.status_code not in (200, 201):
            raise ValueError("Uncertain response")
        data = response.json()
        case_id = required_string(data, "case_id")
        if not is_uuid(case_id):
            raise ValueError("Invalid response identity")
        display = map_case(data, case_id, lang)
        _check_saved(url, payload, key, data, case_id, display)
        return display, "", False
    except http.TokenMissing:
        return None, tr("err_token", lang), False
    except (http.Unreachable, *http.DATA_ERRORS):
        return None, tr("err_uncertain", lang), True


async def fetch_planning_case(
    case_id: str, *, lang: str = "en"
) -> tuple[PlanningDisplay | None, str]:
    """One authenticated GET of a stored case; never re-scores, re-solves or retries."""
    if not is_uuid(case_id):
        return None, tr("err_case_id", lang)
    return await http.get_json(
        f"{settings.planning_cases_url}/{case_id}",
        lambda response: map_case(response.json(), case_id, lang),
        lang=lang,
        unavailable="err_case_unavailable",
        invalid="err_case_invalid",
        statuses={404: "err_case_missing", 401: "err_rejected", 403: "err_rejected"},
    )
