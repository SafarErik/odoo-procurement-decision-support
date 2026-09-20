"""ERP-neutral historical supplier-performance contracts and calculation."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Protocol

MINIMUM_SAMPLE_SIZE = 3
OBSERVATION_WINDOW = timedelta(days=365)
MAX_HISTORY_LINE_IDS = 50
MAX_HISTORY_RESULTS = 200
PERCENT_QUANTUM = Decimal("0.01")


class HistoricalPerformanceError(ValueError):
    """Stable fail-closed error for invalid history requests or evidence."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class HistoricalMetric(StrEnum):
    """Historical metrics accepted by the canonical decision-input contract."""

    DELIVERY_SCHEDULE_ADHERENCE = "delivery_schedule_adherence"


class HistoricalPerformanceAvailability(StrEnum):
    """Whether a historical metric value may be used as contextual data."""

    USABLE = "usable"
    WITHHELD_INSUFFICIENT_SAMPLE = "withheld_insufficient_sample"
    WITHHELD_NO_ELIGIBLE_LINES = "withheld_no_eligible_lines"


class HistoricalWarningCode(StrEnum):
    """Deterministic data-quality and exclusion codes."""

    CANCELLED_RECEIPT_OBLIGATION = "cancelled_receipt_obligation"
    INCOMPLETE_RECEIPT = "incomplete_receipt"
    INSUFFICIENT_HISTORY = "insufficient_history"
    MISSING_EXPECTED_ARRIVAL = "missing_expected_arrival"
    NO_ELIGIBLE_LINES = "no_eligible_lines"
    OVER_RECEIPT = "over_receipt"
    SUPPLIER_RETURN_OBSERVED = "supplier_return_observed"


class ReceiptDirection(StrEnum):
    """ERP-neutral movement direction supported by the accepted policy."""

    SUPPLIER_TO_INTERNAL = "supplier_to_internal"
    INTERNAL_TO_SUPPLIER = "internal_to_supplier"


class ReceiptEventState(StrEnum):
    """Receipt-event states understood by the neutral calculator."""

    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class HistoricalPerformanceQuery:
    """A bounded request for exact supplier purchase-line history."""

    supplier_id: str
    company_id: str
    purchase_line_ids: tuple[str, ...]
    observation_window_start: datetime
    observation_window_end: datetime
    result_limit: int

    def __post_init__(self) -> None:
        _identifier(self.supplier_id, "supplier_id")
        _identifier(self.company_id, "company_id")
        _aware_time(self.observation_window_start, "observation_window_start")
        _aware_time(self.observation_window_end, "observation_window_end")
        if self.observation_window_end - self.observation_window_start != OBSERVATION_WINDOW:
            _fail(
                "invalid_observation_window",
                "Historical performance requires an exact 365-day half-open window.",
            )
        if not self.purchase_line_ids:
            _fail(
                "missing_purchase_line_ids",
                "At least one exact purchase-line identity is required.",
            )
        if len(self.purchase_line_ids) > MAX_HISTORY_LINE_IDS:
            _fail(
                "excessive_purchase_line_ids",
                f"No more than {MAX_HISTORY_LINE_IDS} purchase-line identities are allowed.",
            )
        for line_id in self.purchase_line_ids:
            _identifier(line_id, "purchase_line_id")
        if len(set(self.purchase_line_ids)) != len(self.purchase_line_ids):
            _fail("duplicate_purchase_line_id", "Purchase-line identities must be unique.")
        if isinstance(self.result_limit, bool) or not isinstance(self.result_limit, int):
            _fail("invalid_result_limit", "The history result limit must be an integer.")
        if not 1 <= self.result_limit <= MAX_HISTORY_RESULTS:
            _fail(
                "excessive_result_limit",
                f"The history result limit must be between 1 and {MAX_HISTORY_RESULTS}.",
            )


