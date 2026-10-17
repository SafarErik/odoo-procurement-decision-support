"""Immutable presentation purpose; never authority for planning or approved content."""

import json
from dataclasses import dataclass

from application.decision_cases import RepositoryError
from application.planning_history import HISTORY_INPUT_KIND
from supplier_evaluation.contracts import ODOO_HISTORY, SYNTHETIC

PRACTICE_EXAMPLES = ("compare-plans", "supplier-outage", "infeasible-demand")


@dataclass(frozen=True, slots=True)
class CatalogContext:
    workspace: str
    example_id: str | None = None

    def validate(self, *, from_odoo: bool):
        if self.workspace != ("controlled" if from_odoo else "practice"):
            raise ValueError("Workspace does not match the server's creation path.")
        if self.example_id is not None and (from_odoo or self.example_id not in PRACTICE_EXAMPLES):
            raise ValueError("Unsupported curated example for this creation path.")


def retrieve_catalog(uow, case):
    """Stored-only metadata with original-base inheritance and no repair/write."""
    with uow:
        base = case if case.parent_id is None else uow.cases.get(case.parent_id)
        if base is None or base.parent_id is not None:
            raise RepositoryError("invalid_catalog", "The catalog original is invalid.")
        context = uow.cases.catalog_for(base.case_id)
        if context is None:
            return {"workspace": "unclassified", "example_id": None}
        try:
            facts = json.loads(base.snapshot)["facts"]
            if (facts["source_type"], facts.get("input_kind", "controlled_synthetic")) not in {
                (SYNTHETIC, "controlled_synthetic"),
                (SYNTHETIC, "odoo_quotations_synthetic_history"),
                (ODOO_HISTORY, HISTORY_INPUT_KIND),
            }:
                raise ValueError("Unsupported stored ML evidence source.")
            context.validate(
                from_odoo=facts.get("input_kind")
                in {"odoo_quotations_synthetic_history", HISTORY_INPUT_KIND}
            )
            return {"workspace": context.workspace, "example_id": context.example_id}
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise RepositoryError(
                "invalid_catalog", "Saved catalog classification is invalid."
            ) from error
