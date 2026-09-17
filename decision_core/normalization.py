"""Reusable min-max normalization for cost and benefit criteria."""

from collections.abc import Sequence
from decimal import Decimal

from decision_core.errors import DomainValidationError
from decision_core.models import CriterionDirection


def normalize_values(
    values: Sequence[Decimal], direction: CriterionDirection
) -> tuple[Decimal, ...]:
    """Normalize finite Decimal values to the inclusive range from zero to one.

    Equal raw values all receive 1 because the criterion cannot distinguish the
    alternatives and should neither penalize them nor cause division by zero.
    """

    if not values:
        raise DomainValidationError("At least one value is required for normalization.")
    if direction not in (CriterionDirection.COST, CriterionDirection.BENEFIT):
        raise DomainValidationError(f"Unsupported criterion direction: {direction!r}.")
    for value in values:
        if not isinstance(value, Decimal):
            raise DomainValidationError("Normalization values must be Decimals.")
        if not value.is_finite():
            raise DomainValidationError("Normalization values must be finite.")

    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        return tuple(Decimal("1") for _value in values)

    span = maximum - minimum
    if direction is CriterionDirection.COST:
        return tuple((maximum - value) / span for value in values)
    return tuple((value - minimum) / span for value in values)
