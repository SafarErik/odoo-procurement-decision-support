"""The approved plan PDF for the buyer.

Page 1 is the summary: what was approved, the allocation table, the supplier
assessment table and the human decision. Then one order-line page per supplier with a
non-zero approved quantity, and the verification identifiers at the end.
"""

from decimal import Decimal
from fractions import Fraction

from reportlab.platypus import KeepTogether, PageBreak, Spacer

from application.planning_cases import fingerprint
from application.planning_serialization import read_assessments, read_fraction
from application.supplier_overview import class_label, money_text
from document_adapter.formatting import Formatter
from document_adapter.layout import (
    HEADING,
    NOTICE,
    SMALL,
    SUBHEADING,
    TITLE,
    fields,
    grid,
    paragraph,
)


def plan_story(content: dict, f: Formatter) -> list:
    """All flowables of the plan document, in page order."""
    selected = [a for a in content["selected_plan"]["allocations"] if a["quantity"] > 0]
    story = _summary_page(content, f, selected)
    for allocation in selected:
        story += _order_line_page(content, f, allocation)
    story.append(_verification_block(content, f))
    return story


def plan_name(content: dict, f: Formatter) -> str:
    """Minimum-cost plan (index 0), the balanced plan, or the n-th lower-risk alternative.

    A plan counts as balanced only when the diversification run alone proved it; if a
    risk run found the same plan too, it is named as that risk alternative.
    """
    index = content["plan_index"]
    runs = content["planning_snapshot"]["result"]["runs"]
    proved_by = {r.get("kind", "risk") for r in runs if r["plan_index"] == index}
    if index == 0:
        return f.t["minimum_plan"]
    if proved_by == {"diversified"}:
        return f.t["balanced_plan"]
    return f.t["alternative_plan"].format(n=index)


def _summary_page(content: dict, f: Formatter, selected: list) -> list:
    """Data-origin notice, key figures, allocation and assessment tables, the decision."""
    t, audit, plan = f.t, content["human_decision"], content["selected_plan"]
    snapshot = content["planning_snapshot"]
    demand = snapshot["request"]["requirement"]
    origin = snapshot["model_manifest"]["metadata"]["data_origin"]  # checked at approval
    story = [paragraph(t["doc_title"], TITLE), paragraph(t["summary"], SUBHEADING)]
    story.append(paragraph(t[origin], NOTICE))
    if audit["incomplete_comparison"]:
        status = f.outcome(audit["solver_outcome"])
        story.append(paragraph(t["incomplete"].format(status=status), NOTICE))
    story.append(
        fields(
            [
                (t["product"], f.short(demand["product_id"])),
                (t["demand"], f.quantity(demand["approved_quantity"])),
                (t["required_date"], f.day(demand["required_date"])),
                (t["plan"], plan_name(content, f)),
                (t["total_cost"], f.money(plan["total_cost"])),
                (t["supplier_count"], str(plan["supplier_count"])),
                (t["largest_share"], f.percent(read_fraction(plan["largest_share"]))),
                (t["exposure"], f.ratio(read_fraction(plan["risk_exposure"]))),
                (t["premium"], f.percent(read_fraction(plan["cost_premium"]))),
            ]
        )
    )
    story.append(paragraph(t["exposure_note"], SMALL))
    story += _allocation_table(content, f, selected)
    story += _assessment_table(content, f)
    story.append(paragraph(t["decision"], HEADING))
    story.append(
        fields(
            [
                (t["outcome"], t["approved"]),
                (t["decided_by"], audit["actor_reference"]),
                (t["recorded_at"], f.moment(audit["recorded_at"])),
                (t["rationale"], audit["rationale"] or t["no_rationale"]),
            ]
        )
    )
    story.append(Spacer(1, 8))
    story.append(paragraph(t["scope"], SMALL))
    story.append(paragraph(t["proposals_follow"], SMALL))
    return story