@dataclass(frozen=True, slots=True)
class InventoryHistoryObservation:
    """One neutral, relationship-backed receipt or return observation."""

    company_id: str
    supplier_id: str
    purchase_document_id: str
    purchase_line_id: str
    product_id: str
    uom_id: str
    scheduled_arrival_at: datetime | None
    receipt_event_id: str
    transfer_id: str
    completed_at: datetime
    ordered_quantity: Decimal
    completed_quantity: Decimal
    state: ReceiptEventState
    direction: ReceiptDirection
    backorder_of_transfer_id: str | None = None
    return_of_event_id: str | None = None
    return_of_transfer_id: str | None = None


@dataclass(frozen=True, slots=True)
class InventoryHistorySnapshot:
    """Bounded history evidence and source identity returned through the port."""

    query: HistoricalPerformanceQuery
    observations: tuple[InventoryHistoryObservation, ...]
    observed_at: datetime
    source_type: str
    source_reference: str


class HistoricalPerformancePort(Protocol):
    """Port implementable by Odoo or any other bounded history provider."""

    async def read_inventory_history(
        self, query: HistoricalPerformanceQuery
    ) -> InventoryHistorySnapshot: ...


@dataclass(frozen=True, slots=True)
class HistoricalDataWarning:
    """Structured warning for excluded or unusual historical evidence."""

    code: HistoricalWarningCode
    message: str
    affected_line_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.code, HistoricalWarningCode):
            _fail("invalid_history_warning", "Historical warning code is unsupported.")
        if not isinstance(self.message, str) or not self.message.strip():
            _fail("invalid_history_warning", "Historical warning message is required.")
        for line_id in self.affected_line_ids:
            _identifier(line_id, "warning_purchase_line_id")
        if self.affected_line_ids != tuple(sorted(set(self.affected_line_ids))):
            _fail(
                "invalid_history_warning",
                "Historical warning line identities must be unique and sorted.",
            )


@dataclass(frozen=True, slots=True)
class SupplierHistoricalPerformance:
    """One supplier's contextual historical metric and separate sample size."""

    metric_id: HistoricalMetric
    value: Decimal | None
    sample_size: int
    observation_window_start: datetime
    observation_window_end: datetime
    observed_at: datetime
    supplier_id: str
    availability: HistoricalPerformanceAvailability
    warnings: tuple[HistoricalDataWarning, ...]

    def __post_init__(self) -> None:
        if self.metric_id is not HistoricalMetric.DELIVERY_SCHEDULE_ADHERENCE:
            _fail("unsupported_historical_metric", "Historical metric is unsupported.")
        _identifier(self.supplier_id, "supplier_id")
        _aware_time(self.observation_window_start, "observation_window_start")
        _aware_time(self.observation_window_end, "observation_window_end")
        _aware_time(self.observed_at, "observed_at")
        if self.observation_window_end - self.observation_window_start != OBSERVATION_WINDOW:
            _fail(
                "invalid_observation_window",
                "Historical performance requires an exact 365-day half-open window.",
            )
        if isinstance(self.sample_size, bool) or not isinstance(self.sample_size, int):
            _fail("invalid_sample_size", "Historical sample size must be an integer.")
        if self.sample_size < 0:
            _fail("invalid_sample_size", "Historical sample size must not be negative.")
        if not isinstance(self.availability, HistoricalPerformanceAvailability):
            _fail("invalid_history_availability", "Historical availability is unsupported.")
        if not isinstance(self.warnings, tuple) or any(
            not isinstance(warning, HistoricalDataWarning) for warning in self.warnings
        ):
            _fail("invalid_history_warning", "Historical warnings must be typed.")
        warning_keys = tuple(
            (warning.code.value, warning.affected_line_ids) for warning in self.warnings
        )
        if warning_keys != tuple(sorted(set(warning_keys))):
            _fail("invalid_history_warning", "Historical warnings must be unique and sorted.")

        warning_codes = {warning.code for warning in self.warnings}
        if self.sample_size < MINIMUM_SAMPLE_SIZE:
            if self.value is not None:
                _fail(
                    "invalid_withheld_history",
                    "Historical values below the minimum sample must be absent.",
                )
            expected_availability = (
                HistoricalPerformanceAvailability.WITHHELD_NO_ELIGIBLE_LINES
                if self.sample_size == 0
                else HistoricalPerformanceAvailability.WITHHELD_INSUFFICIENT_SAMPLE
            )
            if self.availability is not expected_availability:
                _fail(
                    "invalid_history_availability",
                    "Historical availability does not match the sample size.",
                )
            required_warnings = {HistoricalWarningCode.INSUFFICIENT_HISTORY}
            if self.sample_size == 0:
                required_warnings.add(HistoricalWarningCode.NO_ELIGIBLE_LINES)
            if not required_warnings <= warning_codes:
                _fail(
                    "invalid_history_warning",
                    "Withheld historical values require deterministic sample warnings.",
                )
        else:
            if self.availability is not HistoricalPerformanceAvailability.USABLE:
                _fail(
                    "invalid_history_availability",
                    "A sufficient historical sample must be marked usable.",
                )
            if (
                not isinstance(self.value, Decimal)
                or not self.value.is_finite()
                or not Decimal("0") <= self.value <= Decimal("100")
                or self.value != self.value.quantize(PERCENT_QUANTUM)
            ):
                _fail(
                    "invalid_historical_value",
                    "A usable historical value must be a two-decimal percentage.",
                )


