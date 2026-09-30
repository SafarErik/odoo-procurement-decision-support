# V2 Reflex frontend capability spike

Date: 2026-09-30. Recommendation: **GO WITH CONDITIONS** for a bounded thesis
PoC. Reflex supports the requested workflow with native components and a
replaceable client boundary. This evidence does not promote V2 or authorize
production frontend implementation.

## Existing baseline and preservation

Reviewed the optimization, Odoo-input and ML-risk reports, existing RFQ
frontend/client, architecture tests, and T1/T12 documentation before editing.
The accepted frontend is a separate Reflex RFQ ledger using an async HTTP client
for documented FastAPI health/RFQ DTOs. It has no Odoo/database access. T12 stores
immutable WSM decision cases; it has no allocation/scenario/PDF API. Its existing
final-decision endpoint is not a V2 allocation approval endpoint.

Starting main lineage: `71396e8924f6a1f60daf8b45f02861adf21a25e5`. Prior spikes
were preserved in `0a316f8` (optimization), `706a882` (input audit) and local
commit `ffa2939` (ML, made before this branch). Work is isolated on
`spike/v2-reflex-frontend-capability`. Earlier uncommitted-handoff statements
remain historical records. No evidence was discarded, pushed or merged. No PR,
Google Drive update or automatic baseline promotion occurred.

The default `/` RFQ page remains unchanged. `/v2-cockpit` is registered only with
`ENABLE_V2_FRONTEND_SPIKE=1`; fresh-process assertions verified both settings.
Actual execution used Python 3.14.7, Reflex 0.9.11.post1,
reflex-components-recharts 0.9.3 and Node 24.20.0. Python 3.11 remains the accepted
compatibility baseline; execution on it remains unverified.

## Prototype scope and implemented workflow

One workspace contains case facts, tabs for procurement plans, supplier evaluation
and stress testing, plus a persistent approval panel. Desktop cards compare three
alternatives; selection exposes allocations and explanations. Native Radix tables,
cards, badges and controls use system fonts and subdued teal selection accents.
Narrow layouts stack panels and allow table scrolling. No authored JavaScript,
separate frontend framework or animation was added.

The header distinguishes contextual product/UoM, supplemental demand/delivery
terms, and allocation/cost-premium policies. All values are synthetic: contextual
does not claim a live Odoo source. Original case terms remain visible while
scenario output names the changed context and quantity. The fixture-specific
header is not a general case editor or provenance framework.

The four-supplier table includes neutral IDs, price, capacity, MOQ, delivery
condition, prior adherence, model score/class and source status. Expandable details
show recorded tree path, quantity input, leaf support and model identifier.
Scores are explicitly uncalibrated synthetic model outputs whose predictive
usefulness is unestablished. Zero leaf score does not guarantee delivery.
Supplier D is contextual only: no commitment/risk input was admitted for allocation.
The frontend displays that status; it does not decide supplier eligibility.

| Original plan | Allocation A/B/C | Cost EUR | Premium vs minimum | ML score exposure | Largest share | Suppliers |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Minimum Cost | 60 / 40 / 0 | 1020 | 0% | 0.2921 | 60% | 2 |
| Balanced | 60 / 0 / 40 | 1040 | 1.9608% | 0.17526 | 60% | 2 |
| Lower-Risk Alternative | 29 / 0 / 71 | 1071 | 5% | 0.084709 | 71% | 2 |

All three satisfy demand 100, maximum two suppliers and 80% concentration.
Balanced permits up to 2%; its realized premium is slightly lower. Presentation
rounding does not alter decimal DTO strings. Lower-risk describes the model
objective, not validated delivery resilience. Each selected plan shows exact
supplier quantities/shares, cost, premium, exposure, supplier count, feasibility
and recorded explanation. Capacity/cost-premium statements follow optimizer
evidence; zero allocation is described as an objective solution without inventing
delivery exclusion or causal ML explanations. No LLM is used.

Scenario controls cover supplier outage, capacity reduction to 30, demand increase
to 120, price increase by 20%, and combined supply disruption. A client call returns
a complete replacement result. Selection retains the same policy only when present
in the new result; old plans disappear during loading. Deltas compare each policy
against its original case, not against another alternative. With A unavailable,
the lower-risk plan becomes 0/20/80, cost 1090, exposure 0.05842; changes are
+19 EUR and -0.026289 exposure.

Combined capacities 10/10/10 cannot meet demand 100. The UI states
"No feasible procurement plan exists under the selected conditions.", displays
the capacity reason and feasibility change, and returns no allocation or approval.

