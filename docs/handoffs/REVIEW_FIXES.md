# External-review fixes — L6 visibility, data origin, wording

Date: 2026-10-19/20. Branch: `feature/cleanup` (on top of `cbc00d1`, i.e. `main` `e3cbf84`
plus the project-baseline refresh and the [L6 provenance](L6_TERMS_PROVENANCE.md) commit).
Not committed; the owner commits. Drive was not changed; a separate session updates it after
merge (Hungarian list at the end). Requirements touched: FR-V2-01/04 and the 06 hybrid-input
rule (L6), NFR-V2-03 (generated vs. observed distinguishable), FR-V2-10, NFR-V2-06; official
task sentences 7, 9, 11, 12. Limitations: L1, L2, L5, L6.

## Problem

An external review of the Drive documents and the code raised findings. The ones verified
against `feature/cleanup` were:

1. **L6 visibility.** The preview fills price and delivery quantity validity ranges (1–1000)
   per supplier, and saving records them as `buyer_reviewed_terms` with
   `kept-suggested=…`. The form had no field for them, and the pre-save review showed only
   price, capacity, MOQ, promised date and availability. So the buyer "reviewed" values they
   never saw.
2. **Hard-coded data origin.** `"data_origin": "generated"` was fixed in
   `supplier_evaluation/history_model.py` (training and metadata validation) and
   `tools/train_history_model.py`. A model trained on observed history could not exist, and
   nothing tied a model's origin to the origin of the history a case was scored on.
3. **Repository wording.** MODEL_MILP §7 described K as enforcing diversification.
   LIMITATIONS L5 proposed a "concave" risk term, and L6 proposed `product.supplierinfo` minimum
   quantity as an MOQ source (ADR-017: it is a price threshold). L1 claimed the pipeline runs
   "unchanged" on real data. MODEL_ML said the 14-day gap "is not used at all", mixed measured
   results with explanations, and used "better" without naming a metric. The project
   baseline still said the P4 demo had not been re-run. The CI scope was described only
   loosely, and the decision-reason and No-award PDF rules were not stated where the
   evidence is listed.

## Decision

Owner (2026-10-19): continue on `feature/cleanup`. Make the ranges **editable** form fields
rather than display-only.

Own decisions:

- The data origin is **declared**, never inferred from the data: `--data-origin` on
  extraction (default `generated`) for the training pipeline, and `ODOO_HISTORY_DATA_ORIGIN`
  (default `generated`) for the runtime database. It is frozen in each new history capture.
- Consistency is checked against the case, not against a constant. The model's `data_origin`
  must equal the capture's origin at load, at preview readiness, at creation and in
  stored-snapshot validation.
- Backwards compatibility: captures stored before this change have no origin field and read
  as `generated`. Existing model metadata already holds `"generated"`, so the model id and
  artifact hash are unchanged. The capture version stays `v2`, because the field is
  additive and validated.
- On narrow screens the review shows one card per supplier instead of a table that scrolls
  sideways, so no term hides off-screen (found during the 375 px check).

## Implemented behavior

- **Form** (`frontend/planning/rfqs.py`): each supplier card has two fieldsets, "Ár érvényes
  mennyiségre" and "Szállítás érvényes mennyiségre" (EN: "Price valid for qty" /
  "Delivery valid for qty"). Each fieldset has a "Legkisebb"/"Legnagyobb" pair, pre-filled
  with the suggestion. `state_creation._odoo_request` accepts whole numbers 1–1000 with
  minimum ≤ maximum. An error (`err_range`) is shown under the field and focus moves to it.
- **Review** (`_set_review`): two new columns, or rows on the narrow-screen cards, `price_range`
  and `delivery_range`, e.g. `1–500` or `1–1 000 (javasolt, nem módosította)` /
  `1–1,000 (suggested, not changed)`. The marker is read from the saved source's
  `kept-suggested` list, i.e. from exactly what is stored. "Feltételek módosítása" returns
  to the form, and not saving aborts. A language switch relabels the open review.
- **Origin** (`supplier_evaluation/contracts.py` `HISTORY_DATA_ORIGINS`,
  `LEGACY_HISTORY_DATA_ORIGIN`):
  - `train(..., data_origin=)` is required.
  - `check_manifest_metadata` accepts `generated` or `observed`.
  - `build_capture(..., data_origin)` freezes the origin, and `capture_origin()` reads it
    (legacy → `generated`).
  - `validate_snapshot` rejects a case whose model origin differs from its capture's origin.
  - `load_history_model` rejects a model whose origin differs from `ODOO_HISTORY_DATA_ORIGIN`
    (`odoo_history_model_incompatible`, nothing saved).
  - The preview reports the capture's origin.
  - The training tool writes the origin to the export, to the dataset card
    (`data_origin` + `data_origin_note`) and to the model. It lists the generated-data
    limitations only for generated exports.