@dataclass(frozen=True, slots=True)
class SourcedSupplierHistoricalPerformance:
    """A canonical history value plus its separate application source metadata."""

    performance: SupplierHistoricalPerformance
    source_type: str
    source_reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.performance, SupplierHistoricalPerformance):
            _fail("invalid_historical_performance", "Historical performance must be typed.")
        _identifier(self.source_type, "source_type")
        _identifier(self.source_reference, "source_reference")


async def acquire_historical_performance(
    port: HistoricalPerformancePort,
    queries: tuple[HistoricalPerformanceQuery, ...],
) -> tuple[SourcedSupplierHistoricalPerformance, ...]:
    """Acquire and calculate one deterministic result for every requested supplier."""

    if not queries:
        _fail("missing_history_queries", "At least one supplier history query is required.")
    supplier_ids = [query.supplier_id for query in queries]
    if len(set(supplier_ids)) != len(supplier_ids):
        _fail("duplicate_supplier_query", "Supplier history queries must be unique.")

    output: list[SourcedSupplierHistoricalPerformance] = []
    for query in sorted(queries, key=lambda item: item.supplier_id):
        snapshot = await port.read_inventory_history(query)
        if snapshot.query != query:
            _fail(
                "history_query_mismatch", "The history source returned a different query context."
            )
        _aware_time(snapshot.observed_at, "observed_at")
        _identifier(snapshot.source_type, "source_type")
        _identifier(snapshot.source_reference, "source_reference")
        output.append(
            SourcedSupplierHistoricalPerformance(
                performance=calculate_delivery_schedule_adherence(snapshot),
                source_type=snapshot.source_type,
                source_reference=snapshot.source_reference,
            )
        )
    return tuple(output)


