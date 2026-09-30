"""Explicit decision-time snapshots and outcome-aware history; no ERP or ML dependencies."""

import hashlib
import json
import math
import random
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

DATASET_VERSION = "synthetic-procurement-lines-v1"
TARGET_VERSION = "completed-line-schedule-miss-v1"
SCHEMA_VERSION = "decision-time-features-v1"
FEATURES = (
    "historical_adherence_before_decision",
    "historical_completed_count",
    "requested_quantity_at_decision",
    "decision_month",
)


def digest(value: object) -> str:
    def encode(item: object) -> str:
        if isinstance(item, datetime):
            return item.isoformat()
        raise TypeError(type(item).__name__)

    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=encode).encode()
    ).hexdigest()


def aware(value: datetime) -> None:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("Timestamps must be timezone-aware.")


@dataclass(frozen=True)
class Receipt:
    occurred_at: datetime
    quantity: int

    def __post_init__(self) -> None:
        aware(self.occurred_at)
        if type(self.quantity) is not int or self.quantity <= 0:
            raise ValueError("Receipt quantity must be a positive integer in the canonical UoM.")


@dataclass(frozen=True)
class Observation:
    observation_id: str
    supplier_id: str
    product_id: str
    decision_at: datetime
    expected_arrival_at_decision: datetime | None
    requested_quantity_at_decision: int
    receipts: tuple[Receipt, ...]
    outcome_recorded_at: datetime
    cancelled: bool = False
    return_affected: bool = False
    quantity_changed: bool = False
    reference_snapshot_proven: bool = True

    def __post_init__(self) -> None:
        for identity in (self.observation_id, self.supplier_id, self.product_id):
            if not isinstance(identity, str) or not identity.strip():
                raise ValueError("Identities must be nonempty.")
        aware(self.decision_at)
        aware(self.outcome_recorded_at)
        if self.expected_arrival_at_decision is not None:
            aware(self.expected_arrival_at_decision)
        if type(self.requested_quantity_at_decision) is not int or (
            self.requested_quantity_at_decision <= 0
        ):
            raise ValueError("Requested quantity must be a positive integer.")
        if not isinstance(self.receipts, tuple) or any(
            not isinstance(receipt, Receipt) for receipt in self.receipts
        ):
            raise ValueError("Receipts must be a tuple of canonical Receipt values.")
        for flag in (
            self.cancelled,
            self.return_affected,
            self.quantity_changed,
            self.reference_snapshot_proven,
        ):
            if type(flag) is not bool:
                raise ValueError("Exclusion flags must be explicit booleans.")


@dataclass(frozen=True)
class Outcome:
    observation: Observation
    completed_at: datetime
    available_at: datetime
    schedule_miss: int


def outcome(row: Observation, as_of: datetime) -> tuple[Outcome | None, str | None]:
    aware(as_of)
    for excluded, reason in (
        (row.cancelled, "cancelled"),
        (row.return_affected, "return_affected"),
        (row.quantity_changed, "quantity_changed"),
        (not row.reference_snapshot_proven, "unproven_decision_snapshot"),
        (row.expected_arrival_at_decision is None, "missing_expected_arrival"),
    ):
        if excluded:
            return None, reason
    assert row.expected_arrival_at_decision is not None
    if (
        row.expected_arrival_at_decision < row.decision_at
        or any(r.occurred_at < row.decision_at for r in row.receipts)
        or row.outcome_recorded_at < row.decision_at
    ):
        return None, "ambiguous_timestamps"
    quantity = 0
    for receipt in sorted(row.receipts, key=lambda r: r.occurred_at):
        quantity += receipt.quantity
        if quantity >= row.requested_quantity_at_decision:
            available = max(receipt.occurred_at, row.outcome_recorded_at)
            if available > as_of:
                return None, "outcome_not_available"
            return Outcome(
                row,
                receipt.occurred_at,
                available,
                int(receipt.occurred_at > row.expected_arrival_at_decision),
            ), None
    return None, "incomplete_receipt"


def feature_values(row: Observation, history: tuple[Outcome, ...]) -> dict[str, float]:
    """Only completed AND recorded outcomes strictly before this decision are eligible."""
    prior = [
        item
        for item in history
        if item.observation.observation_id != row.observation_id
        and item.observation.supplier_id == row.supplier_id
        and item.observation.product_id == row.product_id
        and row.decision_at - timedelta(days=365) <= item.completed_at < row.decision_at
        and item.available_at < row.decision_at
    ]
    if len(prior) < 3:
        raise ValueError("Insufficient prior history; no fabricated value or ML score.")
    return {
        FEATURES[0]: sum(1 - item.schedule_miss for item in prior) / len(prior),
        FEATURES[1]: float(len(prior)),
        FEATURES[2]: float(row.requested_quantity_at_decision),
        FEATURES[3]: float(row.decision_at.month),
    }


