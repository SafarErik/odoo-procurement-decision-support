"""Per-supplier overview of one stored planning case, in Hungarian or English.

Built only from the immutable snapshot: history features, the saved Decision Tree
assessment with a readable path, saved terms and the saved plan quantities. It never
reads Odoo, loads a model or solves. Rows are keyed by product and supplier so a later
multi-product case can reuse the shape.
"""

from decimal import Decimal

from application.planning_serialization import read_assessments, read_request, read_result
from supplier_evaluation.contracts import Assessment

LANGUAGES = ("hu", "en")

# feature -> (Hungarian name, English name, value kind)
FEATURE_TEXT = {
    "on_time_rate": ("Határidőre teljesített szállítások aránya", "On-time delivery rate", "pct"),
    "mean_lateness_days": ("Átlagos késés", "Average lateness", "days"),
    "lateness_spread_days": ("Késés szórása", "Lateness spread", "days"),
    "fill_rate": ("Mennyiségi teljesítési arány", "Fill rate", "pct"),
    "partial_share": ("Részszállítások aránya", "Share of partial deliveries", "pct"),
    "order_count": ("Lezárt rendelési sorok száma", "Settled purchase lines", "int"),
    "days_since_last_receipt": (
        "Utolsó beérkezés óta eltelt napok",
        "Days since last receipt",
        "int",
    ),
    # Synthetic demo model (cases stored before P2).
    "delivery_schedule_adherence": ("Ütemezés betartása", "Schedule adherence", "percent100"),
    "historical_completed_count": ("Teljesített szállítások száma", "Completed deliveries", "int"),
}

CLASS_TEXT = {
    "regular": ("rendben", "regular"),
    "problematic": ("problémás", "problematic"),
    "schedule_regular": ("rendben", "regular"),
    "schedule_watch": ("figyelendő", "watch"),
}


def _language(language: str) -> int:
    if language not in LANGUAGES:
        raise ValueError("Supported languages: hu, en.")
    return LANGUAGES.index(language)


def format_number(value, kind: str, language: str, digits: int = 1) -> str:
    """Locale-aware display of one stored feature value (decimal comma in Hungarian)."""
    days = ("nap", "days")[_language(language)]
    text = {
        "pct": lambda v: f"{v * 100:.{digits}f}%",
        "percent100": lambda v: f"{v:.{digits}f}%",
        "days": lambda v: f"{v:.{digits}f} {days}",
        "int": lambda v: f"{v:.{digits - 1}f}",
    }[kind](float(value))
    return text.replace(".", ",") if language == "hu" else text


def metric_display(feature: str, value, language: str) -> str:
    return format_number(value, FEATURE_TEXT.get(feature, ("", "", "int"))[2], language)


def feature_label(feature: str, language: str) -> str:
    return FEATURE_TEXT.get(feature, (feature, feature))[_language(language)]


def class_label(assessment: Assessment, language: str) -> str:
    return CLASS_TEXT[assessment.class_name][_language(language)]


def path_steps(assessment: Assessment, language: str) -> list[dict]:
    """One readable sentence per stored tree split; values are the stored float32 ones."""
    steps = []
    for step in assessment.path:
        kind = FEATURE_TEXT.get(step.feature, ("", "", "int"))[2]
        name = feature_label(step.feature, language)
        # Add decimals until rounding no longer hides the side of the threshold.
        for digits in (1, 2, 3, 4):
            value = format_number(step.value_float32, kind, language, digits)
            threshold = format_number(step.threshold, kind, language, digits)
            if value != threshold:
                break
        below = step.operator == "<="
        text = (
            f"{name}: {value} – legfeljebb {threshold}."
            if language == "hu" and below
            else f"{name}: {value} – {threshold} felett."
            if language == "hu"
            else f"{name}: {value}, at most {threshold}."
            if below
            else f"{name}: {value}, above {threshold}."
        )
        steps.append(
            {
                "feature": step.feature,
                "label": name,
                "value": step.value_float32,
                "operator": step.operator,
                "threshold": step.threshold,
                "text": text,
            }
        )
    return steps