## Mock contracts and API boundaries

`frontend/v2_spike/contracts.py` defines neutral Pydantic case, supplier,
allocation, plan, result/delta, approval and PDF DTOs, separately from Reflex state.
Costs/scores are decimal strings. Approved plans use frozen nested DTOs/tuples.
These are illustrative contracts, not permanent API decisions.

`service.py` supplies an async `CockpitClient` protocol and a recorded-JSON mock
with a small artificial delay. Components do not read files, use transport, train
models or optimize. State calls the client and applies presentation transitions;
formatting/chart conversion lives in `presentation.py`. Supplied totals, shares,
feasibility, scores and explanations remain authoritative.

`tools/v2_frontend_fixture.py` is an **offline** generator using the existing
experimental optimizer and recorded ML scores (A/B 0.2921, C 0.0000). It freezes
baseline plus 15 bounded scenarios in `v2-reflex-frontend-fixture.json`. Global
demand/disruption cases repeat across supplier choices. The frontend never imports
the generator, solver, application, Odoo, persistence or ML packages. Reactive
state holds only the current result, not all fixture scenarios/training records.

Quantity-100 scores remain fixed under changed demand. The earlier ML spike's
quantity-dependent-feature versus fixed-coefficient limitation is inherited,
not resolved. These interactions demonstrate presentation, not re-inference,
live solver latency, production robustness or business forecasts.

## Charts and capability audit

Installed APIs were inspected before use. Native Recharts horizontal stacked bars
show supplier shares; an adjacent table supplies exact quantities and percentages.
A scatter plot shows total cost on x and weighted score exposure on y, with distinct
colors/shapes. Browser clicking selected the corresponding plan. Selection buttons
provide a keyboard-friendly alternative; comprehensive accessibility was not tested.