- **Docs**: MODEL_MILP §7, LIMITATIONS (status line, L1, L2, L5, L6), MODEL_ML (status, §2
  origin and unit of observation, §3 recency window, §6 measured vs. hypotheses with named
  metrics, §8 origin check), RUNBOOK §5.1/5.3, `.env.example`, TRACEABILITY rows 9 and 11,
  P4 handoff (decision reasons, CI scope), project baseline (CI scope, status as
  branch + commit + run, L6/origin bullet).
  Code facts checked for the wording:
  - `FinalizePlanningCommand.normalized` requires a reason for No-award and for any plan
    other than index 0.
  - `planning_documents` answers `approved_pdf_ineligible` for No-award.
  - `RECENCY_WINDOW = 180 d` covers `[c−180d, c)`, so it includes the settlement gap; only
    receipts before `c` are used.
- **Tests**:
  - `test_creation_review.py`: ranges shown, kept-suggested marker in EN and HU, edited
    range saved without the marker, out-of-range and inverted-range errors create no intent.
  - `test_odoo_purchase_history.py`: observed model trains and validates, unknown origin
    rejected, model/database origin mismatch blocks preview readiness and creation, stored
    model/capture mismatch rejected, legacy capture without origin reads as `generated`.

## Evidence (commands actually run, Windows 11, Python 3.11.15 uv venv)

| Check | Result |
| --- | --- |
| `pytest tests/test_creation_review.py tests/test_odoo_purchase_history.py` | 18 + 37 passed |
| `python -m tools.dev check` (final, after the last UI change) | PASS — format, lint, compile, **504 passed**, 51 deselected, `uv pip check` compatible |
| `pytest -m "integration and not e2e"` (disposable PostgreSQL 16, live Odoo, API :8000, `RUN_ODOO_HISTORY_LIVE=true`), first run 2026-10-19 | 44 passed, 3 skipped, 2 failed: both `test_live_purchase_history.py`, HTTP 401 for the restricted history user's expired API key (environment, not code) |
| same, 2026-10-20 after the owner renewed `ODOO_T7S_API_KEY` | **46 passed**, 3 skipped (T6 and 2× T7S fixture contracts, as in P1–P4) |
| `python -m tools.dev demo` (2026-10-20 07:30 UTC, commit `cbc00d1`, **dirty: true** — these fixes are uncommitted) | complete in 15.3 s (HTTP flow 3.2 s); model `9b45987c…`, `data_origin: generated`; base case unchanged from P4: minimum cost 288,608 HUF, exposure 0.60; alternative 293,132 HUF, exposure 0.3333; nine scenarios, two infeasible (demand 250 and 1000); approval + separate No-award; HU PDF 41,209 B and EN PDF 39,467 B; replay without Odoo and model: preview 503, 13 operations replayed, PDFs byte-identical, No-award PDF 422, `passed: true` → [P4_DEMO_REPORT.json](../evidence/P4_DEMO_REPORT.json). Only ids, hashes, timestamps and PDF bytes differ from the `bb9badf` run |
| `python -m tools.milp_evaluation` (2026-10-20 07:36 UTC, commit `cbc00d1`, **dirty: true**) | **PASSED**; 21/21 correctness checks without failure (every stored request and variant equals the exhaustive reference optimum) → [P4_MILP_EVALUATION.json](../evidence/P4_MILP_EVALUATION.json). Latency ms, median / p95 / max of 30 runs (create · scenario · exact retry · GET): 4 sup/1 ε 378/437/437 · 185/226/236 · 44/50/58 · 24/43/72; 4/3 518/557/558 · 328/363/363 · 44/49/84 · 24/26/27; 5/1 414/470/483 · 225/269/275 · 46/56/92 · 24/27/28; 5/3 622/661/680 · 427/482/483 · 46/50/52 · 25/27/28; 10/1 599/640/668 · 408/453/464 · 58/102/113 · 30/33/33; 10/3 949/1015/1018 · 749/853/869 · 60/67/69 · 32/37/38. Local, single machine, not an SLA |
| `pytest -m e2e tests/e2e --browser chromium` (after the last UI change) | **2 passed** |
| `python -m tools.train_history_model report` (dirty tree, offline) | `unchanged: true`. Artifact hash, export hash, train id and evaluation are equal to P1; `P4_ML_REPORT_CHECK.json` regenerated (only `generated_at` changed; this report has no commit field) |
| Built-in browser, fixture-Odoo API (`tests.e2e.odoo_fixture_api`) + `tools.dev ui` | 1440 px: form fieldsets, review table with both range columns, edited `1–500` without marker, others marked. 375 px: per-supplier review cards show all terms, "Feltételek módosítása" unlocks the form, an out-of-range minimum shows the inline HU error, the EN review shows "(suggested, not changed)" |

