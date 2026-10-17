"""Versioned, dependency-free data and assessment contracts."""

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from fractions import Fraction

DATASET_VERSION = "t14-controlled-supplier-contexts-v1"
FEATURE_VERSION = "t14-history-features-v1"
LABEL_VERSION = "t14-next-window-schedule-watch-v1"
MAPPING_VERSION = "t14-leaf-exposure-v1"
ARTIFACT_VERSION = "t14-trusted-tree-v1"
FEATURES = ("delivery_schedule_adherence", "historical_completed_count")
CLASSES = ("schedule_regular", "schedule_watch")
SEED = 17
SYNTHETIC = "t14_synthetic"

# V2: features computed from the bounded Odoo purchase-history export (docs/MODEL_ML.md).
HISTORY_SOURCE = "odoo_purchase_history"
HISTORY_FEATURE_VERSION = "odoo-purchase-history-features-v2"
HISTORY_FEATURES = (
    "on_time_rate",
    "mean_lateness_days",
    "lateness_spread_days",
    "fill_rate",
    "partial_share",
    "order_count",
    "days_since_last_receipt",
)
HISTORY_DATASET_VERSION = "odoo-purchase-history-dataset-v2"
HISTORY_LABEL_VERSION = "next-60d-problematic-v2"
HISTORY_MAPPING_VERSION = "leaf-exposure-odoo-history-v2"
HISTORY_LOOKBACK = timedelta(days=120)
HISTORY_SETTLEMENT = timedelta(days=14)
FEATURE_SETS = {FEATURE_VERSION: FEATURES, HISTORY_FEATURE_VERSION: HISTORY_FEATURES}
# (source_type, mapping_version) -> (dataset_version, label_version, feature_version)
ASSESSMENT_VERSIONS = {
    (SYNTHETIC, MAPPING_VERSION): (DATASET_VERSION, LABEL_VERSION, FEATURE_VERSION),
    (HISTORY_SOURCE, HISTORY_MAPPING_VERSION): (
        HISTORY_DATASET_VERSION,
        HISTORY_LABEL_VERSION,
        HISTORY_FEATURE_VERSION,
    ),
}


def canonical(value: object) -> str:
    def encode(item):
        if isinstance(item, (datetime, Decimal)):
            return str(item)
        raise TypeError(f"Unsupported canonical value: {type(item).__name__}")

    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=encode, allow_nan=False)


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def text_identity(value: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError("Explicit canonical identity/reference required.")


def utc(value: datetime) -> None:
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError("Explicit UTC timestamps required.")


def feature_vector(names: tuple[str, ...], values: tuple[float, ...]) -> tuple[float, ...]:
    if (
        names not in FEATURE_SETS.values()
        or not isinstance(values, tuple)
        or len(values) != len(names)
    ):
        raise ValueError("Exact ordered feature schema required.")
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in values):
        raise ValueError("Missing or nonfinite feature.")
    if names == HISTORY_FEATURES:
        on_time, lateness, spread, fill, partial, count, recency = values
        if (
            not all(0 <= x <= 1 for x in (on_time, fill, partial))
            or not -30 <= lateness <= 400
            or not 0 <= spread <= 400
            or not 3 <= count <= 500
            or int(count) != count
            or not 0 <= recency <= 400
        ):
            raise ValueError("Invalid feature range or insufficient history support.")
        return tuple(float(x) for x in values)
    adherence, count = values
    if not 0 <= adherence <= 100 or not 3 <= count <= 50 or int(count) != count:
        raise ValueError("Invalid feature range or insufficient history support.")
    return tuple(float(x) for x in values)


@dataclass(frozen=True, slots=True)
class Context:
    supplier_id: str
    company_id: str
    product_id: str
    quantity_unit: str

    def __post_init__(self):
        for value in asdict(self).values():
            text_identity(value)

    @property
    def domain(self) -> tuple[str, str, str]:
        return self.company_id, self.product_id, self.quantity_unit


@dataclass(frozen=True, slots=True)
class LineEvidence:
    line_id: str
    context: Context
    expected_arrival: datetime
    completed_at: datetime
    available_at: datetime

    def __post_init__(self):
        text_identity(self.line_id)
        if not isinstance(self.context, Context):
            raise ValueError("Typed receipt context required.")
        for value in (self.expected_arrival, self.completed_at, self.available_at):
            utc(value)
        if self.available_at < self.completed_at:
            raise ValueError("Evidence cannot be available before completion.")


