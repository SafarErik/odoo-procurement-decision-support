"""Rules of the New procurement wizard as plain functions (no Reflex state): read and bound
the buyer's form values, record which suggested terms were kept, and word the preview and
review rows. ``CreationMixin`` calls these; the What if…? form reuses the integer rule.

Error results are text keys (``err_quantity`` …); the caller translates them.
"""

from collections.abc import Callable
from copy import deepcopy
from datetime import date
from typing import Any

from frontend.i18n import day, money, number, percent, tr

SUPPLIER_TERM_FIELDS = (
    "capacity",
    "available",
    "minimum_order_quantity",
    "price_quantities",
    "delivery_quantities",
    "promised_date",
)
REQUIREMENT_TERM_FIELDS = ("approved_quantity", "required_date")
RANGE_FIELDS = (("price_quantities", "price"), ("delivery_quantities", "delivery"))
_EDITABLE_TERMS = (
    "capacity",
    "moq",
    "promised_date",
    "price_min",
    "price_max",
    "delivery_min",
    "delivery_max",
)
Name = Callable[[str], str]  # supplier id -> display name in the UI language


def bounded_form_integer(value: Any, *, minimum: int) -> int:
    """A form quantity: 1–4 ASCII digits between ``minimum`` and 1,000, else ValueError."""
    if (
        not isinstance(value, str)
        or not value.isascii()
        or not value.isdecimal()
        or len(value) > 4
        or not minimum <= int(value) <= 1000
    ):
        raise ValueError(f"Enter a whole-number quantity from {minimum} to 1,000.")
    return int(value)


def form_date(value: Any) -> str:
    """An ISO ``YYYY-MM-DD`` form date, returned unchanged, else ValueError."""
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("Invalid date")
    return value


def kept_suggested(source: dict) -> set[str]:
    """Term names the buyer left at the preview suggestion, read from a stored source."""
    reference = source["source_reference"]
    kept = reference.split(";kept-suggested=", 1)[1] if ";kept-suggested=" in reference else ""
    return set(kept.split(",")) - {"none", ""}


def reviewed_source(saved: dict, suggested: dict, fields: tuple[str, ...], as_of: str) -> dict:
    """Buyer-reviewed terms that record which values were kept from the preview suggestion.

    The preview proposes defaults (e.g. capacity, "no MOQ", validity ranges). Saving
    them is an explicit buyer decision, but the stored source must still show which
    values the buyer left at the suggestion instead of claiming they were entered.
    """
    kept = [name for name in fields if saved[name] == suggested[name]]
    return {
        "source_type": "buyer_reviewed_terms",
        "source_reference": "ui-odoo-terms-v2;kept-suggested=" + (",".join(kept) or "none"),
        "observed_at": as_of,
    }


# Preview (steps 2 and 3)


def preview_offers(facts: dict, name: Name, lang: str) -> list[dict[str, str]]:
    """One display row per quoted supplier with its suggested editable terms as strings."""
    currency = facts["requirement"]["currency"]
    return [
        {
            "supplier": s["supplier_id"],
            "name": name(s["supplier_id"]),
            "offer": s["offer_id"],
            "price": money(s["unit_price"], currency, lang),
            "capacity": str(s["capacity"]),
            "moq": str(s["minimum_order_quantity"])
            if s["minimum_order_quantity"] is not None
            else "",
            "promised_date": s["promised_date"],
            **{
                f"{prefix}_{end}": str(s[key][bound])
                for key, prefix in RANGE_FIELDS
                for end, bound in (("min", "minimum"), ("max", "maximum"))
            },
        }
        for s in facts["suppliers"]
    ]


def suggested_values(facts: dict, offers: list[dict[str, str]]) -> dict[str, str]:
    """Initial wizard form values: the suggested demand plus every supplier's editable terms."""
    return {
        "odoo_quantity": str(facts["requirement"]["approved_quantity"]),
        "odoo_required_date": facts["requirement"]["required_date"],
        **{row["supplier"] + "_" + key: row[key] for row in offers for key in _EDITABLE_TERMS},
    }


def history_rows(history: list[dict], name: Name, lang: str) -> list[dict[str, str]]:
    """Odoo delivery history per supplier: on time, mean lateness, fill rate, closed lines."""
    return [
        {
            "supplier": name(r["supplier_id"]),
            "on_time": percent(r["on_time_rate"], lang, 0),
            "lateness": tr("days", lang, value=number(r["mean_lateness_days"], lang, 1)),
            "fill": percent(r["fill_rate"], lang, 0),
            "lines": number(r["order_count"], lang, 0),
        }
        for r in history
    ]


def policy_text(policy: dict, lang: str) -> str:
    """The sourcing policy in one sentence: supplier limit, share limit, cost allowances."""
    return tr(
        "policy_text",
        lang,
        suppliers=policy["max_suppliers"],
        share=percent(policy["concentration_limit"], lang, 0),
        allowance=", ".join(percent(e, lang, 0) for e in policy["epsilons"]),
    )


# Reading the form (step 3 -> 4)


def read_demand(form: dict, today: date) -> tuple[int | None, str | None, dict[str, str]]:
    """Demand quantity and required date from the form, with field-id -> error-key problems."""
    errors: dict[str, str] = {}
    quantity = required = None
    try:
        quantity = bounded_form_integer(form.get("odoo_quantity"), minimum=1)
    except (TypeError, ValueError):
        errors["odoo-quantity"] = "err_quantity"
    try:
        required = form_date(form.get("odoo_required_date"))
        if date.fromisoformat(required) < today:
            errors["odoo-required-date"] = "err_date_past"
    except (TypeError, ValueError):
        errors["odoo-required-date"] = "err_date"
    return quantity, required, errors


