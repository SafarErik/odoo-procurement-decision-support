# T10 Handoff — Bounded, Opt-In Historical Performance Scoring

## Decision

**CONDITIONAL — implementation and local fast evidence complete; hosted CI pending.**

T10 implements the fixed T9 policy as an internal, explicitly invoked capability.
It does not expose history through the public HTTP API and does not change Odoo,
the T8 KPI calculation, persistence, provenance placement, or the frontend.

Branch: `codex/t10-bounded-historical-scoring`

Base `main`: `58e3cfe92c8766093274571b87ad81af8b1bc8a1`

The final branch commit and hosted CI status are reported in the delivery handoff;
this document cannot self-reference its own commit SHA.

## Preconditions and baseline

`git fetch --prune origin` completed before branching. Local `main` and
`origin/main` both resolved to `58e3cfe`, the merge commit for PR #10. The merged
state contains `docs/T9_SCORING_DESIGN.md`, `docs/T9_HANDOFF.md`, the accepted T9 GO
decision, and the repository-side accepted policy record.

The pre-change fast baseline on that exact commit was:

```text
pytest -m "not integration and not e2e" -v
197 passed, 23 deselected
```

The local interpreter was Python 3.14.7. Python 3.11 remains the repository and CI
compatibility baseline.

## Implemented architecture

```text
T8 SupplierHistoricalPerformance + CanonicalDecisionInput
                         |
                         v
application explicit mapping (no provenance)
                         |
                         v
SupplierHistoricalPerformanceInput + HistoricalScoringProfile
                         |
                         v
MOQ constraint -> complete eligible-set activation
                 |                         |
                 | inactive                | active
                 v                         v
exact legacy DecisionResult       shared WSM scorer + history contribution
                 \_________________________/
                              |
                              v
                  HistoricalScoringResult
```

The Decision Core remains independent of `application`, `odoo_adapter`, FastAPI,
HTTP schemas, provenance, and T9 analysis tooling. The shared private scorer is used
by both the existing two-criterion entry point and the opt-in historical entry point;
the WSM implementation was not copied.

## New Decision Core contracts

- `SupplierHistoricalPerformanceInput`: stable supplier ID, metric ID, value,
  sample size, and scoring availability only.
- `HistoricalPerformanceAvailability`: `usable` or `withheld` at the core boundary.
- `HistoricalScoringProfile`: versioned three-criterion policy plus its exact legacy
  fallback profile.
- `HistoricalCriterionContribution`: the existing numeric trace plus sample size and
  deterministic history explanation.
- `HistoricalScoringResult`: wrapped `DecisionResult`, activation flag,
  deterministic explanation, and sorted affected offer/supplier IDs.
- `evaluate_historical_decision()`: separate opt-in entry point.

The existing `CriterionContribution` dataclass remains unchanged; only the active
history item uses its specialized subtype. Legacy contribution fields, numeric
values, and ordering are unchanged. `DecisionResult` retains the same four fields.

## Application mapping

`evaluate_procurement_decision_with_history()` accepts a
`CanonicalDecisionInput` and an explicit `HistoricalScoringProfile`. It rejects a
profile whose legacy fallback does not equal the canonical two-criterion profile,
maps T8 availability to the smaller core availability enum, and passes no warning,
window, source, or provenance field into the Decision Core.

## Profiles

| Versioned opt-in profile | Price | Lead time | History | Exact fallback |
| --- | ---: | ---: | ---: | --- |
| `cost_focused_history_v1` | `0.60` | `0.25` | `0.15` | existing `cost_focused()` |
| `urgent_history_v1` | `0.25` | `0.60` | `0.15` | existing `urgent()` |
| `risk_averse_history_v1` | `0.30` | `0.30` | `0.40` | existing `balanced()` |

Every new profile validates finite, non-negative `Decimal` weights summing exactly
to `1`. These are transparent PoC choices, not empirical optimization.

## Activation, fallback, and explanations

MOQ eligibility is evaluated before history. History activates only if the eligible
set is non-empty and every eligible offer's supplier has one usable
`delivery_schedule_adherence` value: present, finite, within `[0, 100]`, and with
`sample_size >= 3`.

When active, normalization is exactly `raw_value / 100`. Every eligible ranked offer
has a benefit contribution with raw percentage, separate sample size, normalized
value, historical weight, weighted contribution, and deterministic text. Total score
is reconstructed exactly from all contributions. Ranking remains score descending,
then stable offer ID ascending.

When any eligible history is missing or withheld, history is inactive for the whole
set. The wrapper reports:

```text
historical criterion inactive: at least one MOQ-eligible offer has missing or withheld history
```

It also returns affected offer and supplier IDs in sorted order. The wrapped result
is the exact existing two-criterion `DecisionResult`; there is no history
contribution, imputation, penalty, confidence factor, weight redistribution, or
history-based exclusion. History belonging only to an MOQ-ineligible supplier is
irrelevant to activation. An all-excluded set returns the exact baseline plus the
deterministic `no MOQ-eligible offers` status.

## Supplier joins