def leaf_text(assessment: Assessment, language: str) -> str:
    regular, flagged = assessment.leaf_counts
    total = regular + flagged
    score = str(assessment.score).replace(".", ",") if language == "hu" else str(assessment.score)
    if language == "hu":
        return (
            f"Hasonló múltbeli esetek: {total} esetből {flagged} lett problémás "
            f"a következő időszakban; kockázati pontszám: {score}."
        )
    return (
        f"Similar past cases: {flagged} of {total} became problematic in the following "
        f"period; risk score {score}."
    )


def saved_labels(snapshot: dict) -> dict[str, str]:
    """Odoo display names stored at creation; older snapshots have none (ids are shown)."""
    return {key: value for key, value in snapshot["facts"].get("labels", ())}


def supplier_overview(snapshot: dict, language: str = "hu") -> dict:
    """Per-supplier rows of a validated stored snapshot (callers validate first)."""
    _language(language)
    request = read_request(snapshot["request"])
    assessments = {
        a.snapshot.context.supplier_id: a for a in read_assessments(snapshot["assessments"])
    }
    result = read_result(snapshot["result"])
    plans = (
        () if result.minimum_cost_plan is None else (result.minimum_cost_plan, *result.alternatives)
    )
    quantities = [{a.supplier_id: a.quantity for a in plan.allocations} for plan in plans]
    offers = {s["terms"]["supplier_id"]: s["offer_id"] for s in snapshot["facts"]["suppliers"]}
    requirement = request.requirement
    names = saved_labels(snapshot)
    rows = []
    for terms in request.suppliers:
        assessment = assessments[terms.supplier_id]
        features = assessment.snapshot
        rows.append(
            {
                "supplier_id": terms.supplier_id,
                "product_id": terms.product_id,
                "quantity_unit": terms.quantity_unit,
                "currency": terms.currency,
                "offer_id": offers.get(terms.supplier_id),
                "supplier_name": names.get(terms.supplier_id),
                "product_name": names.get(terms.product_id),
                "unit_name": names.get(terms.quantity_unit),
                "offer_reference": names.get(offers.get(terms.supplier_id)),
                "terms": {
                    "unit_price": str(terms.unit_price),
                    "capacity": terms.capacity,
                    "available": terms.available,
                    "minimum_order_quantity": terms.minimum_order.quantity,
                    "promised_date": terms.promised_date.isoformat(),
                },
                "history": {
                    "source_type": features.source_type,
                    "feature_version": features.feature_version,
                    "window_start": features.history_start.isoformat(),
                    "window_end": features.history_end.isoformat(),
                    "cutoff": features.cutoff.isoformat(),
                    "metrics": [
                        {
                            "feature": name,
                            "label": feature_label(name, language),
                            "value": value,
                            "display": metric_display(name, value, language),
                        }
                        for name, value in zip(features.feature_names, features.values, strict=True)
                    ],
                },
                "assessment": {
                    "class": assessment.class_name,
                    "class_label": class_label(assessment, language),
                    "score": str(assessment.score),
                    "similar_cases": sum(assessment.leaf_counts),
                    "problematic_cases": assessment.leaf_counts[1],
                    "model_id": assessment.model_id,
                    "training_id": assessment.training_id,
                    "valid_until": assessment.valid_until.isoformat(),
                    "path": path_steps(assessment, language),
                    "summary": leaf_text(assessment, language),
                },
                "allocation": {
                    "minimum_cost_quantity": quantities[0].get(terms.supplier_id, 0)
                    if quantities
                    else None,
                    "alternative_quantities": [q.get(terms.supplier_id, 0) for q in quantities[1:]],
                },
            }
        )
    return {
        "product_id": requirement.product_id,
        "product_name": names.get(requirement.product_id),
        "approved_quantity": requirement.approved_quantity,
        "quantity_unit": requirement.quantity_unit,
        "currency": requirement.currency,
        "language": language,
        "suppliers": rows,
    }


def money_text(value: Decimal, language: str) -> str:
    """Thousands-grouped amount; at least two decimals, never rounding stored digits."""
    text = f"{value:,.2f}" if value == value.quantize(Decimal("0.01")) else f"{value:,}"
    if language == "hu":
        return text.replace(",", " ").replace(".", ",")
    return text
