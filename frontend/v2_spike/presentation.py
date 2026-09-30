"""Display formatting only: never compute a procurement plan or predict supplier risk."""

from decimal import Decimal

from frontend.v2_spike.contracts import PlanDTO


class PlanView(PlanDTO):
    cost_display: str
    premium_display: str
    risk_display: str
    share_display: str
    color: str


COLORS = {"minimum": "#397BA6", "balanced": "#0B7773", "lower": "#AF782B"}


def plan_view(plan: PlanDTO) -> PlanView:
    return PlanView(
        **plan.model_dump(),
        cost_display=f"€{Decimal(plan.total_cost):,.2f}",
        premium_display=f"{Decimal(plan.cost_premium):.1%}",
        risk_display=f"{Decimal(plan.risk_exposure):.4f}",
        share_display=f"{Decimal(plan.largest_share):.0%}",
        color=COLORS[plan.plan_id],
    )


def tradeoff_point(plan: PlanDTO) -> dict[str, str | float]:
    return {
        "name": plan.title,
        "cost": float(plan.total_cost),
        "risk": float(plan.risk_exposure),
        "plan_id": plan.plan_id,
    }


def allocation_series(plan: PlanDTO) -> list[dict[str, str | float]]:
    return [{"name": "Allocation", **{a.supplier_id: a.share for a in plan.allocations}}]


EMPTY_PLAN = PlanDTO(
    plan_id="",
    title="No plan selected",
    feasible=False,
    quantity=0,
    total_cost="0",
    cost_premium="0",
    risk_exposure="0",
    largest_share="0",
    supplier_count=0,
    allocations=(),
    explanations=(),
)
