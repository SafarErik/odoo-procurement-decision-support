"""The audit appendix PDF: everything needed to trace how the approved plan was made.

Sections in order: data source, supplier evaluation model, every supplier assessment
with its history metrics and decision path, optimization settings, the decision log,
content identity and the field-level provenance table.
"""

import json
from decimal import Decimal
from fractions import Fraction

from reportlab.platypus import Table, TableStyle

from application.planning_cases import fingerprint
from application.planning_serialization import read_assessments
from application.supplier_overview import (
    class_label,
    feature_label,
    leaf_text,
    metric_display,
    path_steps,
)
from document_adapter.formatting import Formatter
from document_adapter.layout import (
    HEADING,
    LIGHT_BLUE,
    RULE,
    SMALL,
    SUBHEADING,
    TITLE,
    fields,
    paragraph,
)


def audit_story(content: dict, f: Formatter) -> list:
    """All flowables of the audit appendix, in page order."""
    t = f.t
    content_hash = fingerprint(content)
    story = [
        paragraph(t["audit_title"], TITLE),
        fields([(t["case"], content["case_id"]), (t["content_hash"], content_hash)]),
    ]
    story += _data_source_and_model(content, f)
    story += _assessments(content, f)
    story += _optimization(content, f)
    story += _decision_log(content, f)
    story += [
        paragraph(t["identity"], HEADING),
        fields(
            [
                (t["content_version"], content["content_version"]),
                (t["case"], content["case_id"]),
                (t["snapshot_hash"], content["snapshot_hash"]),
                (t["content_hash"], content_hash),
            ]
        ),
    ]
    story += _provenance(content, f)
    return story


def _data_source_and_model(content: dict, f: Formatter) -> list:
    """Which Odoo database and history capture fed the case, and which model scored it."""
    t = f.t
    snapshot = content["planning_snapshot"]
    metadata = snapshot["model_manifest"]["metadata"]
    capture = json.loads(snapshot["facts"]["history"])
    return [
        paragraph(t["data_source"], HEADING),
        fields(
            [
                (t["data_origin"], t["origin_" + metadata["data_origin"]]),
                (t["database"], capture["evidence"]["database"]),
                (t["quotation_group"], snapshot["facts"]["comparison_case_id"]),
                (t["history_cutoff"], f.moment(capture["evidence"]["cutoff"])),
                (t["capture_hash"], capture["capture_hash"]),
            ]
        ),
        paragraph(t["model"], HEADING),
        fields(
            [
                (t["model_id"], metadata["model_id"]),
                (t["training_id"], metadata["training_id"]),
                (t["trained_through"], f.moment(metadata["trained_through"])),
                (t["artifact_hash"], snapshot["model_manifest"]["artifact_sha256"]),
            ]
        ),
    ]


def _assessments(content: dict, f: Formatter) -> list:
    """Per supplier: class, score, history window, metrics and the decision path."""
    t, language = f.t, f.language
    story = [paragraph(t["assessments"], HEADING)]
    for assessment in read_assessments(content["planning_snapshot"]["assessments"]):
        features = assessment.snapshot
        metrics = "\n".join(
            f"{feature_label(name, language)}: {metric_display(name, value, language)}"
            for name, value in zip(features.feature_names, features.values, strict=True)
        )
        path = "\n".join(
            [s["text"] for s in path_steps(assessment, language)]
            + [leaf_text(assessment, language)]
        )
        window = (
            f"{f.moment(features.history_start.isoformat())} – "
            f"{f.moment(features.history_end.isoformat())}"
        )
        story.append(paragraph(f.short(features.context.supplier_id), SUBHEADING))
        story.append(
            fields(
                [
                    (t["class"], class_label(assessment, language)),
                    (t["score"], f.decimal(assessment.score)),
                    (t["window"], window),
                    (t["metrics"], metrics),
                    (t["path"], path),
                ]
            )
        )
    return story


def _optimization(content: dict, f: Formatter) -> list:
    """Solver and version, time limit, outcome, and the buyer's planning policy."""
    t = f.t
    snapshot = content["planning_snapshot"]
    solver, policy = snapshot["solver"], snapshot["request"]["policy"]
    runtime = ", ".join(f"{k} {v}" for k, v in sorted(solver["runtime"].items()))
    limit = policy["concentration_limit"]
    return [
        paragraph(t["optimization"], HEADING),
        fields(
            [
                (t["solver"], f"{solver['adapter']} ({runtime})"),
                (t["time_limit"], f"{f.decimal(solver['time_limit_seconds'])} {t['seconds']}"),
                (t["solver_outcome"], f.outcome(content["human_decision"]["solver_outcome"])),
                (t["max_suppliers"], str(policy["max_suppliers"])),
                (
                    t["concentration"],
                    t["none"] if limit is None else f.percent(Fraction(Decimal(limit))),
                ),
                (
                    t["epsilons"],
                    ", ".join(f.percent(Fraction(Decimal(e))) for e in policy["epsilons"]),
                ),
            ]
        ),
    ]


def _decision_log(content: dict, f: Formatter) -> list:
    """Who approved which plan when, with the recorded attribution and statement."""
    t, audit = f.t, content["human_decision"]
    return [
        paragraph(t["decision_audit"], HEADING),
        fields(
            [
                (t["outcome"], t["approved"]),
                (t["plan_index"], str(content["plan_index"])),
                (t["decided_by"], audit["actor_reference"]),
                (t["attribution"], f.recorded(audit["actor_attribution"])),
                (t["recorded_at"], f.moment(audit["recorded_at"])),
                (t["reference_time"], f.moment(audit["planning_reference_time"])),
                (t["rationale"], audit["rationale"] or t["no_rationale"]),
                (t["demonstration"], f.recorded(audit["demonstration"])),
            ]
        ),
    ]


def _provenance(content: dict, f: Formatter) -> list:
    """One small-print row per stored field: its path, source type, reference and time."""
    t = f.t
    header = (t["field"], t["source"], t["reference"], t["observed_at"])
    data = [[paragraph(v, SMALL) for v in header]]
    data += [
        [
            paragraph(e["canonical_path"], SMALL),
            paragraph(e["source_type"], SMALL),
            paragraph(e["source_reference"], SMALL),
            paragraph(f.moment(e["observed_at"]), SMALL),
        ]
        for e in content["planning_snapshot"]["provenance"]["entries"]
    ]
    table = Table(data, colWidths=[160, 85, 168, 80], repeatRows=1, hAlign="LEFT", splitInRow=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE),
            ]
        )
    )
    return [paragraph(t["provenance"], HEADING), table]