def calculate_delivery_schedule_adherence(
    snapshot: InventoryHistorySnapshot,
) -> SupplierHistoricalPerformance:
    """Calculate the accepted line-count-weighted operational-schedule metric."""

    query = snapshot.query
    _aware_time(snapshot.observed_at, "observed_at")
    observations_by_line: dict[str, list[InventoryHistoryObservation]] = defaultdict(list)
    event_ids: set[str] = set()
    for observation in snapshot.observations:
        _validate_observation(observation, query)
        if observation.receipt_event_id in event_ids:
            _fail("duplicate_receipt_event", "Receipt-event identities must be unique.")
        event_ids.add(observation.receipt_event_id)
        observations_by_line[observation.purchase_line_id].append(observation)

    warnings: list[HistoricalDataWarning] = []
    adherent_count = 0
    sample_size = 0
    for line_id in sorted(query.purchase_line_ids):
        line_observations = observations_by_line.get(line_id, [])
        if not line_observations:
            warnings.append(_warning(HistoricalWarningCode.INCOMPLETE_RECEIPT, (line_id,)))
            continue
        _validate_line_consistency(line_observations)
        if any(item.state is ReceiptEventState.CANCELLED for item in line_observations):
            warnings.append(
                _warning(HistoricalWarningCode.CANCELLED_RECEIPT_OBLIGATION, (line_id,))
            )
            continue
        if any(
            item.direction is ReceiptDirection.INTERNAL_TO_SUPPLIER
            or item.return_of_event_id is not None
            or item.return_of_transfer_id is not None
            for item in line_observations
        ):
            warnings.append(_warning(HistoricalWarningCode.SUPPLIER_RETURN_OBSERVED, (line_id,)))
            continue
        if any(item.scheduled_arrival_at is None for item in line_observations):
            warnings.append(_warning(HistoricalWarningCode.MISSING_EXPECTED_ARRIVAL, (line_id,)))
            continue

        ordered_quantity = line_observations[0].ordered_quantity
        cumulative = Decimal("0")
        completion_at: datetime | None = None
        for observation in sorted(
            line_observations, key=lambda item: (item.completed_at, item.receipt_event_id)
        ):
            cumulative += observation.completed_quantity
            if completion_at is None and cumulative >= ordered_quantity:
                completion_at = observation.completed_at
        if completion_at is None:
            warnings.append(_warning(HistoricalWarningCode.INCOMPLETE_RECEIPT, (line_id,)))
            continue
        if cumulative > ordered_quantity:
            warnings.append(_warning(HistoricalWarningCode.OVER_RECEIPT, (line_id,)))

        sample_size += 1
        scheduled_arrival_at = line_observations[0].scheduled_arrival_at
        if scheduled_arrival_at is None:  # Narrowing guard after the check above.
            _fail("missing_expected_arrival", "Expected Arrival is required for eligibility.")
        adherent_count += completion_at <= scheduled_arrival_at

    if sample_size == 0:
        warnings.append(_warning(HistoricalWarningCode.NO_ELIGIBLE_LINES))
    if sample_size < MINIMUM_SAMPLE_SIZE:
        warnings.append(_warning(HistoricalWarningCode.INSUFFICIENT_HISTORY))
        value = None
        availability = (
            HistoricalPerformanceAvailability.WITHHELD_NO_ELIGIBLE_LINES
            if sample_size == 0
            else HistoricalPerformanceAvailability.WITHHELD_INSUFFICIENT_SAMPLE
        )
    else:
        value = (Decimal(adherent_count) / Decimal(sample_size) * Decimal("100")).quantize(
            PERCENT_QUANTUM, rounding=ROUND_HALF_UP
        )
        availability = HistoricalPerformanceAvailability.USABLE

    return SupplierHistoricalPerformance(
        metric_id=HistoricalMetric.DELIVERY_SCHEDULE_ADHERENCE,
        value=value,
        sample_size=sample_size,
        observation_window_start=query.observation_window_start,
        observation_window_end=query.observation_window_end,
        observed_at=snapshot.observed_at,
        supplier_id=query.supplier_id,
        availability=availability,
        warnings=tuple(
            sorted(
                warnings,
                key=lambda warning: (warning.code.value, warning.affected_line_ids),
            )
        ),
    )


