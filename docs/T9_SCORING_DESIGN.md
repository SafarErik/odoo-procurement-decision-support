# T9 Historical KPI Scoring Design and Evaluation

## Decision

**GO — authorize a bounded PoC scoring implementation increment, not a production
policy claim.** `delivery_schedule_adherence` should become an optional WSM benefit
criterion under the contract in this document. T9 itself changes no runtime score,
weight, contribution, result, API, Odoo integration, persistence, or frontend.

The recommended policy is:

- normalize usable percentages directly as `value / 100`;
- activate the criterion only when every MOQ-eligible offer has usable history;
- otherwise use the existing two-criterion profile and ranking unchanged;
- keep sample size as the accepted availability gate (`n >= 3`) and explanation
  context only, with no confidence multiplier or additional sample bands;
- use the candidate weights below only as transparent PoC policy candidates; and
- include a normal contribution trace when active and an explicit deterministic
  inactive reason when the comparison set is incomplete.

This recommendation is defensible for a controlled thesis PoC because it rewards
observed operational schedule adherence without converting missing evidence into bad
performance or making offer scores incomparable. It is not empirically calibrated,
statistically reliable at `n = 3`, or suitable for autonomous purchasing.

## Fixed baseline and scope

T9 starts from merged T8 commit `948c092`. The accepted metric remains the
line-count-weighted `delivery_schedule_adherence` percentage in `[0, 100]` based on
operational Expected Arrival. Returns follow the accepted warning/exclusion policy,
sample size remains separate, values below three remain withheld, and `None` never
means zero. Historical provenance remains in the application layer.

The evaluator is `tools/t9_scoring_evaluation.py`. It imports the current Decision
Core to obtain the unchanged baseline and MOQ partition, but no production package
imports `tools`. Run it from the repository root:

```powershell
.\.venv\Scripts\python.exe -m tools.t9_scoring_evaluation
```

The JSON output contains profile candidates, all 15 scenarios, contribution traces,
normalization and missing-policy comparisons, a weight sweep, exact pairwise flip
thresholds, and the add/remove-alternative experiment. All arithmetic is `Decimal`.

## Normalization alternatives

| Alternative | Interpretation | Equal values | Small differences | Add/remove stability | Decision |
| --- | --- | --- | --- | --- | --- |
| Direct absolute benefit: `value / 100` | `80%` always contributes `0.80 * weight` | Equal raw values keep their absolute level | Differences remain proportional; `79.99` vs `80.01` differs by `0.0002` before weighting | Stable because no history bound depends on other offers | **Recommend** |
| Comparison-set min–max | Best observed offer receives 1 and worst receives 0 | Existing convention assigns all equal values 1 | Can turn `79.99`, `80.00`, `80.01` into `0`, `0.5`, `1` | Unstable; an added alternative can reverse the order of existing offers | Reject for history |
| Illustrative bands: `<50 -> 0`, `<75 -> 0.5`, `<90 -> 0.75`, otherwise `1` | Easy verbal categories | Same band is equal | Discontinuous at thresholds and discards within-band evidence | Stable to alternative-set changes | Reject without an evidence-based threshold policy |

Direct normalization has meaningful endpoints (`0 -> 0`, `100 -> 1`), does not
manufacture relative extremes, and permits a deterministic contribution statement.
Min–max is not selected merely because unit price and lead time already use it.

The S09 close-value case produces candidate scores `A=0.719985`, `B=0.545015`, and
`C=0.3700` under direct normalization. With min–max history they become `A=0.60`,
`B=0.575`, and `C=0.325`; a two-hundredths percentage-point historical spread is
artificially expanded across the full history weight.

The S12 add/remove experiment holds A and B's price and lead-time bounds fixed and
uses sensitivity weights `0.45/0.20/0.35`. Direct history keeps A ahead of B both
with and without C (`A=0.695`, `B=0.480`). Min–max ranks `B > A` without C but
`A > B` after adding C, because C changes only the historical lower bound. This is
an avoidable violation of independence from irrelevant alternatives.

## Missing and insufficient history

The activation set is the set remaining **after** the existing MOQ hard constraint.
An MOQ-ineligible offer cannot be scored and cannot deactivate the history criterion.

| Policy | Comparability and fairness | Distortion and explanation | Decision |
| --- | --- | --- | --- |
| Activate only when every eligible offer is usable | Every scored offer has the same criteria and weights | Discards available history for that comparison but exactly preserves the understood baseline | **Recommend** |
| Renormalize each incomplete offer's available weights | Different offers are scored under different utility functions | Can reward missingness and makes equal total scores semantically unequal | Reject |
| Impute neutral `0.5` | Same weights, but invents evidence and treats unknown as average | Rank depends on an unsupported value; `None` is no longer visibly unknown | Reject |
| Impute conservative `0` | Same weights, but turns absence into worst performance | Penalizes new or low-volume suppliers and contradicts T8's withheld-not-zero rule | Reject |
| Exclude missing offers | Superficially comparable remaining set | Violates the accepted rule that insufficient history must not exclude an offer | Reject |

