"""Small immutable synthetic contracts, deliberately separate from the WSM model."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction

MONEY_SCALE = 100
RATIO_SCALE = 10_000


def integer(value: int, name: str, minimum: int = 0, maximum: int = 1_000_000) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}].")


def scaled(value: Decimal, name: str, scale: int, lower: int, upper: int) -> int:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal.")
    number = Fraction(value) * scale
    if number.denominator != 1 or not lower <= number <= upper:
        raise ValueError(f"{name} is outside the supported range or precision.")
    return int(number)


@dataclass(frozen=True)
class PriceTier:
    """All-units price from this inclusive quantity threshold, never marginal pricing."""

    minimum_quantity: int
    unit_cost: Decimal

    def __post_init__(self) -> None:
        integer(self.minimum_quantity, "Tier threshold", 1)
        scaled(self.unit_cost, "Tier unit cost", MONEY_SCALE, 1, 100_000_000)


@dataclass(frozen=True)
class Supplier:
    supplier_id: str
    unit_cost: Decimal
    capacity: int
    minimum_quantity: int = 0
    available: bool = True
    deadline_eligible: bool = True
    historical_adherence: Decimal | None = None
    sample_size: int = 0
    price_tiers: tuple[PriceTier, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.supplier_id, str) or not self.supplier_id.strip():
            raise ValueError("Supplier identity must be nonempty.")
        scaled(self.unit_cost, "Unit cost", MONEY_SCALE, 1, 100_000_000)
        integer(self.capacity, "Capacity")
        integer(self.minimum_quantity, "Minimum quantity")
        integer(self.sample_size, "Sample size")
        if type(self.available) is not bool or type(self.deadline_eligible) is not bool:
            raise ValueError("Availability and deadline eligibility must be explicit booleans.")
        if self.historical_adherence is not None:
            scaled(self.historical_adherence, "Historical adherence", RATIO_SCALE, 0, RATIO_SCALE)
        if not isinstance(self.price_tiers, tuple) or any(
            not isinstance(tier, PriceTier) for tier in self.price_tiers
        ):
            raise ValueError("Price tiers must be a tuple of PriceTier values.")
        if self.price_tiers:
            thresholds = tuple(t.minimum_quantity for t in self.price_tiers)
            if thresholds[0] != 1 or thresholds != tuple(sorted(set(thresholds))):
                raise ValueError("Tier thresholds must start at 1 and be strictly increasing.")
            if self.price_tiers[0].unit_cost != self.unit_cost:
                raise ValueError("The first tier price must equal unit_cost.")


@dataclass(frozen=True)
class ProcurementOptimizationInput:
    required_quantity: int
    suppliers: tuple[Supplier, ...]
    max_suppliers: int
    concentration_limit: Decimal | None = None

    def __post_init__(self) -> None:
        integer(self.required_quantity, "Required quantity", 1)
        integer(self.max_suppliers, "Maximum suppliers", 1, 50)
        if not isinstance(self.suppliers, tuple) or not 1 <= len(self.suppliers) <= 50:
            raise ValueError("Supply 1 to 50 suppliers as a tuple.")
        if any(not isinstance(s, Supplier) for s in self.suppliers):
            raise ValueError("Each supplier must be a Supplier value.")
        identities = [s.supplier_id for s in self.suppliers]
        if len(set(identities)) != len(identities):
            raise ValueError("Supplier identities must be unique; one offer per supplier.")
        if self.concentration_limit is not None:
            scaled(self.concentration_limit, "Concentration", RATIO_SCALE, 1, RATIO_SCALE)
        max_price = max(
            scaled(t.unit_cost, "Price", MONEY_SCALE, 1, 100_000_000)
            for s in self.suppliers
            for t in (s.price_tiers or (PriceTier(1, s.unit_cost),))
        )
        if max_price * self.required_quantity > 10**12:
            raise ValueError("PoC numeric bound exceeded: maximum total cost is 10^12 cents.")


class Status(StrEnum):
    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"
    NO_SOLUTION = "no_proven_optimum"
    SOLVER_ERROR = "solver_error"
    HISTORY_UNAVAILABLE = "history_unavailable"


@dataclass(frozen=True)
class Explanation:
    supplier_id: str | None
    code: str
    detail: str


@dataclass(frozen=True)
class ProcurementPlan:
    allocations: tuple[tuple[str, int], ...]
    total_quantity: int
    total_cost: Decimal
    selected_suppliers: tuple[str, ...]
    risk_proxy: Decimal | None
    concentration: Decimal
    selected_supplier_count: int
    cost_premium: Decimal | None
    explanations: tuple[Explanation, ...]


@dataclass(frozen=True)
class OptimizationResult:
    status: Status
    plan: ProcurementPlan | None = None
    reasons: tuple[Explanation, ...] = ()