def _validate_observation(
    observation: InventoryHistoryObservation,
    query: HistoricalPerformanceQuery,
) -> None:
    for value, label in (
        (observation.company_id, "company_id"),
        (observation.supplier_id, "supplier_id"),
        (observation.purchase_document_id, "purchase_document_id"),
        (observation.purchase_line_id, "purchase_line_id"),
        (observation.product_id, "product_id"),
        (observation.uom_id, "uom_id"),
        (observation.receipt_event_id, "receipt_event_id"),
        (observation.transfer_id, "transfer_id"),
    ):
        _identifier(value, label)
    if observation.company_id != query.company_id:
        _fail("company_identity_mismatch", "Historical evidence crosses the requested company.")
    if observation.supplier_id != query.supplier_id:
        _fail("supplier_identity_mismatch", "Historical evidence belongs to another supplier.")
    if observation.purchase_line_id not in query.purchase_line_ids:
        _fail("unexpected_purchase_line", "Historical evidence contains an unrequested line.")
    _aware_time(observation.completed_at, "completed_at")
    if (
        not query.observation_window_start
        <= observation.completed_at
        < query.observation_window_end
    ):
        _fail("event_outside_observation_window", "Receipt evidence leaves the half-open window.")
    if observation.scheduled_arrival_at is not None:
        _aware_time(observation.scheduled_arrival_at, "scheduled_arrival_at")
    for quantity, label in (
        (observation.ordered_quantity, "ordered_quantity"),
        (observation.completed_quantity, "completed_quantity"),
    ):
        if not isinstance(quantity, Decimal) or not quantity.is_finite() or quantity <= 0:
            _fail("invalid_history_quantity", f"{label} must be a positive finite Decimal.")
    if not isinstance(observation.state, ReceiptEventState):
        _fail("unsupported_receipt_state", "Receipt evidence has an unsupported state.")
    if not isinstance(observation.direction, ReceiptDirection):
        _fail("unsupported_receipt_direction", "Receipt evidence has an unsupported direction.")


def _validate_line_consistency(observations: list[InventoryHistoryObservation]) -> None:
    fields = (
        "company_id",
        "supplier_id",
        "purchase_document_id",
        "purchase_line_id",
        "product_id",
        "uom_id",
        "scheduled_arrival_at",
        "ordered_quantity",
    )
    for field_name in fields:
        if len({getattr(item, field_name) for item in observations}) != 1:
            _fail(
                "inconsistent_line_history",
                f"Historical observations disagree on {field_name}.",
            )


def _warning(
    code: HistoricalWarningCode,
    affected_line_ids: tuple[str, ...] = (),
) -> HistoricalDataWarning:
    messages = {
        HistoricalWarningCode.CANCELLED_RECEIPT_OBLIGATION: (
            "The line was excluded because a cancelled receipt obligation was observed."
        ),
        HistoricalWarningCode.INCOMPLETE_RECEIPT: (
            "The line was excluded because full eligible quantity was not completed."
        ),
        HistoricalWarningCode.INSUFFICIENT_HISTORY: (
            f"The metric is withheld because the historical sample size is below "
            f"{MINIMUM_SAMPLE_SIZE}."
        ),
        HistoricalWarningCode.MISSING_EXPECTED_ARRIVAL: (
            "The line was excluded because operational Expected Arrival is missing."
        ),
        HistoricalWarningCode.NO_ELIGIBLE_LINES: (
            "The metric is withheld because the observation window has no eligible lines."
        ),
        HistoricalWarningCode.OVER_RECEIPT: (
            "The line was included, but completed quantity exceeded ordered quantity."
        ),
        HistoricalWarningCode.SUPPLIER_RETURN_OBSERVED: (
            "The line was excluded because supplier-return activity was observed."
        ),
    }
    return HistoricalDataWarning(code, messages[code], tuple(sorted(affected_line_ids)))


def _identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        _fail("invalid_history_identity", f"{label} must be a non-empty stable identity.")


def _aware_time(value: datetime, label: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _fail("invalid_history_timestamp", f"{label} must be timezone-aware.")


def _fail(code: str, message: str) -> None:
    raise HistoricalPerformanceError(code, message)
