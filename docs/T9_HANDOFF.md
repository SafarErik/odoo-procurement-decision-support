# T9 Handoff — Historical KPI Scoring Design and Evaluation

## Outcome

T9 is **GO — BOUNDED POC SCORING IMPLEMENTATION AUTHORIZED**. The recommendation is
direct absolute normalization, complete-case activation after MOQ filtering, sample
size as an availability/explanation field only, and explicit opt-in PoC weights.
No recommendation is implemented in runtime by T9.

Branch: `codex/t9-historical-scoring-design-evaluation`

Starting point: merged T8 `main` at `948c0928f74f6ec824a2185094164c1e59caf2eb`

## Preconditions

- fetched `origin` before branching;
- confirmed local `main` and `origin/main` both pointed to T8 merge commit `948c092`;
- confirmed `CanonicalDecisionInput.historical_performance` is contextual;
- confirmed README and `docs/T8_HANDOFF.md` record AC-07 as satisfied; and
- ran the pre-change fast baseline: **180 passed, 23 deselected**.

## Artifacts

- `tools/t9_scoring_evaluation.py`: isolated Decimal-based evaluator and JSON report;
- `tests/test_t9_scoring_evaluation.py`: policy, scenario, sensitivity, contract, and
  architecture regressions;
- `docs/T9_SCORING_DESIGN.md`: decision record and exact next-increment contract;
- `docs/T9_HANDOFF.md`: implementation and acceptance evidence;
- `README.md`: current T9 status and artifact links; and
- `docs/IMPLEMENTATION_LOG.md`: append-only T9 record.

No file under `decision_core/`, `application/`, `backend/`, `odoo_adapter/`,
`frontend/`, or `infra/` changed.

## Evaluated alternatives

Normalization:

1. direct absolute percentage divided by 100 — recommended;
2. comparison-set min–max — rejected due amplification and set dependence; and
3. illustrative policy bands — rejected without calibrated thresholds.

Missing history:

1. all-eligible complete-case activation — recommended;
2. per-offer weight renormalization — rejected as non-comparable;
3. neutral imputation — rejected as invented evidence;
4. conservative imputation — rejected as a missingness penalty; and
5. exclusion — rejected because T8 explicitly forbids automatic exclusion.

Sample-size treatment:

- retain the `n >= 3` availability threshold and warning/explanation;
- do not add confidence weighting; and
- do not add further bands without evidence.

The profile candidates are price/lead/history: cost-focused `.60/.25/.15`, urgent
`.25/.60/.15`, and risk-averse `.30/.30/.40`. They sum exactly to one and are
explicitly non-empirical PoC policy candidates.

## Evidence summary

The fixed matrix contains all 15 requested scenarios. Recommended-policy ranking
flips occur in S04 (risk profile chooses reliable/more expensive B), S10 (0/100
endpoints), S11 (B overtakes A while excellent MOQ-ineligible C remains excluded),
and S15 (lower-order conflict). S06-S08 exactly retain the baseline because eligible
history is incomplete. S14 retains offer-ID tie-breaking.

Sensitivity evidence includes:

- an S02 history-weight sweep with A/B, A/C, and B/C exact tie thresholds of
  `0.555555...`, `0.645161...`, and `0.769230...`;
- S09 showing that min–max expands `79.99/80.00/80.01` into `0/.5/1` while direct
  normalization preserves the two-hundredths percentage-point spread;
- S07 showing rank differences under missing-data policies;
- S12 showing an A/B rank reversal after adding C under min–max but stable A/B
  ordering under direct normalization; and
- the controlled T8 value mapping exactly from `33.33` to `.3333` at `n=3`.

Full scores and criterion contributions are reproducible with:

```powershell
.\.venv\Scripts\python.exe -m tools.t9_scoring_evaluation
```

## Runtime boundary confirmation

- Decision Core source and the complete `DecisionResult` dataclass are unchanged.
- Runtime strategic-profile constructors and WSM criteria are unchanged.
- MOQ, scoring, normalization, contributions, ranking, and tie-breaking are unchanged.
- Runtime packages do not import `tools.t9_scoring_evaluation`.
- T8 history remains contextual and provenance remains outside Decision Core.
- Odoo/application adapters, API, persistence, frontend, and Compose runtime are
  unchanged.
- The evaluator requires no Odoo service, credential, live fixture, or network.
- Existing T8 live evidence is referenced but was not re-run or represented as T9
  live evidence.

## Verification record

Local validation used the project `.venv` on Python 3.14.7; Python 3.11 remains the
project and CI baseline.

| Command/check | Result |
| --- | --- |
| Pre-change `pytest -m "not integration and not e2e" -v` | 180 passed, 23 deselected |
| `ruff format --check .` | Passed; 79 files already formatted |
| `ruff check .` | Passed |
| `python -m compileall application backend frontend decision_core odoo_adapter tools` | Passed |
| Focused T9 plus architecture tests | 27 passed |
| Final `pytest -m "not integration and not e2e" -v` | 197 passed, 23 deselected |
| `python -m pip check` | No broken requirements |
| `python -m tools.t9_scoring_evaluation --compact` | Passed; deterministic JSON emitted |
| `podman compose --env-file .env -f infra/odoo/compose.yaml config --quiet` | Passed with project-local provider |
| `git diff --check` | Passed; only Git line-ending conversion warnings |
| Odoo live tests | Not required or run; T9 changes no Odoo/runtime path |

The fast suite reported the two existing FastAPI/Starlette dependency deprecation
warnings and a local pytest cache warning. No test failed.

## Acceptance criteria

| # | Criterion | Status | Evidence |
| ---: | --- | --- | --- |
| 1 | Start from merged T8 main | PASS | fetched `origin/main`; both at `948c092` before branching |
| 2 | Baseline passes | PASS | 180 passed, 23 deselected |
| 3 | Normalization alternatives | PASS | direct, min–max, bands in design/evaluator/tests |
| 4 | Missing-history alternatives | PASS | five policies compared and tested |
| 5 | Candidate weights for all profiles | PASS | exact-sum profile table and tests |
| 6 | Required scenarios | PASS | deterministic S01-S15 matrix |
| 7 | Sensitivity/ranking flips reproducible | PASS | JSON report, sweeps, thresholds, policy/set experiments |
| 8 | Sample-size limitation accurate | PASS | explicit PoC-only threshold statement |
| 9 | Hard constraints precede scoring | PASS | explicit evaluator partition and all-policy S11 regression |
| 10 | Runtime Decision Core unchanged | PASS | no runtime source diff plus architecture regression |
| 11 | Explicit recommendation | PASS | GO at top of design and handoff |
| 12 | Exact implementation contract | PASS | ten bounded rules in design document |
| 13 | Repository documentation | PASS | design, handoff, README, implementation log |
| 14 | CI | Pending branch publication | Local quality-equivalent checks pass; report hosted checks at final handoff |

## Limitations and next increment

T9 is synthetic policy evaluation over one bounded T8 metric. It does not establish
statistical reliability, causal supplier quality, production representativeness,
calibrated weights, time decay, product/category segmentation, persistence, or
autonomous selection. Expected Arrival remains an operational schedule, not a
supplier promise. The minimum sample size of three is not a confidence guarantee.

The next increment may implement only the opt-in internal scoring contract in
`docs/T9_SCORING_DESIGN.md`. Public API exposure, Odoo changes, persistence, and
frontend work require later explicit scope. This branch must not be merged by the
implementing agent.