**Evidence state.** The demo, MILP and ML evidence JSON were produced by this code, but on an
uncommitted tree (`cbc00d1` + these changes, `dirty: true`). For a commit-exact record,
rerun the three tools after the owner commits. A dirty-tree run is recorded honestly rather
than relabelled.

**Not run:** hosted CI (nothing pushed). Its scope is described in TRACEABILITY row 11: it
runs no live history path, browser flow or P4 tool.

## Limitation

- The ranges and other buyer terms are still suggestions, not supplier-confirmed (L6). The
  review marks only the two ranges as "suggested". Capacity, MOQ and promised date are
  recorded as kept in `kept-suggested` but are not marked in the review, because they were
  already visible, editable form fields.
- The origin is an operator declaration. Nothing verifies that a database declared
  `observed` really holds business data. An observed-history model is technically
  accepted but has not been validated (L1).
- The fixture-Odoo browser check uses the P1 test fixture group, not the seeded
  `pdss_history_gen` group.

## Thesis chapter

Chapter 3 (data origin, generated vs. observed), chapter 5 (MILP: K as upper bound, L5
proposal), chapter 6 (implementation: editable ranges, origin consistency), chapter 7
(evaluation wording: metric-tied comparison, unit of observation, gate results), and
chapter 9 (L1, L5, L6 proposals).

## Drive teendők (magyarul, a Drive-session számára, merge után)

- **06 Requirements baseline:**
  - FR-V2-10, NFR-V2-06 és FR-V2-08 normatív szövegének pontosítása, dátummal
    (2026-10-19) és ADR-028 hivatkozással.
  - A hibrid bemeneti szabály: a javasolt ár/szállítás tartomány is látható, szerkeszthető,
    és a review „javasolt” jelöléssel mutatja.
  - A `data_origin` deklarált (`generated` | `observed`), és a modellnek egyeznie kell az
    eset history-eredetével.
- **Állapotfejlécek (00, 06, 07):**
  - A státusz formája: ág + commit + bizonyító futás (melyik JSON, melyik commit, dirty
    flag).
  - Nem szabad „a demó nem futott újra” állítás, ha a riport újrafutást mutat.
  - A demó, a `milp_evaluation` és az ML-report a jelen kódon lefutott (2026-10-20,
    `cbc00d1` + nem commitolt javítások, `dirty: true`); commit után érdemes újrafuttatni.
- **03 ADR-register:**
  - ADR-024, 027, 028 és 030 pontosítása: az adat-eredet paraméter, a konzisztencia-ellenőrzés
    és a régi capture-ök `generated`-ként olvasása.
  - ADR-030: generált történet, de a pipeline megfigyelt adatra **adaptálható**, nem
    „változatlanul futtatható”.
- **04/05/07/08 szövegezés:**
  - K felső korlát, nem kényszerít diverzifikációt. A kapacitás és a koncentrációs korlát
    tehet szükségessé több szállítót.
  - L5 javaslat: darabonként lineáris koncentrációs büntetés vagy explicit kiesési
    forgatókönyvek; konkáv büntetés nem.
  - L6: a `product.supplierinfo.min_qty` nem MOQ-forrás (ADR-017).
  - A 180 napos recency ablak tartalmazza a 14 napos rést (nincs szivárgás).
  - Az eredmények metrikához kötve: macro-F1 / pontosság / problémás recall.
  - Mért eredmény és hipotézis külön.
  - Megfigyelési egység: 2 546 sor → 1 804 sor, 682 tanító, 140 elsődleges teszt sor
    10 szállítótól.
  - No-award esetén nincs jóváhagyott PDF. Indoklás kötelező az alternatíva választásánál és
    No-awardnál.
  - A CI pontos hatóköre.