def feature_vector(values: dict[str, float]) -> tuple[float, ...]:
    if set(values) != set(FEATURES):
        raise ValueError("Only the exact decision-time feature schema is accepted.")
    result = tuple(float(values[name]) for name in FEATURES)
    if not all(math.isfinite(value) for value in result):
        raise ValueError("Features must be finite.")
    if not 0 <= result[0] <= 1 or result[1] < 3 or result[2] <= 0 or not 1 <= result[3] <= 12:
        raise ValueError("Feature values violate their canonical bounds.")
    if any(not result[i].is_integer() for i in (1, 2, 3)):
        raise ValueError("Counts, quantity and calendar month must be integers.")
    return result


@dataclass(frozen=True)
class Example:
    outcome: Outcome
    features: tuple[float, ...]
    history_ids: tuple[str, ...]


@dataclass(frozen=True)
class Dataset:
    train: tuple[Example, ...]
    test: tuple[Example, ...]
    outcomes: tuple[Outcome, ...]
    exclusions: dict[str, int]
    cutoff: datetime
    as_of: datetime
    dataset_hash: str


def build_dataset(rows: tuple[Observation, ...], cutoff: datetime, as_of: datetime) -> Dataset:
    aware(cutoff)
    aware(as_of)
    if cutoff >= as_of:
        raise ValueError("Holdout cutoff must precede dataset export time.")
    if len({r.observation_id for r in rows}) != len(rows):
        raise ValueError("Observation identities must be unique.")
    ordered = tuple(sorted(rows, key=lambda r: (r.decision_at, r.observation_id)))
    exclusions: Counter = Counter()
    outcomes = []
    for row in ordered:
        item, reason = outcome(row, as_of)
        if item is None:
            exclusions[reason] += 1
        else:
            outcomes.append(item)
    pool = tuple(outcomes)
    train_pool = tuple(
        item
        for item in pool
        if item.observation.decision_at < cutoff and item.available_at < cutoff
    )
    train, test = [], []
    for item in pool:
        row = item.observation
        is_train = row.decision_at < cutoff
        if is_train and item.available_at >= cutoff:
            exclusions["purged_training_outcome_after_cutoff"] += 1
            continue
        history = train_pool  # Test outcomes never enter any holdout history feature.
        try:
            features = feature_vector(feature_values(row, history))
        except ValueError:
            exclusions["insufficient_prior_history"] += 1
            continue
        eligible_ids = tuple(
            sorted(
                prior.observation.observation_id
                for prior in history
                if prior.observation.observation_id != row.observation_id
                and prior.observation.supplier_id == row.supplier_id
                and prior.observation.product_id == row.product_id
                and row.decision_at - timedelta(days=365) <= prior.completed_at < row.decision_at
                and prior.available_at < row.decision_at
            )
        )
        (train if is_train else test).append(Example(item, features, eligible_ids))
    return Dataset(
        tuple(train),
        tuple(test),
        pool,
        dict(sorted(exclusions.items())),
        cutoff,
        as_of,
        digest(
            {
                "version": DATASET_VERSION,
                "rows": [asdict(r) for r in ordered],
                "cutoff": cutoff,
                "as_of": as_of,
            }
        ),
    )


def synthetic_rows() -> tuple[Observation, ...]:
    """720 noisy completed lines + six deliberately unusable boundary examples."""
    rng = random.Random(17)
    start = datetime(2025, 1, 1, tzinfo=UTC)
    rows = []
    for week in range(60):
        for supplier in range(12):
            decision = start + timedelta(days=7 * week, hours=supplier)
            requested = rng.choice((50, 100, 200, 350))
            # Hidden propensity is not exported or passed as a feature. Outcomes are stochastic.
            propensity = 0.08 + supplier * 0.035 + (0.24 if requested >= 200 else 0)
            propensity += 0.07 if decision.month in (11, 12) else 0
            late = rng.random() < propensity
            expected = decision + timedelta(days=12)
            completed = expected + timedelta(
                days=rng.randint(1, 14) if late else -rng.randint(0, 5)
            )
            rows.append(
                Observation(
                    f"S{supplier:02}-W{week:02}",
                    f"S{supplier:02}",
                    "P1",
                    decision,
                    expected,
                    requested,
                    (
                        Receipt(decision + timedelta(days=5), requested // 2),
                        Receipt(completed, requested - requested // 2),
                    ),
                    completed + timedelta(days=1),
                )
            )
    from dataclasses import replace

    base = rows[0]
    rows.extend(
        (
            replace(base, observation_id="excluded-cancelled", cancelled=True),
            replace(base, observation_id="excluded-return", return_affected=True),
            replace(base, observation_id="excluded-quantity", quantity_changed=True),
            replace(base, observation_id="excluded-reference", expected_arrival_at_decision=None),
            replace(base, observation_id="excluded-snapshot", reference_snapshot_proven=False),
            replace(base, observation_id="excluded-incomplete", receipts=base.receipts[:1]),
        )
    )
    return tuple(rows)


def synthetic_dataset() -> Dataset:
    return build_dataset(
        synthetic_rows(), datetime(2025, 11, 12, tzinfo=UTC), datetime(2026, 4, 1, tzinfo=UTC)
    )
