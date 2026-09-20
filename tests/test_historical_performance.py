"""ERP-neutral delivery-schedule-adherence policy tests."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from application.historical_performance import (
    HistoricalPerformanceAvailability,
    HistoricalPerformanceError,
    HistoricalPerformanceQuery,
    HistoricalWarningCode,
    InventoryHistoryObservation,
    InventoryHistorySnapshot,
    ReceiptDirection,
    ReceiptEventState,
    acquire_historical_performance,
    calculate_delivery_schedule_adherence,
)

WINDOW_END = datetime(2026, 9, 20, tzinfo=UTC)
WINDOW_START = WINDOW_END - timedelta(days=365)
SUPPLIER_ID = "supplier:1"
COMPANY_ID = "company:1"


def _query(*line_ids: str, supplier_id: str = SUPPLIER_ID) -> HistoricalPerformanceQuery:
    return HistoricalPerformanceQuery(
        supplier_id=supplier_id,
        company_id=COMPANY_ID,
        purchase_line_ids=tuple(line_ids),
        observation_window_start=WINDOW_START,
        observation_window_end=WINDOW_END,
        result_limit=40,
    )


def _observation(
    line_number: int,
    *,
    event_number: int | None = None,
    completed_at: datetime | None = None,
    scheduled_arrival_at: datetime | None = None,
    ordered_quantity: str = "100",
    completed_quantity: str = "100",
    supplier_id: str = SUPPLIER_ID,
    state: ReceiptEventState = ReceiptEventState.COMPLETED,
    direction: ReceiptDirection = ReceiptDirection.SUPPLIER_TO_INTERNAL,
    backorder_of_transfer_id: str | None = None,
    return_of_event_id: str | None = None,
    return_of_transfer_id: str | None = None,
) -> InventoryHistoryObservation:
    event_number = event_number or line_number
    return InventoryHistoryObservation(
        company_id=COMPANY_ID,
        supplier_id=supplier_id,
        purchase_document_id=f"purchase:{line_number}",
        purchase_line_id=f"line:{line_number}",
        product_id="product:1",
        uom_id="uom:1",
        scheduled_arrival_at=(
            WINDOW_START + timedelta(days=200)
            if scheduled_arrival_at is None
            else scheduled_arrival_at
        ),
        receipt_event_id=f"event:{event_number}",
        transfer_id=f"transfer:{event_number}",
        completed_at=completed_at or WINDOW_START + timedelta(days=100),
        ordered_quantity=Decimal(ordered_quantity),
        completed_quantity=Decimal(completed_quantity),
        state=state,
        direction=direction,
        backorder_of_transfer_id=backorder_of_transfer_id,
        return_of_event_id=return_of_event_id,
        return_of_transfer_id=return_of_transfer_id,
    )


def _snapshot(
    query: HistoricalPerformanceQuery,
    observations: tuple[InventoryHistoryObservation, ...],
) -> InventoryHistorySnapshot:
    return InventoryHistorySnapshot(
        query=query,
        observations=observations,
        observed_at=WINDOW_END + timedelta(seconds=1),
        source_type="test_fixture",
        source_reference="fixture:history",
    )


def _calculate(*observations: InventoryHistoryObservation):
    line_ids = tuple(dict.fromkeys(item.purchase_line_id for item in observations)) or ("line:1",)
    return calculate_delivery_schedule_adherence(_snapshot(_query(*line_ids), observations))


@pytest.mark.parametrize(
    ("late_lines", "expected_value"),
    [
        (set(), Decimal("100.00")),
        ({1, 2, 3}, Decimal("0.00")),
        ({2, 3}, Decimal("33.33")),
    ],
)
def test_all_on_time_all_late_and_mixed_lines(
    late_lines: set[int], expected_value: Decimal
) -> None:
    deadline = WINDOW_START + timedelta(days=200)
    observations = tuple(
        _observation(
            line,
            scheduled_arrival_at=deadline,
            completed_at=deadline + (timedelta(seconds=1) if line in late_lines else timedelta()),
        )
        for line in range(1, 4)
    )

    result = _calculate(*observations)

    assert result.value == expected_value
    assert result.sample_size == 3
    assert result.availability is HistoricalPerformanceAvailability.USABLE


def test_exact_deadline_is_adherent_and_immediately_after_is_late() -> None:
    deadline = WINDOW_START + timedelta(days=10)
    result = _calculate(
        _observation(1, scheduled_arrival_at=deadline, completed_at=deadline),
        _observation(
            2,
            scheduled_arrival_at=deadline,
            completed_at=deadline + timedelta(microseconds=1),
        ),
        _observation(3, scheduled_arrival_at=deadline, completed_at=deadline),
    )

    assert result.value == Decimal("66.67")


def test_partial_before_deadline_and_completion_after_is_late() -> None:
    deadline = WINDOW_START + timedelta(days=10)
    result = _calculate(
        _observation(
            1,
            event_number=11,
            completed_quantity="40",
            completed_at=deadline - timedelta(seconds=1),
            scheduled_arrival_at=deadline,
        ),
        _observation(
            1,
            event_number=12,
            completed_quantity="60",
            completed_at=deadline + timedelta(seconds=1),
            scheduled_arrival_at=deadline,
            backorder_of_transfer_id="transfer:11",
        ),
        _observation(2, scheduled_arrival_at=deadline, completed_at=deadline),
        _observation(3, scheduled_arrival_at=deadline, completed_at=deadline),
    )

    assert result.value == Decimal("66.67")
    assert result.sample_size == 3


def test_multiple_pickings_and_late_backorder_count_as_one_late_line() -> None:
    deadline = WINDOW_START + timedelta(days=10)
    result = _calculate(
        _observation(
            1,
            event_number=11,
            completed_quantity="40",
            completed_at=deadline + timedelta(seconds=1),
            scheduled_arrival_at=deadline,
        ),
        _observation(
            1,
            event_number=12,
            completed_quantity="60",
            completed_at=deadline + timedelta(seconds=2),
            scheduled_arrival_at=deadline,
            backorder_of_transfer_id="transfer:11",
        ),
        _observation(2, scheduled_arrival_at=deadline, completed_at=deadline),
        _observation(3, scheduled_arrival_at=deadline, completed_at=deadline),
    )

    assert result.value == Decimal("66.67")
    assert result.sample_size == 3


def test_return_affected_line_is_excluded_with_warning() -> None:
    observations = (
        _observation(1),
        _observation(2),
        _observation(3, completed_at=WINDOW_START + timedelta(days=250)),
        _observation(4, event_number=41),
        _observation(
            4,
            event_number=42,
            direction=ReceiptDirection.INTERNAL_TO_SUPPLIER,
            return_of_event_id="event:41",
            return_of_transfer_id="transfer:41",
        ),
    )

    result = _calculate(*observations)

    assert result.sample_size == 3
    assert result.value == Decimal("66.67")
    assert [(warning.code, warning.affected_line_ids) for warning in result.warnings] == [
        (HistoricalWarningCode.SUPPLIER_RETURN_OBSERVED, ("line:4",))
    ]


def test_cancelled_and_incomplete_lines_are_excluded_deterministically() -> None:
    query = _query("line:1", "line:2", "line:3")
    result = calculate_delivery_schedule_adherence(
        _snapshot(
            query,
            (
                _observation(1, state=ReceiptEventState.CANCELLED),
                _observation(2, completed_quantity="20"),
            ),
        )
    )

    assert result.value is None
    assert result.sample_size == 0
    assert [warning.code for warning in result.warnings] == [
        HistoricalWarningCode.CANCELLED_RECEIPT_OBLIGATION,
        HistoricalWarningCode.INCOMPLETE_RECEIPT,
        HistoricalWarningCode.INCOMPLETE_RECEIPT,
        HistoricalWarningCode.INSUFFICIENT_HISTORY,
        HistoricalWarningCode.NO_ELIGIBLE_LINES,
    ]
    assert result.availability is HistoricalPerformanceAvailability.WITHHELD_NO_ELIGIBLE_LINES


@pytest.mark.parametrize("sample_size", [0, 1, 2])
def test_sample_sizes_below_three_are_withheld_not_zero(sample_size: int) -> None:
    line_ids = tuple(f"line:{line}" for line in range(1, max(sample_size, 1) + 1))
    observations = tuple(_observation(line) for line in range(1, sample_size + 1))
    result = calculate_delivery_schedule_adherence(_snapshot(_query(*line_ids), observations))

    assert result.value is None
    assert result.sample_size == sample_size
    assert HistoricalWarningCode.INSUFFICIENT_HISTORY in {
        warning.code for warning in result.warnings
    }


def test_minimum_sample_size_three_is_usable() -> None:
    result = _calculate(_observation(1), _observation(2), _observation(3))

    assert result.value == Decimal("100.00")
    assert result.sample_size == 3
    assert result.availability is HistoricalPerformanceAvailability.USABLE


def test_half_open_window_includes_start_and_rejects_end() -> None:
    included = _calculate(
        _observation(1, completed_at=WINDOW_START),
        _observation(2, completed_at=WINDOW_START),
        _observation(3, completed_at=WINDOW_START),
    )
    assert included.sample_size == 3

    with pytest.raises(HistoricalPerformanceError) as raised:
        _calculate(_observation(1, completed_at=WINDOW_END))
    assert raised.value.code == "event_outside_observation_window"


def test_supplier_identity_mismatch_fails_closed() -> None:
    with pytest.raises(HistoricalPerformanceError) as raised:
        _calculate(_observation(1, supplier_id="supplier:other"))
    assert raised.value.code == "supplier_identity_mismatch"


def test_warning_order_is_stable_regardless_of_observation_order() -> None:
    query = _query("line:1", "line:2", "line:3")
    observations = (
        _observation(2, completed_quantity="20"),
        _observation(1, state=ReceiptEventState.CANCELLED),
    )
    forward = calculate_delivery_schedule_adherence(_snapshot(query, observations))
    reverse = calculate_delivery_schedule_adherence(_snapshot(query, tuple(reversed(observations))))

    assert forward.warnings == reverse.warnings


def test_over_receipt_uses_completion_threshold_and_warns() -> None:
    deadline = WINDOW_START + timedelta(days=10)
    result = _calculate(
        _observation(
            1,
            event_number=11,
            completed_quantity="100",
            completed_at=deadline,
            scheduled_arrival_at=deadline,
        ),
        _observation(
            1,
            event_number=12,
            completed_quantity="10",
            completed_at=deadline + timedelta(days=1),
            scheduled_arrival_at=deadline,
        ),
        _observation(2, completed_at=deadline, scheduled_arrival_at=deadline),
        _observation(3, completed_at=deadline, scheduled_arrival_at=deadline),
    )

    assert result.value == Decimal("100.00")
    assert result.warnings[0].code is HistoricalWarningCode.OVER_RECEIPT


class _FakeHistoryPort:
    def __init__(self, snapshots: dict[str, InventoryHistorySnapshot]) -> None:
        self.snapshots = snapshots
        self.queries: list[HistoricalPerformanceQuery] = []

    async def read_inventory_history(
        self, query: HistoricalPerformanceQuery
    ) -> InventoryHistorySnapshot:
        self.queries.append(query)
        return self.snapshots[query.supplier_id]


def test_port_is_erp_neutral_and_results_use_stable_supplier_identity() -> None:
    query_b = _query("line:2", supplier_id="supplier:B")
    query_a = _query("line:1", supplier_id="supplier:A")
    snapshots = {
        "supplier:A": _snapshot(query_a, (replace(_observation(1), supplier_id="supplier:A"),)),
        "supplier:B": _snapshot(
            query_b,
            (
                replace(
                    _observation(2),
                    supplier_id="supplier:B",
                    purchase_line_id="line:2",
                ),
            ),
        ),
    }
    port = _FakeHistoryPort(snapshots)

    acquired = asyncio.run(acquire_historical_performance(port, (query_b, query_a)))

    assert [item.performance.supplier_id for item in acquired] == ["supplier:A", "supplier:B"]
    assert [query.supplier_id for query in port.queries] == ["supplier:A", "supplier:B"]


def test_exact_365_day_window_and_request_bounds_are_enforced() -> None:
    with pytest.raises(HistoricalPerformanceError) as window_error:
        replace(_query("line:1"), observation_window_start=WINDOW_START - timedelta(seconds=1))
    assert window_error.value.code == "invalid_observation_window"

    with pytest.raises(HistoricalPerformanceError) as line_error:
        _query(*(f"line:{index}" for index in range(1, 52)))
    assert line_error.value.code == "excessive_purchase_line_ids"

    with pytest.raises(HistoricalPerformanceError) as limit_error:
        replace(_query("line:1"), result_limit=201)
    assert limit_error.value.code == "excessive_result_limit"