Joins use stable supplier ID only. Multiple offers may share one supplier history
value. Duplicate history for a supplier and history for an unknown supplier fail
closed. Empty identities fail in the input contract. Input order does not change
activation, scores, explanations, exclusions, or ranking.

## Regression evidence

`tests/test_historical_scoring.py` executes the complete accepted T9 matrix S01–S15
against the runtime path and compares activation, ranking, and exact scores with the
preserved T9 evaluator. It also covers profile validation, direct normalization,
exact score reconstruction, legacy fallback equality, sorted inactive context,
all-excluded handling, duplicate/unknown suppliers, multiple offers per supplier,
input-order independence, invalid and non-finite percentages, sample sizes 0–3,
T8 application mapping, profile mismatch, and provenance exclusion.

Focused implementation evidence:

```text
pytest tests/test_historical_scoring.py tests/test_t9_scoring_evaluation.py \
  tests/test_decision_core.py tests/test_decisions.py tests/test_decision_api.py \
  tests/test_architecture.py -v
114 passed
```

The public route and schemas remain unchanged. Existing API tests cover the response
contract and OpenAPI registration; T10 does not add a historical request field,
response field, profile, or endpoint.

## Validation status

| Command | Result |
| --- | --- |
| `ruff format --check .` | PASS |
| `ruff check .` | PASS |
| `python -m compileall application backend frontend decision_core odoo_adapter infra/odoo/addons/t7s_inventory_history_projection` | PASS |
| `python -m pip check` | PASS — no broken requirements |
| focused T10/T9/core/application/API/architecture selection above | PASS — 114 passed |
| `pytest -m "not integration and not e2e" -v` | PASS — 222 passed, 23 deselected |
| `pytest -m "integration and not e2e" -v` | PASS — 21 passed, 2 skipped, 222 deselected |
| project-local `podman-compose --env-file .env -f infra/odoo/compose.yaml config` | PASS |
| `git diff --check` | PASS |

The integration selection was rerun after restoring the existing local services and
a localhost-only tunnel for the known `win-sshproxy` forwarding fault. The two
controlled T7-S/T8 live gates skipped because their opt-in flags remained disabled;
T10 changes no Odoo path, so this is not new Odoo live evidence. The temporary API,
tunnel, services, and Podman machine were stopped after validation. Hosted CI cannot
be reported as passing until the branch is pushed and the actual GitHub checks
finish.

## Acceptance criteria

| # | Criterion | Status | Evidence |
| ---: | --- | --- | --- |
| 1 | Starts from merged T9 main | PASS | fetched base `58e3cfe`, PR #10 merge |
| 2 | Existing fast baseline passes | PASS | 197 passed, 23 deselected |
| 3 | Historical scoring explicit and opt-in | PASS | separate profile and evaluator |
| 4 | Existing profiles unchanged | PASS | legacy constructor regressions |
| 5 | New weights sum exactly to one | PASS | model validation and tests |
| 6 | MOQ before activation | PASS | eligible-set activation tests |
| 7 | Complete usable eligible set required | PASS | S06–S08 and focused tests |
| 8 | Exact baseline fallback | PASS | full dataclass equality regression |
| 9 | Missing history never becomes zero | PASS | withheld contract and fallback |
| 10 | Insufficient history does not exclude | PASS | fallback preserves eligible set |
| 11 | Direct `value / 100` normalization | PASS | contribution and parity tests |
| 12 | Active contributions reconstruct scores | PASS | exact Decimal sum regression |
| 13 | Deterministic inactive explanation | PASS | exact text and sorted IDs |
| 14 | Duplicate, unknown, ambiguous joins fail closed | PASS | stable-ID validation tests |
| 15 | Multiple offers per supplier | PASS | shared-history regression |
| 16 | All T9 scenarios executable | PASS | S01–S15 runtime parity |
| 17 | Legacy Decision Core unchanged | PASS | legacy core suite |
| 18 | Public API unchanged | PASS | existing API regression suite |
| 19 | Runtime does not import T9 tooling | PASS | AST architecture scan |
| 20 | Provenance remains outside core | PASS | architecture scan and mapper test |
| 21 | Odoo, persistence, frontend unchanged | PASS | source scope/diff review |
| 22 | Local checks pass | PASS | full command matrix above |
| 23 | Hosted CI passes | PENDING | requires push and completed checks |
| 24 | Documentation reflects scope | PASS | README, core docs, log, handoff |

## Limitations

- The `n >= 3` threshold is a PoC availability rule, not statistical reliability.
- The metric measures adherence to the operational Expected Arrival used by T8; it
  is not proof of a supplier promise.
- No confidence weighting, time decay, calibration, segmentation, uncertainty
  estimate, or outcome validation is implemented.
- The three profiles are not production validated.
- Historical scoring is internal only; no public API or UI selects it.
- No decision persistence, automatic supplier selection, or purchase-order write is
  introduced.

## Recommended next increment

Keep public exposure out of scope until this internal policy is reviewed from the
completed branch and the PoC limitations are accepted. A later, separately approved
increment may design an authenticated public selection contract and UI explanation,
without changing T8 evidence semantics or treating the weights as calibrated.
