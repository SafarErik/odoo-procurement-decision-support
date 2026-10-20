# Natural Hungarian copy, quieter workspace and more cost–risk alternatives

Date: 2026-10-20. Working-tree increment on `feature/frontend-revamp`.
The owner commits and pushes; this work performs neither.

## Problem

The owner's walkthrough found three issues. Hungarian texts read like literal translations
(e.g. "Nincs odaítélés" for No-award). Several screens repeated the same reassurance
("nothing is recalculated", "the base case stays unchanged") or explained the data source
in a box nobody needs ("Honnan jönnek az ajánlatok?", "Odoo mellett, csak olvasás").
Most cases also showed only one alternative plan.

## Diagnosis of "only one alternative"

Saved requests were replanned in memory (no write) using the stored request and
the real planner/CBC:

| Case (suppliers) | ε = {0.2} | ε = {0.05, 0.1, 0.2} |
| --- | --- | --- |
| 5f9b7b21 (5) | 1 alternative | 2 alternatives (+1.0 %, +6.9 %) |
| 52170388, 26c06a3f, 18d1eef1, 964d36e6 (4) | 1 | 1 |

Cause 1: the preview policy requested a single allowance (ε = 0.2), so at most one
alternative could exist. Cause 2 (model, unchanged): exposure Σrᵢxᵢ/Q is linear and the
tree yields few distinct scores, so the cost–exposure frontier has few breakpoints. In the
4-supplier cases a +1.6 % plan already reaches the minimum exposure, so every larger
allowance returns the same allocation (deduplicated). See L5 in
[LIMITATIONS_AND_FUTURE_WORK.md](../LIMITATIONS_AND_FUTURE_WORK.md).

## Decision and implemented behavior

- The Odoo preview policy now requests ε ∈ {0.05, 0.1, 0.2} (the API already accepted
  1–3 values; P4 evaluation used the same set). Existing saved cases are immutable and keep
  their recorded policy. No solver, model or schema change.
- Each alternative shows the tightest allowance that produced it
  ("legfeljebb +5 % többletköltséggel"), derived from the saved `runs`; the lowest-exposure
  plan carries a "legkisebb kockázat" badge in Overview and Plans.
- Copy: No-award is "Nem rendelünk" in Hungarian (English stays "No-award"); "Legolcsóbb
  terv" / "Cheapest plan" replaces "Legkisebb költség" as the plan name; "Mi lenne, ha…?";
  one name ("Új beszerzés") for the new-procurement action; redundant reassurances removed
  or shortened. The honest caveats stay: failed alternative search does not prove absence,
  exposure is not a failure probability, scenarios cannot be approved, no Odoo order.
- Layout: sidebar footer note, RFQ source explainer and company-scope identifier, the
  home "1-2-3" strip, the case-header next-action banner (duplicate of the badge and the
  Overview "Next step" card) and repeated callouts removed. The Overview decision tile
  (duplicate of the badge) became an "Értékelt szállítók" tile with the link to suppliers.
- Cost–exposure chart: the exposure axis spans the saved plans with whole-point padding
  instead of a fixed 0–100 band, and the cost axis is padded so labels do not clip.

Maps to FR-V2-07/09 and AC-V2-09 (explanations and buyer UI) and FR-V2-05/06 (cost/risk
alternatives); no requirement is redefined.

## Evidence (commands actually run)

| Check | Result |
| --- | --- |
| In-memory replanning script over five saved cases | table above |
| `python -m tools.dev check` | 516 passed; format, lint, compileall, dependency check passed |
| `reflex compile --dry` | passed |
| Built-in browser, dev server on spare ports | Home, Overview, Plans (chart), Decision at 1440 px; Overview at 390 px without horizontal overflow |
| `impeccable detect --json frontend` | `[]` (limited coverage of Python wrappers) |
| `pytest tests/e2e -m e2e --browser chromium` | 3 passed (disposable PostgreSQL, FastAPI, Reflex; fixture Odoo) |

## Limitations

- Old cases still show one alternative; only newly created cases use three allowances.
- Four-supplier demonstration groups still yield one alternative; more alternatives there
  need a model change (diversification-aware exposure, L5), which is an owner/thesis decision.
- Integration tests were not run (no persistence or Odoo-access change).
- English copy was adjusted only where the Hungarian sentence changed meaning.

## Thesis chapter

Chapter 5: why the number of alternatives is small (linear exposure, discrete tree scores,
ε grid). Chapter 6: buyer-language copy and progressive disclosure. Chapter 7: in-memory
replanning as evidence; old cases are immutable.