@dataclass(frozen=True, slots=True)
class FeatureSnapshot:
    context: Context
    cutoff: datetime
    history_start: datetime
    history_end: datetime
    evidence_available_at: datetime
    values: tuple[float, ...]
    source_type: str
    source_reference: str
    feature_version: str = FEATURE_VERSION
    feature_names: tuple[str, ...] = FEATURES

    def __post_init__(self):
        if not isinstance(self.context, Context):
            raise ValueError("Typed feature context required.")
        for value in (
            self.cutoff,
            self.history_start,
            self.history_end,
            self.evidence_available_at,
        ):
            utc(value)
        if FEATURE_SETS.get(self.feature_version) != self.feature_names:
            raise ValueError("Incompatible feature version.")
        if self.feature_version == HISTORY_FEATURE_VERSION:
            window_ok = (
                self.history_end - self.history_start == HISTORY_LOOKBACK
                and self.cutoff - self.history_end == HISTORY_SETTLEMENT
            )
        else:
            window_ok = self.history_end - self.history_start == timedelta(days=365) and timedelta(
                0
            ) <= self.cutoff - self.history_end <= timedelta(days=7)
        if not window_ok or not self.history_end <= self.evidence_available_at <= self.cutoff:
            raise ValueError("Future, stale or incompatible history cutoff.")
        feature_vector(self.feature_names, self.values)
        text_identity(self.source_type)
        text_identity(self.source_reference)


@dataclass(frozen=True, slots=True)
class QuantityValidity:
    minimum: int
    maximum: int
    reference: str

    def __post_init__(self):
        if type(self.minimum) is not int or type(self.maximum) is not int:
            raise ValueError("Quantity applicability must use integers.")
        if not 1 <= self.minimum <= self.maximum:
            raise ValueError("Invalid quantity validity range.")
        text_identity(self.reference)


@dataclass(frozen=True, slots=True)
class PathStep:
    node_id: int
    feature: str
    value_float32: float
    operator: str
    threshold: float

    def __post_init__(self):
        if (
            type(self.node_id) is not int
            or self.node_id < 0
            or self.feature not in FEATURES + HISTORY_FEATURES
            or type(self.value_float32) is not float
            or not math.isfinite(self.value_float32)
            or type(self.threshold) is not float
            or not math.isfinite(self.threshold)
            or self.operator != ("<=" if self.value_float32 <= self.threshold else ">")
        ):
            raise ValueError("Invalid tree-path condition.")


@dataclass(frozen=True, slots=True)
class Assessment:
    snapshot: FeatureSnapshot
    quantities: QuantityValidity
    valid_until: datetime
    predicted_class: int
    score: Decimal
    model_id: str
    training_id: str
    leaf_id: int
    leaf_counts: tuple[int, int]
    path: tuple[PathStep, ...]
    mapping_version: str = MAPPING_VERSION
    dataset_version: str = DATASET_VERSION
    label_version: str = LABEL_VERSION

    def __post_init__(self):
        if not isinstance(self.snapshot, FeatureSnapshot) or not isinstance(
            self.quantities, QuantityValidity
        ):
            raise ValueError("Typed assessment evidence/validity required.")
        utc(self.valid_until)
        if self.valid_until != self.snapshot.cutoff + timedelta(days=30):
            raise ValueError("Invalid assessment time validity.")
        versions = ASSESSMENT_VERSIONS.get((self.snapshot.source_type, self.mapping_version))
        if versions != (
            self.dataset_version,
            self.label_version,
            self.snapshot.feature_version,
        ) or any(
            getattr(step, "feature", None) not in self.snapshot.feature_names for step in self.path
        ):
            raise ValueError("Incompatible assessment version/provenance.")
        if type(self.predicted_class) is not int or self.predicted_class not in (0, 1):
            raise ValueError("Invalid supplier class.")
        if (
            not isinstance(self.leaf_counts, tuple)
            or len(self.leaf_counts) != 2
            or any(type(x) is not int or x < 0 for x in self.leaf_counts)
            or sum(self.leaf_counts) < 10
        ):
            raise ValueError("Insufficient leaf support.")
        from decimal import ROUND_HALF_UP, localcontext

        with localcontext() as ctx:
            ctx.prec = 28
            expected = (Decimal(self.leaf_counts[1]) / sum(self.leaf_counts)).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
        if (
            not isinstance(self.score, Decimal)
            or not self.score.is_finite()
            or not 0 <= self.score <= 1
            or self.score != expected
            or self.predicted_class != int(self.leaf_counts[1] > self.leaf_counts[0])
        ):
            raise ValueError("Invalid risk score, direction or class mapping.")
        for value in (self.model_id, self.training_id):
            text_identity(value)
        if not isinstance(self.path, tuple) or any(not isinstance(s, PathStep) for s in self.path):
            raise ValueError("Actual tree path required.")

    @property
    def reference(self) -> str:
        return digest(asdict(self))

    @property
    def class_name(self) -> str:
        return CLASSES[self.predicted_class]

    @property
    def raw_class1_fraction(self) -> Fraction:
        return Fraction(self.leaf_counts[1], sum(self.leaf_counts))