The installed scatter click event supplies no arguments. One native series per
plan binds its fixed ID, a small bounded composition appropriate for three plans.
No custom JavaScript handler is needed. Arbitrary large interactive frontiers need
another capability check. Axes/series here are deliberately fixture-specific.
Primary references: [Reflex scatter charts](https://reflex.dev/docs/library/graphing/charts/scatterchart/)
and [bar charts](https://reflex.dev/docs/library/graphing/charts/barchart/).
Installed behavior and browser results support the conclusion independently.

Reflex added native component dependencies to the existing lock:
`@radix-ui/react-accordion` 1.2.20, `react-debounce-input` 3.3.0 and `recharts`
3.10.1. This introduces no separately authored JS application or Python framework.

| Capability | Classification | Evidence / limitation |
| --- | --- | --- |
| Data tables | NATIVE / STRAIGHTFORWARD | Four-supplier and allocation Radix tables; no large-grid benchmark |
| Forms / inputs | NATIVE / STRAIGHTFORWARD | Native selects, bounded optional textarea, buttons |
| Tabs / navigation | NATIVE / STRAIGHTFORWARD | Three tabs in one workspace |
| Dialogs / drawers | NATIVE / STRAIGHTFORWARD | Installed APIs present; unused/not browser-tested; inline approval suffices |
| Charts | NATIVE / STRAIGHTFORWARD | Native bar/scatter; three bound series for click selection |
| State management | NATIVE / STRAIGHTFORWARD | DTOs, selection/current result, guarded transitions |
| Async API calls | NATIVE / STRAIGHTFORWARD | Awaited mock-client calls and loading yields; real V2 HTTP absent |
| Dependent updates | NATIVE / STRAIGHTFORWARD | Scenario replaces plans/chart/allocation/approval context |
| Loading / errors | NATIVE / STRAIGHTFORWARD | Busy flags, disabled actions, safe errors/recovery |
| Conditional rendering | NATIVE / STRAIGHTFORWARD | Native cond/foreach |
| Large result objects | POSSIBLE_WITH_SMALL_WORKAROUND | Bounded DTOs; future paging/server summaries; large payloads unmeasured |
| Approval | POSSIBLE_WITH_SMALL_WORKAROUND | UI locking; durable backend/version/idempotency contract required |
| PDF / downloads | POSSIBLE_WITH_SMALL_WORKAROUND | Native download event and pending DTO; real renderer/download unverified |
| Responsive layout | NATIVE / STRAIGHTFORWARD | 1440px desktop and narrow in-app viewport inspected |
| Component composition | NATIVE / STRAIGHTFORWARD | Panel/metric/card/chart helpers; verbose tree merits later extraction |
| Testing | POSSIBLE_WITH_SMALL_WORKAROUND | Existing pytest/async conventions plus manual browser smoke; sustained E2E absent |

No exercised core requirement showed high friction or impracticality. Unused
dialog and unmeasured large-payload classifications are provisional judgments.

## State, approval, PDF and maintainability

`CockpitState` holds one case/current result, selected ID, scenario draft, note,
four operation flags and explicit errors. Async generators yield before awaiting
the client so busy states can render; event guards also reject changes while
busy/approved. See [Reflex yield events](https://reflex.dev/docs/events/yield-events/).
Long solver/API jobs need later job/polling or background-event design; short mocks
do not establish long-job responsiveness or multi-user throughput. See
[Reflex background events](https://reflex.dev/docs/events/background-events/).

Approval requires a feasible current selected plan. The mock compares the reviewed
DTO with the fixture before returning an approval ID/hash. State checks case version,
scenario and plan identity, then locks plan/scenario/note/reload controls. Failure
leaves review open. Frozen nested plan data is not shared mutably across sessions.
This is **session-local** evidence, not durable/authenticated approval or backend
immutability enforcement. Restart/reload can lose approval. Production backend
must enforce all rules and persist the snapshot independently.

PDF is disabled until approval. Then the mock returns pending status with the same
approval ID/hash, and the UI states that the backend will generate it from that
snapshot. A future ready response produces native `rx.download`; tests reject
mismatched hashes. No PDF bytes/renderer were implemented and actual ready download
was not browser-tested. Frontend never rescored or recomputed the approved plan.
Future PDFs must use the persisted approval snapshot and its recorded context.

Loading, no selection, unavailable service, no plans, missing risk, infeasibility,
approval error/success and PDF pending have explicit paths. Missing risk remains
null/withheld and has no fabricated risk plan. Service failures clear stale results.
A collapsed prototype-state control exposes mock errors without dominating the
procurement flow.

Maintainability is adequate for a bounded thesis PoC: DTO/client/view/state are
separate, domain algorithms do not leak into components, and comparison/scenario
state stays small. The approximately 630-line component file is verbose but uses
focused helpers; extract supplier/chart/approval panels as production scope grows.
Avoid raw training data, all scenarios, solver objects and transport errors in
reactive state. Real revisions, authorization, durability and long jobs are future
pressure points. A state-machine framework or complete frontend rewrite would be
disproportionate for this evidence.

## Future API needs (illustrative, not implemented)

| Conceptual operation | Frontend need | Backend responsibility |
| --- | --- | --- |
| GET case | Version, source status, terms/policies, risk DTOs | Fail-closed assembly/history and model context |
| POST optimize case | Three explained plans and result/revision IDs | ML/MILP execution; input/result association |
| POST case scenario | Base revision, explicit changes, replacement/deltas | Validate changes, create scenario revision, report infeasibility |
| POST approve plan | Case/scenario/result/plan IDs, expected revision, note, idempotency key | Authenticate identity, reject stale result, persist immutable snapshot |
| GET approved snapshot | Approved DTO/hash/audit context | Stored read without inference/optimization |
| GET approved PDF | Pending or ready PDF/reference bound to approval/hash | Generate/download from the same stored snapshot |

These operations do not replace T12 or prescribe permanent route names. A future
HTTP adapter should reuse safe-error/DTO conventions. Shared trusted-caller secrets
must not enter browser configuration; identity/access design requires separate
authorization. Measured execution latency may justify job-status/cancellation APIs.

## Testing and browser evidence

- Final fast suite: **370 passed, 37 deselected**, 18.03 seconds, including 21 focused
  frontend/state/boundary checks. Existing FastAPI/Starlette deprecations remain.
  First attempt had 369 passes and one Windows system-temp permission error; an
  ignored project-local pytest temp root resolved it.
- Ruff format/lint, Python compileall and pip check: PASS.
- Opt-in `reflex export --frontend-only --no-zip`: PASS, production build exit 0.
  This is compilation evidence, separate from browser interaction.
- Fresh-process route assertions: default index only; opt-in adds v2-cockpit.
- Fixture checks independently verify demand sums, capacity, concentration,
  supplier count, cost caps and weighted exposure with Decimal arithmetic.
- State tests cover loading cleanup, four requested scenario types/replacement,
  infeasible no-allocation state, selection, service/empty/risk errors, stale approval,
  approval failure, frozen snapshot/session isolation and PDF binding/download event.
  Import checks parse Python 3.11 grammar; they do not prove execution on 3.11.

Local browser smoke used Reflex frontend 3011/backend 8011 and synthetic mocks:
page load, four supplier rows/tree details, button/scatter selection, A outage and
deltas, explicit shortfall infeasibility, unavailable-service recovery, approval
failure/recovery, successful approval locking and PDF gating/pending. Desktop
1440 CSS pixels and narrow default viewport were inspected. Export temporarily
regenerated default connection settings; restarting the development preview fixed
this. It is Reflex-to-mock interaction, not real FastAPI V2 or automated browser E2E.

Screenshots (device scale can differ from CSS pixels):

- [Plans and native charts](screenshots/v2-reflex-plans.jpg)
- [Supplier evaluation/tree path](screenshots/v2-reflex-suppliers.jpg)
- [A outage/deltas](screenshots/v2-reflex-scenario.jpg)
- [Infeasible, no allocation](screenshots/v2-reflex-infeasible.jpg)
- [Unavailable service, no stale plans](screenshots/v2-reflex-error.jpg)
- [Approved plan/PDF pending](screenshots/v2-reflex-approved.jpg)

Integration/live Odoo contracts, container/API job, hosted CI, actual V2 HTTP,
real PDF rendering/download, production identity/durability, large payload/load
tests and Python 3.11 execution were **not run**. No Odoo/DB/cloud change was needed.
Existing API, Decision Core, ML training and solver behavior remain unchanged.

## Reproduce

From repository root in PowerShell with project-local frontend/dev extras:

```powershell
$projectRoot = (Get-Location).Path
$env:ENABLE_V2_FRONTEND_SPIKE = '1'
$env:PYTHONPATH = $projectRoot
# Existing Node runtime; this terminal's PATH only.
$env:PATH = "$env:LOCALAPPDATA\Author Software\nvm\installs\v24.20.0;$env:PATH"
Set-Location frontend
..\.venv\Scripts\reflex.exe run --frontend-port 3011 --backend-port 8011 --backend-host 127.0.0.1
```

Open `http://localhost:3011/v2-cockpit`; a fresh session permits another approval.
Remove the opt-in variable for the default RFQ-only application. Stop development
before export: both write the generated `.web` directory. No global Node selection
or other framework is needed. Offline `python -m tools.v2_frontend_fixture` requires
the existing optimization-spike extra and recorded ML JSON, not model training.
Never invoke the generator from frontend events.

## Explicit acceptance answers

1. **Full cockpit workflow? Yes**, synthetic case through local approval/PDF contract.
2. **Clear supplier ML evaluation/explanations? Yes**, table and expandable recorded
   path/support/context, with explicit uncalibrated-score wording.
3. **Clear MILP plan comparison? Yes**, three cards, shared metrics and allocation
   details; plans are offline recorded outputs.
4. **Allocation without fragile custom code? Yes**, native stacked bar and table.
5. **Adequate cost-risk alternatives? Yes**, native three-point scatter/selection;
   large frontiers are untested.
6. **Clean stress inputs/results? Yes**, bounded controls, async client, full replacement.
7. **Clear infeasible result? Yes**, explicit reason and no fabricated allocation.
8. **Clean human selection/approval? Yes for the prototype**; authenticated durable
   backend enforcement is still required.
9. **Clean backend-PDF workflow? Yes at UI/contract level**; actual renderer and
   downloaded PDF remain unverified.
10. **Understandable growing state? Yes within this bounded scope**; introduce
    revisions/job contracts before long-running production calls.
11. **Pure presentation/client layer? Yes**, transport/mock behind client, ML/MILP
    offline outside frontend; import boundaries tested.
12. **Custom JS/unsupported workaround needed? No authored JS or unsupported core
    workaround**; three bound series accommodate the native no-argument click.
13. **Practical Reflex visualizations? Yes** for bounded allocation/trade-off analysis.
14. **Maintainable thesis PoC? Yes**, separate contracts/client/state/views; extract
    verbose component panels incrementally as scope grows.
15. **Suitable V2 baseline? GO WITH CONDITIONS**, as a candidate subject to explicit
    thesis acceptance, Python 3.11 verification, actual API/approval/PDF boundaries,
    bounded state and later long-job/browser-regression validation. No automatic
    promotion follows.

Stop at this spike. Frontend capability does not establish real ML predictive value,
optimizer business validity or production readiness.