S07 demonstrates material policy sensitivity for one supplier with `n = 2`:

| Policy | Ranking | Relevant scores/impact |
| --- | --- | --- |
| Complete-case activation | `A > B > C` | History inactive; exact baseline `0.70 / 0.3740 / 0.30` |
| Per-offer renormalization | `A > C > B` | B falls to `0.372941...` under a different weight basis |
| Neutral imputation | `A > B > C` | B becomes `0.3920` from invented neutral evidence |
| Conservative imputation | `A > C > B` | B becomes `0.3170` because unknown is treated as zero |
| Exclusion | `A > C`; B removed | Directly violates the accepted non-exclusion rule |

All-withheld history (S08) therefore produces the exact current baseline, not three
zero-performance suppliers. Only-one-usable history (S06) behaves the same way.

## Sample-size treatment

Sample size remains an availability threshold and explanation/warning field. T9 does
not recommend confidence weighting or bands above three because there is no validated
mapping from line count to confidence, no treatment of supplier/product heterogeneity,
and no empirical calibration set. A minimum sample size of three is an accepted PoC
policy, **not proof of statistical reliability**. Applying a weight multiplier would
create false precision and could make otherwise identical percentages incomparable.

Production-level work would require a materially larger representative dataset,
time-decay and segmentation decisions, uncertainty estimation, and outcome review.

## PoC strategic-profile candidates

The weights are policy candidates, not empirically optimal estimates.

| Profile | Current comparator (price/lead) | Candidate price | Candidate lead | Candidate history | Reduction rationale |
| --- | ---: | ---: | ---: | ---: | --- |
| Cost-focused | `0.70 / 0.30` | `0.60` | `0.25` | `0.15` | Price remains dominant; price gives up `0.10` and lead time `0.05` for a bounded reliability signal |
| Urgent | `0.30 / 0.70` | `0.25` | `0.60` | `0.15` | Lead time remains dominant; lead gives up `0.10` and price `0.05` |
| Risk-averse | balanced comparator `0.50 / 0.50` | `0.30` | `0.30` | `0.40` | New PoC candidate; both existing criteria give up `0.20`, making observed reliability the largest single criterion |

Each row sums exactly to `1`. The existing runtime constructors remain unchanged in
T9. The risk-averse row is a proposed new profile; it is not a silent rename of the
current `balanced` constructor.

## Required scenario matrix

The table uses direct normalization and complete-case activation. Scores are shown
in descending candidate order; baseline comparisons use the current two-criterion
weights. Offer-ID ascending remains the deterministic tie-break.

| ID | Scenario | Profile | Baseline | Candidate | Active | Candidate scores | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | Cheapest also best history | Cost | `A > B > C` | `A > B > C` | Yes | `A=.9925, B=.530, C=.075` | Signals reinforce |
| S02 | Cheapest has worst history | Cost | `A > B > C` | `A > B > C` | Yes | `A=.910, B=.545, C=.1425` | Candidate `0.15` history does not overwhelm cost |
| S03 | Fastest has weak history | Urgent | `A > B > C` | `A > B > C` | Yes | `A=.660, B=.560, C=.370` | Urgency remains dominant |
| S04 | Reliable supplier is more expensive | Risk | `A > B > C` | `B > A > C` | Yes | `B=.800, A=.660, C=.300` | Intended, defensible risk-profile flip |
| S05 | Equal history | Cost | `A > B > C` | `A > B > C` | Yes | `A=.7125, B=.5375, C=.3625` | Absolute level contributes equally |
| S06 | Only one usable | Cost | `A > B > C` | `A > B > C` | No | `A=.70, B=.500, C=.30` | Exact baseline fallback |
| S07 | One sample below three | Urgent | `A > B > C` | `A > B > C` | No | `A=.70, B=.3740, C=.30` | Withheld, not zero |
| S08 | All withheld | Risk comparator | `A > B > C` | `A > B > C` | No | all `.50`, tie by ID | Exact baseline fallback |
| S09 | Tiny differences near boundary | Cost | `A > B > C` | `A > B > C` | Yes | `A=.719985, B=.545015, C=.3700` | Direct method avoids amplification |
| S10 | Historical `0` and `100` | Risk | `A > B > C` | `C > B > A` | Yes | `C=.70, B=.50, A=.30` | Endpoints behave monotonically |
| S11 | MOQ-ineligible offer has `100` | Risk | `A > B` | `B > A` | Yes | `B=.580, A=.500`; C excluded | C never enters normalization/scoring |
| S12 | Add/remove third offer | Cost | `A > C > B` | `A > C > B` | Yes | `A=.705, C=.425, B=.370` | Separate sensitivity experiment exposes min–max reversal |
| S13 | Controlled T8 `33.33`, `n=3` | Cost | `A > B > C` | `A > B > C` | Yes | `A=.649995, B=.525005, C=.40` | `33.33 -> .3333` exactly |
| S14 | Complete tie | Cost | `A > B > C` | `A > B > C` | Yes | all `.970` | Offer-ID tie-break preserved |
| S15 | All signals conflict | Risk | `B > A > C` | `B > C > A` | Yes | `B=.730, C=.512, A=.460` | History changes lower ordering, not winner |

