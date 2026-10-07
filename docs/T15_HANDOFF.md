# T15 — controlled planning API, stress scenarios and immutable cases

## Current controlled hybrid completion — 2026-10-07

**LOCAL CONTROLLED T15 ACCEPTANCE PASS; USER REVIEW/PUBLICATION AND NEW-SHA CI PENDING.**
The user renewed the history key, selected the existing fixture and delegated
the fastest sound implementation choice. The key now authenticates uid 8; the
read-only projection security contract passed (1 test / 19 deselected, 1.80 s).
The bounded read found no confirmed company-1 orders for suppliers 51/52/53.
The chosen path therefore uses live Odoo quotations plus separately synthetic ML
history; actual Odoo receipt/model promotion stays open.

The new `/api/v2/procurement/planning-cases/from-odoo` POST reuses strict controlled
DTOs, bearer/body-size guards, saved inference, unchanged MILP and immutable
storage. It reads the selected group and currency through existing adapters after
locked idempotency lookup, checks expected identities/prices, and stores separate
Odoo/business/synthetic/clock provenance and comparison identity. The original
synthetic POST and V1 behavior remain supported. GET/exact replay do not acquire
sources; scenarios reuse the stored parent and assessments.

Offline preparation genuinely trains/saves a synthetic artifact in the fixture's
company/product/unit domain with a new model/training ID and recorded dataset.
It does not patch manifests, change source checks or feed observed receipts into
the synthetic model. Full [boundary/contract](T15_ODOO_COMPATIBILITY_PLAN.md) and
[terminal variant](T15_DEMO.md#controlled-odoo-quotation-demo).

Final Python 3.11 fast checks: **433 passed / 45 deselected / one upstream warning,
39.46 s**. Actual isolated PostgreSQL T15+V1: **22 passed / one warning, 25.90 s**.
Controlled live Odoo + saved model + CBC + PostgreSQL/API produced USD **1,850**
minimum (50/0/150), USD **2,200** lower-exposure alternative (100/100/0), and USD
**2,200** C-outage minimum (100/100/0). The API used TestClient against real Odoo
and PostgreSQL, not a new separate Uvicorn/browser run. With Odoo/model disabled
in a fresh TestClient context, base/child GET and exact base/child replay returned
200 with equal snapshots; fresh creation returned 503.

Verification started the existing stopped disposable database without replacing
its credentials/data, then used a separate `t15_odoo_verify_*` database. The known
Windows forwarding issue required a hidden localhost-only tunnel. The temporary
database, tunnel and credential file were removed; the test container returned to
its original stopped state. Odoo remains running and no Odoo business record changed.
Reports are ignored under `.artifacts/t15-odoo-demo/` and
`.artifacts/t15-odoo-verify-00ee8a59ce1f4dd4b926f936e8e4bf43/`.

The prior published HEAD `ab8d7b21b18ac4b7323e0ed32f637ae351658786` has successful
CI, but does not cover this uncommitted increment. The user's previous PostgreSQL
retry remains user-unconfirmed and is not overwritten by agent service acceptance.
Drive was not changed here. Controlled T15 is locally ready to close after review,
publication and exact-SHA CI; the next product capability is the T16 planning
cockpit. Observed history/model validity, approval/PDF and full V2 remain open.

## Historical initial Odoo/model readiness, before key renewal — 2026-10-07

The user committed/published the prior documentation as
`ab8d7b21b18ac4b7323e0ed32f637ae351658786`. PR #17 remains open; exact-head
`quality`, `container-api-integration` and GitGuardian checks succeeded, verified
through authenticated GitHub metadata. Earlier SHA/run records below remain
historical; they do not cover the new uncommitted compatibility-plan documentation.

The user authorized investigation/implementation of the Odoo/model dependency
and selected reuse of the controlled development fixture. Read-only preflight:
existing RFQ identity and group 2 access succeed; four focused live RFQ/T6 tests
passed, 16 deselected. The dedicated history key returns HTTP 401. Known history
uses supplier 55/product 57, not comparison suppliers 51/52/53/product 54; no
matching history or model is inferred. The synthetic T14 artifact explicitly
rejects Odoo-derived evidence and a different company/product/unit domain.

[Reviewable readiness and implementation plan](T15_ODOO_COMPATIBILITY_PLAN.md)
records the stable input/API boundary, missing business/history/model contracts
and meaningful acceptance checks. Renew the dedicated key using the existing
manual procedure, then confirm and verify it read-only. No key was printed,
Odoo UI/write performed, database reset or compatibility guard weakened.
No product code was implemented; full Odoo/model acceptance and the user's prior
PostgreSQL retry remain unverified. Current documentation is unstaged/uncommitted;
Drive was not changed by this readiness task. User retains merge control.

## Historical publication, user verification and Drive synchronization — 2026-10-06

The user published `feature/T15-implementation` at
`200af3e79ac82640fac882b95c2cf85ed80ff588` and opened
[PR #17](https://github.com/SafarErik/odoo-procurement-decision-support/pull/17).
Authenticated GitHub checks confirm the PR is **open, not merged**;
main remains `247914ac05663d7358d53036c08750d9390d1baa`.
Exact-head [Quality 37523314998](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37523314998),
[Container/API 37523314994](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/37523314994)
and GitGuardian succeeded. No new test count is inferred from workflow metadata.

The user confirmed the terminal demonstration worked, but their database selection
reported **14 passed / 7 setup errors / 2 warnings, 11.81 s**. The seven T15 tests
share a temporary saved-model fixture; `WinError 5` under Windows Temp blocks setup
before their business/SQL assertions. The inspected shared pytest root is owned by
`CodexSandboxOffline`, strongly supporting a cross-identity permission conflict.
The user's full traceback is unavailable, so the precise nested path is unconfirmed.

The [persistence guide](PERSISTENCE_DEVELOPMENT.md#windows-permissionerror-winerror-5-during-fixture-setup)
now creates a fresh ignored GUID directory in the current user's terminal for
each pytest invocation, with separate `--basetemp` and `cache_dir`. No ACL changes
or shared Temp deletion. The first workaround trial omitted parent creation:
383 passed / 40 setup errors (`WinError 3`). After adding that step, actual Python
3.11 fast acceptance passed: **423 passed / 44 deselected / one upstream warning,
24.33 s**. The user's real PostgreSQL retry remains pending; earlier local database
success and hosted CI do not overwrite their failed run.

On explicit request, Hungarian Drive 00/01/02/03/04/06/07/08/99 were synchronized:
controlled T15 is implemented/published/CI verified; AC-V2-08/10 pass in that slice;
PR #17 is open; V2 Odoo assembly, observed-model promotion and full V2 remain open.
Task assignments and repository-versus-Drive responsibilities now agree. 05 was
checked and retained. Native readback verified all intended text, existing heading/
list roles, date chips, native links, new GitHub links and historical records.

These documentation changes remain unstaged/uncommitted/unpushed, outside the
published SHA's hosted evidence. Next: user database retry and PR review/merge
decision, then plan the smallest V2 Odoo/model boundary increment before T16.
No production code, Odoo operation, frontend or approval/PDF was added.

## Historical terminal demonstration and verification, before publication — 2026-10-06

The user committed the consolidation as `d1b7acd3070f4c10f58f5bf4b5a61897cf2314ba`.
The separate demo increment is uncommitted. [Terminal procedure](T15_DEMO.md)
and `python -m tools.t15_demo prepare` generate matched synthetic model/base/outage
files; `run` calls the existing loopback API, stores per-run replay keys/responses
and checks base/child retrieval plus exact base replay. Existing tests share the
same moved fixture generator. There is no new endpoint, training-in-HTTP path,
solver/model change, dependency, Odoo flow, frontend or approval/PDF.

Fresh Python 3.11 fast evidence: **423 passed / 44 deselected / one upstream warning,
37.82 s**. Focused actual PostgreSQL V1/T15 acceptance: **21 passed / one warning,
22.11 s**. Actual separate Uvicorn/HTTP demo produced EUR **102 / 109** base plans
and EUR **106** outage minimum. After restarting without a configured model,
base/child GET and exact base/child replay returned `200` with equal snapshots;
fresh base returned `503`. This evidence includes the audit fixes and new fixture
location; it does not overwrite the earlier service results below.

Verification reused the running disposable test container but created a separate
temporary database, preserving existing test cases. Windows 55432 remained refused;
a temporary localhost-only tunnel was used. The task database, owned backend/tunnel
processes and local credential file were removed afterward; the existing test/Odoo
containers remain running. Generated reports are ignored local review artifacts.
No Odoo business call, browser or full service suite was run.

Authenticated GitHub reads still find main `247914ac05663d7358d53036c08750d9390d1baa`;
the entry local `d1b7acd` could not be resolved and has zero hosted workflow runs.
Hosted T15 CI and Drive synchronization remain pending. Next: user review/publication,
exact-SHA CI, then explicitly requested affected Hungarian document updates and
the V2 Odoo/model demonstration boundary before the next product capability.

## Historical consolidation review record, before publication — 2026-10-06

The user has committed the controlled slice and audit fixes locally as
`921673493d63b3e5fadd9189f50ee5b644308871` on `feature/T15-implementation`.
GitHub could not resolve that SHA and returned no workflow runs for it at this
check. Remote main remains `247914ac05663d7358d53036c08750d9390d1baa`;
its successful T13/T14 checks do not establish T15 hosted acceptance.
The documentation/workflow consolidation is a separate uncommitted working-tree
change. [README](../README.md) owns current capability/publication status;
[the terminal runbook](LOCAL_DEVELOPMENT_AND_SSH.md) and
[persistence guide](PERSISTENCE_DEVELOPMENT.md) own current execution procedures.

The implementation evidence below is preserved as a dated record. PostgreSQL and
loopback HTTP acceptance predates the subsequent audit fixes; no new service/live
acceptance is claimed by this consolidation. Full V2 and observed integration
remain open. Drive still reflects the previously synchronized T15 proposal.

## Historical implementation handoff — 2026-10-05

Status, 2026-10-05: **CONTROLLED LOCAL IMPLEMENTATION AND ACCEPTANCE PASS;
REVIEW PENDING; HOSTED T15 CI UNVERIFIED.** Entry branch was
`feature/T15-implementation`, HEAD `aac86eb7c7081fc3a780efa4da351f5616cd1185`,
containing the user-committed proposal. This task leaves changes unstaged,
uncommitted and unpushed. T13/T14 hosted evidence is historical and does not cover
these edits. [Reviewed plan](T15_IMPLEMENTATION_PLAN.md).

## Implemented boundary

Controlled, explicitly synthetic receipt evidence and attributed business bundles
are assembled into T14 features and T13 terms. New base creation loads the
owner-configured saved T14 artifact, performs inference and exact risk joins, then
calls the unchanged T13 planner/CBC adapter. Training stays offline. There is no
T15 Odoo adapter, observed data relabelling, frontend, final approval or PDF flow.

| Operation | Behavior |
| --- | --- |
| `POST /api/v2/procurement/planning-cases` | Controlled base creation; canonical UUID `Idempotency-Key`; `201` stored result, `200` exact replay |
| `POST /api/v2/procurement/planning-cases/{case_id}/scenarios` | Explicit perturbation of a stored base; creates an immutable child; same shared key namespace and replay contract |
| `GET /api/v2/procurement/planning-cases/{case_id}` | Stored snapshot only; no source read, model load, training, inference or solve |

All three reuse the fail-closed `T12_TRUSTED_CALLER_TOKEN` bearer gate. Missing/wrong
token is `401`; unconfigured gate is `503`. The secret proves possession, not buyer
identity. Business source/approval references are caller attribution. Scenario
demand changes represent attributed simulations, not final operational approval.

Requests forbid unknown fields, use decimal strings and strict integers/booleans,
and require explicit UTC simulation timestamps and ISO dates. Limits: 1–10 suppliers,
3–50 prior receipts each, 1–3 epsilon values, 256 KiB streamed JSON body (`413` above
the limit). Mandatory MOQ absence is explicit `null`; there are no currency/unit,
quantity-approval or delivery-promise defaults. Each commercial bundle has one
declared source for all its fields; assembly expands it into separate T6 field
provenance. Receipt source identity and as-of evidence remain separately recorded.
HTTP cannot supply features, predictions, future labels, coefficients or artifact paths.

Invalid input/validity returns `422`; absent case `404`; conflicting key reuse `409`;
unavailable persistence/artifact/solver runtime a sanitized `503`. Valid completed
solver runs can be stored with `optimal`, `infeasible`, `no_proven_optimum` or
`solver_error`. HTTP success means stored evidence, not optimality or approval.
Unproven incumbents never become plans; a proved minimum may survive a failed
alternative stage. Stored failures replay unchanged; recomputation requires a new key.

## Scenarios and storage

Supported perturbations: supplier outage, capacity reduction, demand increase,
price increase and combined disturbance. Values must change in the named direction;
combined requires at least two disturbance types. Unknown/duplicate suppliers and
no-op changes fail closed. This slice permits children of a base only.

Commercial-only scenarios reuse frozen features/assessments, revalidate context,
time and full feasible quantity coverage, and rerun the same T13 planner. They do
not reload or infer a model. Beyond-score-range requests fail closed rather than
narrowing physical bounds. Changed history/model/context/cutoff requires a new base.
Children store complete derived requests/results, delta, parent ID and updated
field provenance. Minimum-cost comparisons include allocation, exact total-cost
and exposure differences and statuses; missing plans yield unavailable comparison.
A demand change's cost difference is not a like-for-like saving claim. Distinct
epsilon alternatives and their stage statuses remain in each complete result.

Migration `20261005_01` adds one `planning_cases` JSONB table with parent FK,
version/hash, creation time and unique key/fingerprint. PostgreSQL transaction
advisory locks serialize same-key creation; one row atomically stores case and key
mapping. A database trigger rejects all UPDATE and DELETE operations. GET/replay
reconstruct and validate stored values without recomputation. Model manifest/hash,
model/training IDs, dataset/feature/label/mapping versions, actual paths and leaf
support, exact decimals/fractions, input receipts/policy/source provenance and
solver version/configuration are retained. Executable joblib bytes stay outside DB.
Existing V1 tables, serializers, records and routes remain intact.

## Configuration and verification

Keep application PostgreSQL configuration `DECISION_DATABASE_URL` in ignored `.env`.
The backend loads that file; Alembic does not. Export the configured application URL
to the current PowerShell process before applying migrations explicitly:

```powershell
$env:DECISION_DATABASE_URL = .\.venv\t13-check\Scripts\python.exe -c "from backend.app.config import settings; print(settings.decision_database_url.get_secret_value())"
.\.venv\t13-check\Scripts\python.exe -m alembic upgrade head
```

For the separate disposable test database, follow
[the persistence guide](PERSISTENCE_DEVELOPMENT.md#apply-or-inspect-migrations).
Set `T15_TRUSTED_MODEL_DIRECTORY` only to an owner-generated local T14 model directory
(for example the `model` directory
from the existing offline T14 CLI). A checksum is integrity evidence, not artifact
authenticity; HTTP callers never choose executable files. Blank configuration
disables new base creation while existing GET/replay/scenarios remain stored-only.

Subsequent audit fixes, 2026-10-05: the shared bearer guard rejects non-ASCII
credentials with `401` and invalid token configuration with `503`; T15 rejects
unrepresentable history/score-validity windows with `422`, without solving or
storing a case. T12 creation now keeps its blocking transaction and awaited Odoo
reads in a FastAPI worker. Unused frontend health code and solver risk-scale storage
were removed. Audit working-tree verification: **419 fast tests passed / 44
deselected / one upstream warning, 30.89 s**, plus Ruff format/lint, compilation,
dependency, whitespace and quiet Compose configuration checks. The same-event-loop
concurrency regression uses controlled bounded lock contention. PostgreSQL/service,
live Odoo, browser and hosted CI checks were not rerun for these fixes; the historical
acceptance evidence below predates them. See [implementation log](IMPLEMENTATION_LOG.md).

Initial implementation's local Python 3.11 evidence (before the subsequent audit fixes):

- Fast regression: **418 passed / 44 deselected / one upstream Starlette warning,
  37.57 s**. Includes real saved-model/CBC composition, all five scenarios checked
  against the existing independent exhaustive oracle, strict input/artifact gates,
  failure proof semantics, GET/replay traps and legacy regressions.
  The final blank-setting normalization was separately rechecked with the targeted
  API guard/configuration test: 1 passed in 3.50 s.
- PostgreSQL T15 plus legacy T11/T12 persistence: **21 passed / one upstream warning,
  22.14 s**. Separate sessions/HTTP round-trip, immutable fields/key/deletion,
  concurrent same-key compute-once behavior, conflicts and atomic rollback verified.
- Actual Uvicorn/loopback HTTP smoke: base `201`, EUR **102 / 109**; with the configured
  manifest temporarily unavailable, GET and exact replay `200`, scenario `201`,
  fresh base `503`. Server stopped and manifest restored afterward. Detailed local
  evidence is generated under ignored `.artifacts/t15/`; fixtures/models are synthetic.
- Ruff format/lint, compilation, dependency and whitespace checks passed. The
  integration workflow now includes `supplier_evaluation/**` in its path filters;
  existing Python 3.11 jobs discover the new fast/PostgreSQL tests. No new hosted run
  was executed, and no prior commit's success is attributed to this working tree.

The isolated existing T11 PostgreSQL test Compose service was started with synthetic
credentials. It was healthy in Podman but Windows port 55432 remained refused;
tests used a temporary localhost-only SSH tunnel on 55433. This is a workaround,
not resolution of the historical forwarding failure. The temporary HTTP server,
tunnel and test container were cleaned up; the user's Odoo stack was left running.
No Odoo business/live contracts, browser E2E or complete service suite was run here.

Reproduce fast coverage with the standard repository checks. For the separate
disposable test database, use the existing `infra/persistence/compose.test.yaml`,
set `T11_TEST_DATABASE_URL`, and run:

```powershell
.\.venv\t13-check\Scripts\python.exe -m pytest tests/integration/test_t15_planning_postgres.py tests/integration/test_decision_case_postgres.py -v
```

Those fixtures downgrade/reset their isolated test database; never point the test
URL at an application or Odoo database. They require actual PostgreSQL services.

Full V2 and observed Odoo/model promotion remain OPEN. Synthetic technical acceptance
does not satisfy AC-V2-01's observed Odoo input gate or full AC-V2-13. The current
model rejects observed contexts. Live commercial mappings, historical availability,
source-derived labels and an observed-compatible model/schema/mapping still require
separate audited acceptance. Drive was not edited in this implementation task;
its T15 proposal/status should be synchronized after review.
