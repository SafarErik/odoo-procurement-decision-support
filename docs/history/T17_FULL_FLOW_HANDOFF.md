# Complete controlled procurement-to-approved-PDF acceptance — 2026-10-11

## Result and review boundary

[#22](https://github.com/SafarErik/odoo-procurement-decision-support/issues/22) is
implemented on `feature/T17-implementation`, starting clean at #21 commit `cf20ada`.
The defined **controlled local AC-V2-13 gate is met**: fresh read-only Odoo
acquisition, source-attributed terms, saved synthetic Decision Tree inference,
CBC alternatives, five stress types plus infeasibility, original-base approval,
stored reopening and matching PDF, with a separate No-award case.

User review, publication/exact-new-SHA CI, merge and issue closure remain pending.
Changes are unstaged/uncommitted. The user explicitly requires stopping before
Drive synchronization; no Drive documents were edited. No Odoo configuration,
business data or user application database was changed. T18 evaluation and thesis
acceptance are not claimed.

## Implemented change and reproduction

Existing product layers already compose the complete flow; no product/API/schema,
model/solver, frontend, dependency or infrastructure change was necessary.
`tools/t17_demo.py` provides repository-local HTTP `run` and `reopen` commands.
It reuses T15 offline preparation and API routes, requires explicit actor and
separate approval/No-award reasons, saves exact intent/key before each POST,
records measured time, and rejects changed replay/PDF content. It never trains,
selects an executable artifact, writes Odoo or retries automatically.

Two fast tests exercise real saved inference/CBC/rendering, all five scenario
types, an infeasible child, two original human outcomes, exact stored retrieval,
corrupted replay/PDF detection and uncertain-POST intent retention. Acquisition,
inference, solving, rendering and training sentinels guard the relevant stages.
Integration workflow path filters include the tool. README/index/runbook now
route to [the complete reproduction guide](T17_FULL_FLOW_DEMO.md).

## Executed verification

| Scope | Result |
| --- | --- |
| Final fast suite | **579 passed, 59 deselected**, 55.60 s; actual CBC/ML gates executed; one existing Starlette TestClient deprecation warning |
| Service suite | **57 passed, 2 skipped, 579 deselected**, 49.88 s; real PostgreSQL, runtime API/Odoo health and read-only T6/live contracts |
| Skipped service gate | Two dedicated T7-S projection checks; `RUN_T7S_LIVE_CONTRACTS` was not enabled |
| Required quality | Ruff format (196 files), lint, compileall including the demo, pip check, both quiet Compose configs and whitespace passed |
| Browser | Actual built-in browser -> Reflex 0.9.12 -> FastAPI -> Odoo 19 / saved ML / CBC -> PostgreSQL; manual milestone acceptance, not automated browser CI |
| PDF | Real browser download equals helper-database bytes/SHA-256; required saved content extracts; all five pages rendered with Poppler and inspected without clipping/overlap |
| New frontend export | Not repeated: #22 changes no frontend or dependency; #21's production export/browser evidence remains separate |
| New hosted CI | Unverified for these unpublished changes; no old SHA result is promoted |

The first focused demo selection passed 2 tests (6.45 s). An earlier full fast run
passed 579 tests (55.38 s) with a Windows pytest cache-permission warning; the final
selection followed the separate-rationale refinement and used a precreated cache,
leaving only the existing upstream warning. A manual evidence script initially
used an incorrect PDF ORM attribute; the corrected actual-field comparison passed.
That failed inspection is not PASS evidence.

### Complete browser observations

Fresh base `c0167ed5-2290-4602-aaf0-359c5a355923` independently reread group 2 and
saved USD 1,850 (A/B/C = 50/0/150) and USD 2,200 (100/100/0). Supplier/Audit views
show Odoo identities/prices, controlled capacities/MOQs/dates and separately
synthetic history. All five stress types were saved through the UI, followed by
demand 500 infeasibility. Each child retains the original base parent, even when
created from another child. Demand-total warnings and absent infeasible metrics
were visible; the scenario Plans view offered no finalization.

| Browser scenario | Case | Minimum |
| --- | --- | --- |
| Supplier C outage | `bd62ab21-8d22-4994-8508-ab4400b65d7b` | USD 2,200 |
| C capacity 100 | `c36ec5ac-4f78-4180-bb6f-dffa7b9badfd` | USD 2,200 |
| Demand 250 | `26e391f8-bc16-43ba-b8cc-b5b8c51ddb98` | USD 2,340 |
| C price 13 | `329fb467-a605-4a5c-97a6-da7563308377` | USD 2,200 |
| Demand 220; C capacity 150 / price 10 | `7c752874-47f0-4b07-bb0a-79a8f187afae` | USD 2,200 |
| Demand 500 | `1faaf1fd-ac02-4355-b1f7-ec334316f183` | Infeasible |

Separate browser base `e0f82aa5-e4b5-4b7e-9201-8b77dc64eab3` records reasoned
No-award at `2026-10-11T12:48:38.315154Z`, with no approved-PDF action. After
Odoo was stopped and the API restarted without a model, the original base received
explicit alternative approval at `2026-10-11T12:49:25.974465Z`. Its reason was
"Pay USD 350 more for the lower saved synthetic exposure."

A test-only renderer failure returned safe 503 with that approval still visible
and zero download links. Explicit retry after removing the marker generated the
same approved content. The native download saved an actual file; its 30,434 bytes
equal persisted bytes, SHA-256
`68e2851ccc2feb0467d82080bc472d37b9226cb8b3ea2f848c98c123f33cc5d3`.
Approved content hash:
`a349d05c35081f0f980f5815b9fc17180571a66f0f8a0268674997f4e1031fd4`.
Original snapshot hash:
`ce6dd117771443b55517f3f66ffec6d012549c7bf449592c403c50300a354fac`.

Stopping the API and requesting the PDF again retained approval, showed the safe
unavailable message and removed the stale download action. Restarting without a
model and with acquisition/inference/solver/**renderer** forbidden allowed browser
reopening and all five saved PDF pages. Exact API retries of both browser decisions
returned unchanged records/time; a child PDF request was denied. Original snapshots
remain identical. One browser download tool call took about 18 minutes to return;
this tool delay is not application processing time or benchmark evidence.

### Runtime and reproducible bounds

The final repeatable CLI run took **5.671 s**: fresh first creation 1.216 s, five
feasible scenario requests 0.469–0.526 s, demand-500 infeasible request 0.240 s,
second creation 0.757 s, finalizations 0.218/0.173 s. Total includes initial PDF
generation; excludes offline preparation, startup, browser actions and subsequent
replay verification. This single local run is descriptive, not a latency SLA.
An earlier complete run took 5.605 s; its exact stored replays were also verified.

Environment: Python 3.11.16; scikit-learn 1.8.0 / NumPy 2.3.5 / SciPy 1.16.3;
PuLP 3.3.0 / CBC 2.10.3; ReportLab 4.4.10. Controlled dataset: 240 generated
observations, 160 training / 80 held-out, 4,597 history lines and 1,200 outcome
lines, seed 17. Runtime buyer assessment uses three mapped synthetic profiles;
these are not receipt history measured from Odoo.

Model artifact SHA-256:
`d94a1c50576c45d0b852ed4fdcfefa590ed85cbd6201e491c830d21938cb818a`;
model ID `6a982edc068f77784ed3045812fafe72e52c81eb8d10c1fed9734b2f2e6c43d7`.
Policy: max suppliers 2, concentration 0.8, epsilon 0.2; price/delivery/score
quantity applicability 1–1000. Q=200, capacities 120/100/160 and MOQ 50/100/150
are supplemental controlled terms; quote quantity 100 is not approved demand.
Tree metadata, training/feature/label/mapping versions and exact solver contract
remain saved in every snapshot and the approved content.

## Evidence, cleanup and remaining work

Ignored `.artifacts/t22/` retains offline model/request, timed `odoo/t17-run-*.json`
and PDFs, all 16 browser/first-CLI snapshots and four decisions preserved before
disposable service resets (`manual-database.json`), database equality evidence,
before/after browser records, event traces, rendered pages, failure and successful
workspace screenshots. The final CLI has its own additional two bases/six children
and two decisions. Its report is `t17-run-1eeac37f-f8ea-4377-a767-e587a72fa0e6.json`.
Local evidence is not uploaded or a durable application deployment.

Acceptance reused the existing initially stopped Podman machine and existing Odoo
fixture containers. Only the separately created `procurement-decision-support-t22-acceptance`
helper database was migrated/reset. A task-created localhost-only SSH tunnel
forwarded host 55435 -> VM 55434 and host 8069 -> VM 8069 after the Windows proxy
failed. Acceptance processes/container/network/tunnel/tab are cleaned up, existing
Odoo containers stopped again, and the machine restored to stopped state. The
temporarily replaced default frontend preview is restored from its byte backup.

No new runtime blocker remains for the defined controlled milestone. User review
is next; **stop before Drive updates**, as requested. When approved separately,
consolidate thesis-relevant T17 results with evidence links and clear local/hosted
status, rather than migrating code or command diaries. Commit/push/merge and
#19–#22 issue closure remain under user control. After accepted T17, plan T18's
integrated negative/regression/performance/stress evaluation separately.

## Thesis-useful T17 result

| Problem -> decision | Implemented behavior and evidence | Limitation / chapter relevance |
| --- | --- | --- |
| Machine plans lacked a recorded human outcome -> base-only immutable finalization | #20 explicit plan/reasoned No-award, exact retry, audit/content identity and PostgreSQL concurrency; retained #20 evidence plus #22 hybrid browser/replay | Technical caller attribution, synthetic/historical validity; chapters 3/4/6/7 |
| Approved content lacked a usable document -> render/store backend PDF from that content | #21 renderer/artifact/reference, view/download, immutable storage and retry; retained layout/Unicode/concurrency evidence plus #22 actual matching hybrid PDF | Not a legal external PO; font/2 MiB bounds; chapters 4/6/7 |
| Independently working slices lacked one reproducible chain -> controlled full-flow acceptance | #22 real read-only Odoo through saved synthetic ML/CBC/stress/human decision/PDF, measured run and model-unavailable reopening | Controlled AC-V2-13 only; T18 evaluation and observed-model promotion remain open; chapters 3/4/5/6/7 |

This is the material to summarize later in Hungarian Drive status, roadmap,
requirements evidence and affected architecture records after the user's green light.
