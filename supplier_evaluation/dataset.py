"""Controlled receipts, leakage-safe preparation and reproducible dataset JSON."""

import json
import random
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from supplier_evaluation.contracts import (
    DATASET_VERSION,
    LABEL_VERSION,
    SEED,
    SYNTHETIC,
    Context,
    FeatureSnapshot,
    LineEvidence,
    canonical,
    digest,
    text_identity,
    utc,
)
from supplier_evaluation.history import prepare_history


@dataclass(frozen=True, slots=True)
class Observation:
    observation_id: str
    context: Context
    cutoff: datetime
    history: tuple[LineEvidence, ...]
    outcomes: tuple[LineEvidence, ...]
    source_reference: str
    source_type: str = SYNTHETIC

    def __post_init__(self):
        text_identity(self.observation_id)
        text_identity(self.source_reference)
        utc(self.cutoff)
        if not isinstance(self.context, Context) or self.source_type != SYNTHETIC:
            raise ValueError("This dataset supports explicitly synthetic observations only.")
        if any(
            not isinstance(lines, tuple) or any(not isinstance(x, LineEvidence) for x in lines)
            for lines in (self.history, self.outcomes)
        ):
            raise ValueError("Typed immutable receipt evidence required.")


@dataclass(frozen=True, slots=True)
class Example:
    observation_id: str
    snapshot: FeatureSnapshot
    label: int
    label_available_at: datetime


@dataclass(frozen=True, slots=True)
class Split:
    train: tuple[Example, ...]
    test: tuple[Example, ...]
    dataset_id: str
    boundary: datetime
    extracted_at: datetime

    def __post_init__(self):
        utc(self.boundary)
        utc(self.extracted_at)
        text_identity(self.dataset_id)
        if (
            not isinstance(self.train, tuple)
            or not isinstance(self.test, tuple)
            or not self.train
            or not self.test
            or any(
                not isinstance(e, Example) or not isinstance(e.snapshot, FeatureSnapshot)
                for e in self.train + self.test
            )
        ):
            raise ValueError("Nonempty train and held-out partitions required.")
        examples = self.train + self.test
        ids = [e.observation_id for e in examples]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate observation identity.")
        keys = [(e.snapshot.context, e.snapshot.cutoff) for e in examples]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate context cutoff.")
        domains = {e.snapshot.context.domain for e in examples}
        if len(domains) != 1:
            raise ValueError("A dataset must have one explicit company/product/unit context.")
        groups = [
            {e.snapshot.context.supplier_id for e in rows} for rows in (self.train, self.test)
        ]
        if groups[0] & groups[1]:
            raise ValueError("Supplier group leakage across train/test.")
        for e in examples:
            utc(e.label_available_at)
            if (
                type(e.label) is not int
                or e.label not in (0, 1)
                or e.snapshot.source_type != SYNTHETIC
                or not e.snapshot.cutoff + timedelta(days=30)
                <= e.label_available_at
                <= self.extracted_at
            ):
                raise ValueError("Invalid or unavailable future outcome label.")
        if any(e.label_available_at >= self.boundary for e in self.train) or any(
            e.snapshot.cutoff < self.boundary for e in self.test
        ):
            raise ValueError("Temporal label-window leakage across split.")


def prepare_features(row: Observation) -> FeatureSnapshot:
    """Outcome data is deliberately never consulted here."""
    return prepare_history(
        row.context, row.cutoff, row.history, row.source_type, row.source_reference
    )


def future_label(row: Observation, extracted_at: datetime) -> tuple[int, datetime]:
    utc(extracted_at)
    end = row.cutoff + timedelta(days=30)
    if len(row.outcomes) != 5 or any(
        line.context != row.context
        or not row.cutoff < line.expected_arrival <= end
        or not row.cutoff < line.completed_at <= end
        or line.available_at > extracted_at
        for line in row.outcomes
    ):
        raise ValueError("Five complete contextual outcomes in the 30-day label window required.")
    available = max(end, *(line.available_at for line in row.outcomes))
    if extracted_at < available:
        raise ValueError("Outcome window is not yet observable.")
    return int(
        sum(line.completed_at > line.expected_arrival for line in row.outcomes) >= 2
    ), available