def _allocation_table(content: dict, f: Formatter, selected: list) -> list:
    """Supplier, quantity, unit price, line total and share of demand, with a total row."""
    t = f.t
    request = content["planning_snapshot"]["request"]
    approved_quantity = request["requirement"]["approved_quantity"]
    prices = {s["supplier_id"]: s["unit_price"] for s in request["suppliers"]}
    rows = [
        (
            f.short(a["supplier_id"]),
            f.quantity(a["quantity"]),
            f.money(prices[a["supplier_id"]]),
            f.money(Decimal(prices[a["supplier_id"]]) * a["quantity"]),
            f.percent(Fraction(a["quantity"], approved_quantity)),
        )
        for a in selected
    ]
    total = (
        t["total"],
        f.quantity(approved_quantity),
        "",
        f.money(content["selected_plan"]["total_cost"]),
        "",
    )
    return [
        paragraph(t["allocation"], HEADING),
        grid(
            (t["supplier"], t["quantity"], t["unit_price"], t["line_total"], t["share"]),
            rows,
            [140, 85, 85, 95, 68],
            total=total,
        ),
    ]


def _assessment_table(content: dict, f: Formatter) -> list:
    """Every supplier's saved Decision Tree class and risk score, with the score caveat."""
    t = f.t
    rows = [
        (f.short(a.snapshot.context.supplier_id), class_label(a, f.language), f.decimal(a.score))
        for a in read_assessments(content["planning_snapshot"]["assessments"])
    ]
    return [
        paragraph(t["assessments"], HEADING),
        grid((t["supplier"], t["class"], t["score"]), rows, [253, 140, 100]),
        paragraph(t["score_note"], SMALL),
    ]


def _order_line_page(content: dict, f: Formatter, allocation: dict) -> list:
    """One supplier's order line: header, line table, dates and the planning terms used."""
    t = f.t
    snapshot = content["planning_snapshot"]
    demand = snapshot["request"]["requirement"]
    identity = allocation["supplier_id"]
    terms = next(s for s in snapshot["request"]["suppliers"] if s["supplier_id"] == identity)
    offers = {s["terms"]["supplier_id"]: s["offer_id"] for s in snapshot["facts"]["suppliers"]}
    offer = offers.get(identity)
    price = Decimal(terms["unit_price"])
    moq = terms["minimum_order"]["quantity"]
    return [
        PageBreak(),
        paragraph(t["proposal"], TITLE),
        paragraph(f.short(identity), SUBHEADING),
        fields(
            [
                (t["supplier"], f.short(identity)),
                (t["offer"], "—" if offer is None else f.short(offer)),
                (t["product"], f.short(demand["product_id"])),
                (t["case"], content["case_id"]),
                (t["recorded_at"], f.moment(content["human_decision"]["recorded_at"])),
            ]
        ),
        paragraph(t["line"], HEADING),
        grid(
            (
                t["product"],
                t["quantity"],
                t["unit"],
                t["unit_price"],
                t["line_total"],
                t["currency"],
            ),
            [
                (
                    f.short(demand["product_id"]),
                    f.number(allocation["quantity"]),
                    f.unit,
                    money_text(price, f.language),
                    money_text(price * allocation["quantity"], f.language),
                    f.currency,
                )
            ],
            [128, 62, 78, 66, 82, 60],
        ),
        paragraph(t["dates"], HEADING),
        fields(
            [
                (t["required_date"], f.day(demand["required_date"])),
                (t["promised_date"], f.day(terms["promised_date"])),
            ]
        ),
        paragraph(t["terms"], HEADING),
        paragraph(t["terms_note"], SMALL),
        fields(
            [
                (t["moq"], t["none"] if moq is None else f.quantity(moq)),
                (t["capacity"], f.quantity(terms["capacity"])),
                (t["available"], f.yes_no(terms["available"])),
                (t["price_range"], f.quantity_range(terms["price_quantities"])),
                (t["delivery_range"], f.quantity_range(terms["delivery_quantities"])),
            ]
        ),
        Spacer(1, 10),
        paragraph(t["proposal_note"], SMALL),
    ]


def _verification_block(content: dict, f: Formatter) -> KeepTogether:
    """Case id, content hash, data origin, short model id and decision time.

    Kept together so it lands on the last order-line page when it fits there.
    """
    t = f.t
    metadata = content["planning_snapshot"]["model_manifest"]["metadata"]
    return KeepTogether(
        [
            Spacer(1, 6),
            paragraph(t["verification"], HEADING),
            fields(
                [
                    (t["case"], content["case_id"]),
                    (t["content_hash"], fingerprint(content)),
                    (t["data_origin"], t["origin_" + metadata["data_origin"]]),
                    (t["model_id"], metadata["model_id"][:12]),
                    (t["decision_time"], f.moment(content["human_decision"]["recorded_at"])),
                ]
            ),
            paragraph(t["audit_pointer"], SMALL),
        ]
    )