Ranking changes under the recommended candidates occur in S04, S10, S11, and S15.
S04 is the central intended change: the explicit risk-averse profile selects a more
reliable but more expensive supplier. S10 validates endpoint monotonicity. S11 also
proves that the excellent but MOQ-ineligible offer stays excluded before scoring.

## Weight and value sensitivity

S02 sweeps history weight from `0` while allocating the remainder in the original
cost profile's `70:30` ratio. Exact direct-normalization tie thresholds are:

- A/B: `0.555555...`; B outranks A only above this value (the ID tie-break keeps A
  first at exact equality);
- A/C: `0.645161...`; and
- B/C: `0.769230...`; C becomes first only above this value.

The sweep confirms A remains first through `0.55`, B is first from `0.60` through
`0.75`, and C is first at `0.80`. The proposed cost history weight `0.15` is far
below the first top-rank threshold in this deliberately conflicting case.

Across the fixed matrix, input history spans missing, withheld `n=0/1/2`, the
controlled `33.33` at `n=3`, close `79.99/80.00/80.01`, and endpoints `0/100`.
Price and lead weights vary both across profiles and in the ratio-preserving sweep.
Availability changes are covered by S06-S08 and the five-policy S07 comparison.

## Deterministic explanation contract

When active, each ranked offer should add a contribution with:

- `criterion = delivery_schedule_adherence`;
- `direction = benefit`;
- the raw percentage and separate sample size;
- `normalized_value = raw_value / 100`;
- the selected profile's history weight; and
- `weighted_contribution = normalized_value * weight`.

The total score remains the exact sum of all contributions. When inactive, the
result must say `historical criterion inactive: at least one MOQ-eligible offer has
missing or withheld history`, list the affected stable offer IDs, omit the history
contribution for every offer, and reproduce the existing two-criterion result
exactly. Provenance must remain outside Decision Core explanations.

## Authorized next-increment implementation contract

The GO authorizes one bounded follow-up scoring increment with these exact rules:

1. Keep MOQ filtering first and use only eligible offers for the activation check
   and all normalization.
2. Accept ERP-neutral, supplier-linked history values plus sample sizes; reject
   duplicate, unknown, or ambiguous joins. Do not accept provenance in Decision Core.
3. Treat a value as usable only when it is present, finite, within `[0, 100]`, and
   `sample_size >= 3`. Never convert `None` to zero.
4. Activate history only when every eligible offer has usable history. Otherwise
   reproduce the existing two-criterion `DecisionResult` values and ordering while
   returning an explicit inactive reason.
5. Normalize history only as `value / 100`; do not use comparison-set min–max,
   imputation, per-offer renormalization, penalties, confidence multipliers, or
   history-based exclusion.
6. Add the three candidate profile policies exactly as documented above under
   explicit versioned/opt-in names. Do not silently mutate the existing constructors.
7. When active, emit the complete history contribution described above and retain
   score-descending, offer-ID-ascending ranking.
8. Add regressions for all T9 scenarios, exact thresholds, full baseline fallback,
   all-excluded behaviour, input-order independence, and score reconstruction.
9. Keep Odoo reads, T8 calculation semantics, provenance, persistence, frontend,
   and existing public HTTP behaviour out of that increment. API exposure requires
   a separately reviewed contract after the internal scoring path is accepted.
10. Continue to describe the weights and `n >= 3` threshold as PoC policy choices,
    not statistically learned or production-validated values.

## Decision questions answered

1. **Should history become a criterion?** Yes, in a bounded opt-in PoC increment.
2. **Normalization?** Direct absolute percentage divided by 100.
3. **Missing history?** Deactivate history for the whole eligible comparison set and
   use the exact two-criterion baseline.
4. **Sample size?** Availability and explanation only; no confidence weighting.
5. **Weights?** Cost `.60/.25/.15`, urgent `.25/.60/.15`, risk `.30/.30/.40`.
6. **Explanation?** A normal benefit contribution when active; explicit set-level
   inactive reason and no history contributions on fallback.
7. **Which scenarios change rank?** S04, S10, S11, and S15 under candidates; policy
   and min–max alternatives create additional changes documented above.
8. **Are changes defensible?** Yes for controlled, human-reviewed PoC decisions,
   especially the explicit risk profile; not for autonomous or production use.
9. **Limitations?** Small samples, one bounded metric, operational rather than
   promised schedule, no statistical calibration, segmentation, decay, or field data.
10. **Is implementation authorized?** Yes, only under the bounded contract above.