def prepare_dataset(
    rows: tuple[Observation, ...], *, boundary: datetime, extracted_at: datetime
) -> Split:
    utc(boundary)
    utc(extracted_at)
    if not isinstance(rows, tuple) or any(not isinstance(row, Observation) for row in rows):
        raise ValueError("Typed dataset observations required.")
    ids, cutoffs, line_ids = set(), set(), set()
    train, test = [], []
    for row in sorted(rows, key=lambda x: x.observation_id):
        key = (row.context, row.cutoff)
        if row.observation_id in ids or key in cutoffs:
            raise ValueError("Duplicate observation/context cutoff.")
        ids.add(row.observation_id)
        cutoffs.add(key)
        for line in row.history + row.outcomes:
            if line.line_id in line_ids:
                raise ValueError("Duplicate evidence or history/outcome leakage.")
            line_ids.add(line.line_id)
        label, available = future_label(row, extracted_at)
        example = Example(row.observation_id, prepare_features(row), label, available)
        (train if row.cutoff < boundary else test).append(example)
    return Split(
        tuple(train),
        tuple(test),
        digest([asdict(r) for r in sorted(rows, key=lambda x: x.observation_id)]),
        boundary,
        extracted_at,
    )


def generate_dataset(
    *, domain: tuple[str, str, str] = ("synthetic-company", "synthetic-product", "piece")
) -> tuple[Observation, ...]:
    """Generate synthetic evidence in an explicit context; never import Odoo history."""
    if not isinstance(domain, tuple) or len(domain) != 3:
        raise ValueError("Supply one company/product/unit domain.")
    rng = random.Random(SEED)
    rows = []
    for i in range(240):
        context = Context(f"synthetic-S{i:03}", *domain)
        cutoff = datetime(2026, 1 if i < 160 else 3, 1, tzinfo=UTC)
        count = rng.randint(8, 30)
        past_miss_rate = rng.uniform(0.05, 0.70)
        history = []
        for j in range(count):
            expected = cutoff - timedelta(days=2 + j * 5)
            completed = expected + timedelta(hours=12 if rng.random() < past_miss_rate else -12)
            history.append(
                LineEvidence(
                    f"H:{i}:{j}", context, expected, completed, completed + timedelta(hours=1)
                )
            )
        adherence = (
            sum(line.completed_at <= line.expected_arrival for line in history) / count * 100
        )
        future_miss_rate = 0.65 if adherence < 80 else 0.10
        outcomes = []
        for j in range(5):
            expected = cutoff + timedelta(days=3 + j * 5)
            completed = expected + timedelta(hours=12 if rng.random() < future_miss_rate else -12)
            outcomes.append(
                LineEvidence(
                    f"Y:{i}:{j}", context, expected, completed, completed + timedelta(hours=1)
                )
            )
        rows.append(
            Observation(
                f"observation:{i:03}",
                context,
                cutoff,
                tuple(history),
                tuple(outcomes),
                f"{DATASET_VERSION}:seed={SEED}:{i}",
            )
        )
    return tuple(rows)


BOUNDARY = datetime(2026, 2, 15, tzinfo=UTC)
EXTRACTED_AT = datetime(2026, 4, 1, tzinfo=UTC)


def save_dataset(path: Path, rows: tuple[Observation, ...]) -> None:
    prepare_dataset(rows, boundary=BOUNDARY, extracted_at=EXTRACTED_AT)
    payload = {
        "dataset_version": DATASET_VERSION,
        "label_version": LABEL_VERSION,
        "seed": SEED,
        "boundary": BOUNDARY,
        "extracted_at": EXTRACTED_AT,
        "rows": [asdict(r) for r in rows],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(payload) + "\n", encoding="utf-8")


def load_dataset(path: Path) -> Split:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        set(data)
        != {"dataset_version", "label_version", "seed", "boundary", "extracted_at", "rows"}
        or data["dataset_version"] != DATASET_VERSION
        or data["label_version"] != LABEL_VERSION
        or data["seed"] != SEED
    ):
        raise ValueError("Incompatible dataset envelope.")
    rows = []
    for raw in data["rows"]:
        item = dict(raw)
        item["context"] = Context(**item["context"])
        item["cutoff"] = datetime.fromisoformat(item["cutoff"])
        for field in ("history", "outcomes"):
            lines = []
            for raw_line in item[field]:
                line = dict(raw_line)
                line["context"] = Context(**line["context"])
                for time in ("expected_arrival", "completed_at", "available_at"):
                    line[time] = datetime.fromisoformat(line[time])
                lines.append(LineEvidence(**line))
            item[field] = tuple(lines)
        rows.append(Observation(**item))
    return prepare_dataset(
        tuple(rows),
        boundary=datetime.fromisoformat(data["boundary"]),
        extracted_at=datetime.fromisoformat(data["extracted_at"]),
    )


def split_details(split: Split) -> dict:
    return {
        "dataset_version": DATASET_VERSION,
        "dataset_id": split.dataset_id,
        "boundary": split.boundary,
        "extracted_at": split.extracted_at,
        "train_rows": len(split.train),
        "test_rows": len(split.test),
        "train_class_support": dict(Counter(e.label for e in split.train)),
        "test_class_support": dict(Counter(e.label for e in split.test)),
        "supplier_groups_disjoint": True,
        "receipt_ids_unique": True,
    }
