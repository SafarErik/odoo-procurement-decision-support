"""Immutable canonical models used by the procurement Decision Core."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from decision_core.errors import DomainValidationError

WEIGHT_SUM_TOLERANCE = Decimal("0.000001")


class Criterion(StrEnum):
    """Criteria supported by the first Weighted Sum Model increment."""

    UNIT_PRICE = "unit_price"
    LEAD_TIME_DAYS = "lead_time_days"


class CriterionDirection(StrEnum):
    """Whether a criterion rewards lower or higher raw values."""

    COST = "cost"
    BENEFIT = "benefit"


class Constraint(StrEnum):
    """Hard constraints evaluated before an offer can be scored."""

    MINIMUM_ORDER_QUANTITY = "minimum_order_quantity"


def _validate_identifier(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{field_name} must not be empty.")


def _validate_decimal(value: Decimal, field_name: str) -> None:
    if not isinstance(value, Decimal):
        raise DomainValidationError(f"{field_name} must be provided as a Decimal.")
    if not value.is_finite():
        raise DomainValidationError(f"{field_name} must be finite.")


@dataclass(frozen=True, slots=True)
class PurchaseRequirement:
    """A requested quantity that supplier offers must be able to satisfy."""

    requirement_id: str
    requested_quantity: Decimal

    def __post_init__(self) -> None:
        _validate_identifier(self.requirement_id, "Requirement identifier")
        _validate_decimal(self.requested_quantity, "Requested quantity")
        if self.requested_quantity <= 0:
            raise DomainValidationError("Requested quantity must be greater than zero.")


@dataclass(frozen=True, slots=True)
class SupplierOffer:
    """Canonical supplier offer independent of any ERP representation."""

    offer_id: str
    supplier_id: str
    unit_price: Decimal
    lead_time_days: Decimal
    minimum_order_quantity: Decimal

    def __post_init__(self) -> None:
        _validate_identifier(self.offer_id, "Offer identifier")
        _validate_identifier(self.supplier_id, "Supplier identifier")
        _validate_decimal(self.unit_price, "Unit price")
        _validate_decimal(self.lead_time_days, "Lead time")
        _validate_decimal(self.minimum_order_quantity, "Minimum order quantity")
        if self.unit_price <= 0:
            raise DomainValidationError("Unit price must be greater than zero.")
        if self.lead_time_days < 0:
            raise DomainValidationError("Lead time must not be negative.")
        if self.minimum_order_quantity <= 0:
            raise DomainValidationError("Minimum order quantity must be greater than zero.")


@dataclass(frozen=True, slots=True)
class StrategicProfile:
    """Named weights for the criteria supported by this increment."""

    name: str
    unit_price_weight: Decimal
    lead_time_weight: Decimal

    def __post_init__(self) -> None:
        _validate_identifier(self.name, "Strategic profile name")
        _validate_decimal(self.unit_price_weight, "Unit price weight")
        _validate_decimal(self.lead_time_weight, "Lead time weight")
        if self.unit_price_weight < 0 or self.lead_time_weight < 0:
            raise DomainValidationError("Criterion weights must not be negative.")

        total = self.unit_price_weight + self.lead_time_weight
        if total > Decimal("1") or Decimal("1") - total > WEIGHT_SUM_TOLERANCE:
            raise DomainValidationError(
                "Supported criterion weights must sum to no more than 1 and be within "
                f"{WEIGHT_SUM_TOLERANCE} below 1."
            )

    @classmethod
    def cost_focused(cls) -> "StrategicProfile":
        """Prioritize unit price over lead time."""

        return cls(
            name="cost-focused",
            unit_price_weight=Decimal("0.7"),
            lead_time_weight=Decimal("0.3"),
        )

    @classmethod
    def urgent(cls) -> "StrategicProfile":
        """Prioritize lead time over unit price."""

        return cls(
            name="urgent",
            unit_price_weight=Decimal("0.3"),
            lead_time_weight=Decimal("0.7"),
        )

    @classmethod
    def balanced(cls) -> "StrategicProfile":
        """Give equal importance to unit price and lead time."""

        return cls(
            name="balanced",
            unit_price_weight=Decimal("0.5"),
            lead_time_weight=Decimal("0.5"),
        )

    def weight_for(self, criterion: Criterion) -> Decimal:
        """Return the configured weight for a supported criterion."""

        if criterion is Criterion.UNIT_PRICE:
            return self.unit_price_weight
        if criterion is Criterion.LEAD_TIME_DAYS:
            return self.lead_time_weight
        raise DomainValidationError(f"Unsupported criterion: {criterion!r}.")


@dataclass(frozen=True, slots=True)
class ExcludedOffer:
    """An offer removed by a hard constraint before normalization."""

    offer: SupplierOffer
    failed_constraint: Constraint
    explanation: str
    requested_quantity: Decimal
    minimum_order_quantity: Decimal


@dataclass(frozen=True, slots=True)
class CriterionContribution:
    """Complete trace of one criterion's contribution to a WSM score."""

    criterion: Criterion
    direction: CriterionDirection
    raw_value: Decimal
    normalized_value: Decimal
    weight: Decimal
    weighted_contribution: Decimal


@dataclass(frozen=True, slots=True)
class RankedOffer:
    """An eligible offer with its deterministic rank and explanation trace."""

    rank: int
    offer: SupplierOffer
    total_score: Decimal
    contributions: tuple[CriterionContribution, ...]


@dataclass(frozen=True, slots=True)
class DecisionResult:
    """Eligible rankings and exclusions produced from one decision evaluation."""

    requirement: PurchaseRequirement
    profile: StrategicProfile
    ranked_offers: tuple[RankedOffer, ...]
    excluded_offers: tuple[ExcludedOffer, ...]

    @property
    def recommended_offer(self) -> RankedOffer | None:
        """Return the highest-ranked eligible offer, if any exists."""

        return self.ranked_offers[0] if self.ranked_offers else None
