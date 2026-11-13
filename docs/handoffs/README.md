# Handoffs

One record per increment: problem → decision → implemented behaviour → evidence →
limitation → thesis chapter. Each file states its branch and the PR that merged it.
Earlier increments (T0–T18, UX32–UX41) are in [../history/](../history/).

## Revamp delivery (P0–P4, plan: [REVAMP_PLAN](../history/REVAMP_PLAN.md))

| Handoff | Content |
| --- | --- |
| [P0_REPO_CLEANUP](P0_REPO_CLEANUP.md) | V1/WSM and Practice workspace removed, one baseline migration, current-state docs |
| [P1_ODOO_HISTORY_ML](P1_ODOO_HISTORY_ML.md) | Guarded Odoo history seeder; Decision Tree retrained on Odoo-read history |
| [P2_BACKEND_CAPABILITIES](P2_BACKEND_CAPABILITIES.md) | Quotation-group selection, two-way scenarios, supplier overview, HU/EN PDF |
| [P3_FRONTEND_REVAMP](P3_FRONTEND_REVAMP.md) | Hungarian-default Reflex UI with case tabs and charts |
| [P3_LIBRARY_SEARCH_RELOAD_FIX](P3_LIBRARY_SEARCH_RELOAD_FIX.md) | Case search submitted during a reload is kept |
| [P4_VALIDATION](P4_VALIDATION.md) | One-command demo, MILP/API evaluation, ML report check, limitations |
| [P4_RERUN_AND_PDF_FIXES](P4_RERUN_AND_PDF_FIXES.md) | P4 evidence rerun with the balanced plan; Hungarian PDF fixes |

## Follow-ups and fixes

| Handoff | Content |
| --- | --- |
| [P4_MEASUREMENT_REFRESH_20261113](P4_MEASUREMENT_REFRESH_20261113.md) | Clean thesis-tag demo/MILP rerun, rebuilt local environment, new model/data and timing context |
| [PROJECT_BASELINE_REFRESH](PROJECT_BASELINE_REFRESH.md) | Agent baseline aligned with the post-revamp state |
| [L6_TERMS_PROVENANCE](L6_TERMS_PROVENANCE.md) | Suggested buyer terms carry their source; P4 evidence rerun |
| [REVIEW_FIXES](REVIEW_FIXES.md) | External-review fixes: L6 visibility, data origin, wording |
| [GUIDED_WORKSPACE](GUIDED_WORKSPACE.md) | Guided preparation, suggested-input explanations, plan comparison, confirmed decision |
| [UI_COPY_AND_ALTERNATIVES](UI_COPY_AND_ALTERNATIVES.md) | Natural Hungarian copy, more cost–risk alternatives |
| [BALANCED_ALTERNATIVE_AND_PDF_TITLE](BALANCED_ALTERNATIVE_AND_PDF_TITLE.md) | Balanced (min–max share) alternative, ADR-035 |
| [PDF_PLAN_AND_AUDIT_SPLIT](PDF_PLAN_AND_AUDIT_SPLIT.md) | Approved plan and audit appendix as two PDFs, ADR-036 |
| [FINAL_REVIEW](FINAL_REVIEW.md) | Defects found by the final whole-repository review |

## Technical-debt refactor (R1–R9; R1 removes legacy paths, the rest preserve behaviour)

| Handoff | Content |
| --- | --- |
| [R1_LEGACY_REMOVAL](R1_LEGACY_REMOVAL.md) | Pre-P2 code paths removed; old stored records no longer readable |
| [R2_TEST_STRUCTURE](R2_TEST_STRUCTURE.md) | Tests named by capability, shared code in `tests/helpers/` |
| [R3_FRONTEND_TEXTS](R3_FRONTEND_TEXTS.md) | Every UI text in `frontend/i18n/` |
| [R4_FRONTEND_API_CLIENT](R4_FRONTEND_API_CLIENT.md) | One HTTP-client layer, `frontend/api/` |
| [R5_FRONTEND_VIEWS](R5_FRONTEND_VIEWS.md) | Readable views and state; one theme token file |
| [R6_BACKEND_KERNEL](R6_BACKEND_KERNEL.md) | Shared errors, stored contract ids, Odoo JSON-2 client |
| [R7_BACKEND_SPLITS](R7_BACKEND_SPLITS.md) | PDF renderer split; MILP and ML models explained in docstrings |
| [R8_TOOLS_CI](R8_TOOLS_CI.md) | Self-documenting tools; CI runs `tools.dev check` |
| [R9_DOCS_CONSOLIDATION](R9_DOCS_CONSOLIDATION.md) | One entry README, docs index, package READMEs |