def _optional_moq(value: Any) -> int | None:
    return None if value == "" else bounded_form_integer(value, minimum=1)


def reviewed_terms(form: dict, odoo_payload: dict, now) -> tuple[dict | None, dict[str, str]]:
    """The save request from the buyer's form and the Odoo preview payload.

    Returns ``(request, {})`` or ``(None, {field id: error key})``; the order of the
    problems is the order of the fields on screen, so the first one gets focus.
    """
    facts = deepcopy(odoo_payload["controlled_input"])
    quantity, required, errors = read_demand(form, now.date())

    def field(identity, parser, message):
        try:
            return parser(form.get(identity))
        except (ValueError, TypeError):
            errors[identity] = message
            return None

    for supplier in facts["suppliers"]:
        prefix = supplier["supplier_id"]
        supplier["capacity"] = field(
            prefix + "_capacity", lambda v: bounded_form_integer(v, minimum=0), "err_capacity"
        )
        supplier["minimum_order_quantity"] = field(prefix + "_moq", _optional_moq, "err_moq")
        supplier["promised_date"] = field(prefix + "_promised_date", form_date, "err_date")
        for key, name in RANGE_FIELDS:
            low, high = (
                field(
                    f"{prefix}_{name}_{end}",
                    lambda v: bounded_form_integer(v, minimum=1),
                    "err_range",
                )
                for end in ("min", "max")
            )
            if low is not None and high is not None and low > high:
                errors[f"{prefix}_{name}_max"] = "err_range"
            supplier[key] = {"minimum": low, "maximum": high}
    if errors:
        return None, errors
    facts["as_of"] = now.isoformat()
    facts["requirement"]["approved_quantity"] = quantity
    facts["requirement"]["required_date"] = required
    facts["approval_reference"] = f"controlled-demand-{quantity}-t16-odoo-v1"
    suggested = odoo_payload["controlled_input"]
    facts["requirement_source"] = reviewed_source(
        facts["requirement"], suggested["requirement"], REQUIREMENT_TERM_FIELDS, facts["as_of"]
    )
    proposals = {s["supplier_id"]: s for s in suggested["suppliers"]}
    for supplier in facts["suppliers"]:
        supplier["source"] = reviewed_source(
            supplier, proposals[supplier["supplier_id"]], SUPPLIER_TERM_FIELDS, facts["as_of"]
        )
    return {"purchase_group_id": odoo_payload["purchase_group_id"], "terms": facts}, {}


# Review (step 4)


def _kept_labels(source: dict, labels: tuple[tuple[str, str], ...], lang: str) -> str:
    kept = kept_suggested(source)
    return ", ".join(tr(key, lang) for field, key in labels if field in kept) or tr("none", lang)


def review_summary(
    facts: dict, group: dict, unit_name: str, policy: str, captured: str, lang: str
) -> dict:
    """Display strings of the reviewed demand (product, quantity, dates, currency…)."""
    r = facts["requirement"]
    return {
        "kind": "odoo",
        "product": group.get("product", r["product_id"]),
        "group": group.get("name", ""),
        "company": facts["company_id"],
        "quantity": str(r["approved_quantity"]),
        "quantity_display": tr(
            "pieces", lang, quantity=number(r["approved_quantity"], lang), unit=unit_name
        ),
        "unit": r["quantity_unit"],
        "currency": r["currency"],
        "required_date": r["required_date"],
        "required_display": day(r["required_date"], lang),
        "cutoff": facts["as_of"],
        "captured": captured,
        "origin": "Odoo",
        "policy": policy,
        "suggested_requirements": _kept_labels(
            facts["requirement_source"],
            (("approved_quantity", "demand_label"), ("required_date", "required_label")),
            lang,
        ),
    }


def review_rows(facts: dict, name: Name, lang: str) -> list[dict[str, str]]:
    """One display row per supplier with every reviewed term and what stayed suggested."""
    currency = facts["requirement"]["currency"]

    def quantities(s, key):
        values = s[key]
        text = f"{number(values['minimum'], lang, 0)}–{number(values['maximum'], lang, 0)}"
        if key in kept_suggested(s["source"]):
            text += f" ({tr('suggested_value', lang)})"
        return text

    return [
        {
            "name": name(s["supplier_id"]),
            "price": money(s["unit_price"], currency, lang),
            "capacity": str(s["capacity"]),
            "moq": tr("none", lang)
            if s["minimum_order_quantity"] is None
            else str(s["minimum_order_quantity"]),
            "price_range": quantities(s, "price_quantities"),
            "delivery_range": quantities(s, "delivery_quantities"),
            "promised": day(s["promised_date"], lang),
            "available": tr("available" if s["available"] else "not_available", lang),
            "offer": s["offer_id"],
            "suggested": _kept_labels(
                s["source"],
                (
                    ("capacity", "capacity_label"),
                    ("minimum_order_quantity", "moq_label"),
                    ("promised_date", "promised_label"),
                    ("price_quantities", "price_range_label"),
                    ("delivery_quantities", "delivery_range_label"),
                ),
                lang,
            ),
        }
        for s in facts["suppliers"]
    ]
