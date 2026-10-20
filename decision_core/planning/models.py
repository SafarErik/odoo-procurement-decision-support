"""Immutable one-product planning contracts. Critical business fields are explicit."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction


class InvalidPlanningInput(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise InvalidPlanningInput(code, message)


def identity(value: str, name: str) -> None:
    require(
        isinstance(value, str) and bool(value) and value == value.strip(),
        "invalid_identity",
        f"{name} must be nonempty canonical text.",
    )


def integer(value: int, name: str, minimum: int = 0) -> None:
    require(type(value) is int and value >= minimum, "invalid_quantity", f"Invalid {name}.")


def decimal(value: Decimal, name: str, *, positive: bool = False) -> None:
    require(
        isinstance(value, Decimal)
        and value.is_finite()
        and (value > 0 if positive else value >= 0),
        "invalid_decimal",
        f"{name} must be a finite {'positive' if positive else 'nonnegative'} Decimal.",
    )


@dataclass(frozen=True, slots=True)
class QuantityRange:
    """Known inclusive positive-order applicability; never inferred from quoted quantity."""

    minimum: int
    maximum: int

    def __post_init__(self):
        integer(self.minimum, "range minimum", 1)
        integer(self.maximum, "range maximum", self.minimum)


@dataclass(frozen=True, slots=True)
class MinimumOrder:
    """None explicitly records absence of hard MOQ; absence of this object is invalid."""

    quantity: int | None

    def __post_init__(self):
        if self.quantity is not None:
            integer(self.quantity, "hard MOQ", 1)


@dataclass(frozen=True, slots=True)
class ProcurementRequirement:
    product_id: str
    approved_quantity: int
    quantity_unit: str
    currency: str
    required_date: date

    def __post_init__(self):
        identity(self.product_id, "product ID")
        identity(self.quantity_unit, "integer quantity unit")
        integer(self.approved_quantity, "approved quantity", 1)
        require(
            isinstance(self.currency, str)
            and len(self.currency) == 3
            and self.currency.isascii()
            and self.currency.isalpha()
            and self.currency.isupper(),
            "invalid_currency",
            "Currency must be an explicit three-letter uppercase context; no conversion.",
        )
        require(type(self.required_date) is date, "invalid_date", "Required date must be a date.")


@dataclass(frozen=True, slots=True)
class SupplierTerms:
    supplier_id: str
    product_id: str
    quantity_unit: str
    currency: str
    unit_price: Decimal
    capacity: int
    available: bool
    minimum_order: MinimumOrder
    price_quantities: QuantityRange
    delivery_quantities: QuantityRange
    promised_date: date

    def __post_init__(self):
        for value, name in (
            (self.supplier_id, "supplier ID"),
            (self.product_id, "product ID"),
            (self.quantity_unit, "quantity unit"),
            (self.currency, "currency"),
        ):
            identity(value, name)
        decimal(self.unit_price, "unit price", positive=True)
        integer(self.capacity, "capacity")
        require(type(self.available) is bool, "unknown_availability", "Availability must be known.")
        require(
            isinstance(self.minimum_order, MinimumOrder),
            "unknown_moq",
            "Supply hard MOQ or explicitly record its absence.",
        )
        require(
            isinstance(self.price_quantities, QuantityRange)
            and isinstance(self.delivery_quantities, QuantityRange),
            "unknown_commercial_applicability",
            "Price and delivery applicability ranges must both be known.",
        )
        require(type(self.promised_date) is date, "unknown_delivery", "Supply a promised date.")


@dataclass(frozen=True, slots=True)
class RiskCoefficient:
    """Higher [0,1] score means greater undesirable exposure, never calibrated probability."""

    supplier_id: str
    value: Decimal
    valid_quantities: QuantityRange

    def __post_init__(self):
        identity(self.supplier_id, "risk supplier ID")
        decimal(self.value, "risk coefficient")
        require(self.value <= 1, "invalid_risk", "Risk coefficient must be in [0,1].")
        require(
            isinstance(self.valid_quantities, QuantityRange),
            "unknown_risk_validity",
            "Risk quantity applicability must be explicit.",
        )


@dataclass(frozen=True, slots=True)
class PlanningPolicy:
    max_suppliers: int
    concentration_limit: Decimal | None
    epsilons: tuple[Decimal, ...]
    # Cost allowance for the balanced (min–max supplier share) alternative; None skips it.
    # Recorded only when set, so snapshots saved before it existed keep their exact JSON.
    diversification_epsilon: Decimal | None = field(default=None, metadata={"omit_default": True})

    def __post_init__(self):
        integer(self.max_suppliers, "maximum supplier count", 1)
        if self.diversification_epsilon is not None:
            decimal(self.diversification_epsilon, "diversification epsilon")
        if self.concentration_limit is not None:
            decimal(self.concentration_limit, "concentration", positive=True)
            require(self.concentration_limit <= 1, "invalid_concentration", "Limit exceeds 1.")
        require(isinstance(self.epsilons, tuple), "invalid_policy", "Epsilons must be a tuple.")
        for epsilon in self.epsilons:
            decimal(epsilon, "epsilon")


@dataclass(frozen=True, slots=True)
class PlanningRequest:
    requirement: ProcurementRequirement
    suppliers: tuple[SupplierTerms, ...]
    policy: PlanningPolicy
    risk_coefficients: tuple[RiskCoefficient, ...] | None

    def __post_init__(self):
        require(
            isinstance(self.requirement, ProcurementRequirement)
            and isinstance(self.policy, PlanningPolicy),
            "invalid_request",
            "Requirement and policy must be typed.",
        )
        require(
            isinstance(self.suppliers, tuple)
            and bool(self.suppliers)
            and all(isinstance(s, SupplierTerms) for s in self.suppliers),
            "invalid_suppliers",
            "Supply a nonempty tuple of supplier terms.",
        )
        require(
            len({s.supplier_id for s in self.suppliers}) == len(self.suppliers),
            "duplicate_supplier",
            "Exactly one offer per supplier is supported.",
        )
        r = self.requirement
        require(
            all(
                (s.product_id, s.quantity_unit, s.currency)
                == (r.product_id, r.quantity_unit, r.currency)
                for s in self.suppliers
            ),
            "incompatible_commercial_context",
            "Product, integer unit and currency must match; no implicit conversion.",
        )
        if self.risk_coefficients is not None:
            require(
                isinstance(self.risk_coefficients, tuple)
                and all(isinstance(c, RiskCoefficient) for c in self.risk_coefficients),
                "invalid_risk",
                "Risk coefficients must be typed tuples or explicit None for cost-only.",
            )
            names = [c.supplier_id for c in self.risk_coefficients]
            require(
                len(set(names)) == len(names)
                and set(names) <= {s.supplier_id for s in self.suppliers},
                "invalid_risk_join",
                "Risk IDs must be unique and belong to the input suppliers.",
            )


class PlanningStatus(StrEnum):
    INVALID_INPUT = "invalid_input"
    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"
    NO_PROVEN_OPTIMUM = "no_proven_optimum"
    SOLVER_ERROR = "solver_error"


@dataclass(frozen=True, slots=True)
class Explanation:
    code: str
    detail: str
    supplier_id: str | None = None


@dataclass(frozen=True, slots=True)
class Allocation:
    supplier_id: str
    quantity: int


@dataclass(frozen=True, slots=True)
class ProcurementPlan:
    allocations: tuple[Allocation, ...]
    total_cost: Decimal
    risk_exposure: Fraction | None
    largest_share: Fraction
    supplier_count: int
    cost_premium: Fraction
    explanations: tuple[Explanation, ...]


@dataclass(frozen=True, slots=True)
class AlternativeRun:
    epsilon: Decimal
    status: PlanningStatus
    plan_index: int | None
    code: str
    # "risk": minimum exposure within the allowance; "diversified": minimum largest share.
    kind: str = field(default="risk", metadata={"omit_default": True})


@dataclass(frozen=True, slots=True)
class PlanningResult:
    status: PlanningStatus
    minimum_cost_plan: ProcurementPlan | None = None
    alternatives: tuple[ProcurementPlan, ...] = ()
    runs: tuple[AlternativeRun, ...] = ()
    explanations: tuple[Explanation, ...] = ()
