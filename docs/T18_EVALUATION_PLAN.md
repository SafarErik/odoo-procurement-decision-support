# Integrated evaluation and buyer usability — T18 planning

Status: **CONFIRMED PLAN — the five delivery slices have evidence consolidated in [#30's controlled assessment](T18_CONTROLLED_ASSESSMENT.md). Controlled functional/latency results pass; pending human/accessibility gates and substantial UX/UI reassessment remain explicit. Review/publication/issue closure are separate. The agreed evaluation contract is unchanged.**
Updated 2026-10-11 on `feature/T18-implementation`, initially clean at
`ed4be413b11dc469307fc1bb1ed4bd6c16c17b88`. The first executed results are recorded
separately in [#26's handoff](T18_26_HANDOFF.md); this plan retains the agreed contract.

## Outcome and development sequence

The technical procurement-to-approved-PDF chain works in the controlled T17
scope. T18 must determine how reliably it behaves, how long supported operations
take, and where an unfamiliar buyer needs help or risks making the wrong choice.
A passing demonstration does not establish that the product experience is finished.

Confirmed by the user in planning rounds 1–3:

1. T18 evaluates correctness, runtime and task-based usability, and fixes defects
   that block these checks. Substantial UX/UI improvement follows as a separate
   development increment before final acceptance and thesis closure.
2. Evaluate the implemented controlled hybrid: read-only Odoo quotations,
   explicit business terms and the separately synthetic saved Decision Tree.
   Observed-history/model promotion retains a separate data-readiness scope.
3. The target user understands procurement but has not learned this application.
   A prepared thesis presenter is not the sole usability benchmark.
4. Use the bounded workload/repetition/latency contract below. Targets are local
   PoC evaluation criteria, not production SLAs.
5. Agent/user walkthroughs proceed; sessions with 3–5 unfamiliar participants
   remain pending. Agent inspection does not establish first-time-user usability.
6. Add a small committed browser smoke suite through real Reflex/API/disposable
   PostgreSQL: create, compare, approve, reopen, view/download PDF and handle an
   unavailable backend. Manual visual/accessibility checks remain separate.
7. T18 may close its scoped technical evaluation and agent/user walkthrough report
   with unfamiliar-participant usability explicitly **NOT ASSESSED**. The later
   UX/UI increment must address findings and obtain further usability evidence
   before claiming the buyer experience is validated.
8. Deliver the browser suite locally first, with optional `pytest-playwright`
   test dependencies and Chromium. A hosted browser job is later work; the
   required Quality gate remains unchanged.

The existing T19 thesis-closure milestone is preserved. Its timing follows the
necessary development and reassessment; a follow-up UX increment is not silently
renumbered as T19. No new requirement namespace, accepted ADR or technology
baseline is introduced by this plan.

## Authoritative sources and publication baseline

- [Official task, 423.589/25/140](https://drive.google.com/file/d/1T4Fo_RsSFgs-zjV5NUPfF6_h7xOraog8/view).
- [Requirements](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig/edit): canonical FR/AC and NFR-V2-01–08.
- [Research questions](https://docs.google.com/document/d/1wpglDSL8rMUCFADUhslrgtIRRcWVAdujoEncrDY9WmY/edit): RQ-V2-01–07.
- [Roadmap](https://docs.google.com/document/d/1jlTCsRsO8C-MZ2xT-szbFJvExM2OVuphE5524NpIOr4/edit)
  and [ADRs](https://docs.google.com/document/d/1HzhcD03TAiIpJT4n9_tYLurYT3u68ziRND_E9RHRTW4/edit).
- [T17 full-flow evidence](T17_FULL_FLOW_HANDOFF.md),
  [approval](T17_HANDOFF.md), [PDF](T17_PDF_HANDOFF.md),
  [renderer/storage decision](T17_PDF_SPIKE.md).

[PR #24](https://github.com/SafarErik/odoo-procurement-decision-support/pull/24)
is merged at the SHA above. Exact post-merge
[Quality](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38150351508)
and [Container/API](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38150351451)
are SUCCESS. The user closed #19–#22; this session checked 34 child acceptance
items and added pinned handoffs, current CI and limitations to their issue bodies.

Source reconciliation: earlier repository handoffs and the 2026-10-09 project
alignment guide retain pre-implementation/publication wording. The 2026-10-11
Drive update predates the merge and this planning clarification. Those dated
states are not current blockers. Drive publication/scope correction requires its
own authorized update; no Drive write is performed in this planning session.

## Evidence to reuse and actual gaps

| Area | Existing evidence | T18 work remaining |
| --- | --- | --- |
| Allocation correctness | Small independent exhaustive oracle, constraints, alternatives, deterministic ties, exact money, infeasibility and solver failures in `tests/test_t13_planning.py` | Link coverage to AC/RQ; add only demonstrable missing cases |
| ML integrity | Synthetic split/cutoff/leakage, training/reload, metadata/checksum and unsupported observed-input checks in T14 tests; `T14_EVALUATION.json` | Interpret controlled metrics and limits; no new model or observed relabelling |
| API and persistence | T15 negative input/auth/integrity tests; real PostgreSQL creation, approval/PDF contention, rollback and immutability | Trace existing checks, run relevant residual integration gates, investigate actual failures |
| Complete flow | T17 actual hybrid/browser chain, five stresses/infeasible, two human outcomes, saved-only replay/PDF | Systematic repeatable assessment, not another identical demonstration |
| Runtime | Two descriptive full HTTP runs, 5.605/5.671 s, on one three-supplier fixture | Repetitions, supported size/epsilon matrix, raw observations and operation-specific summaries |
| Browser/user experience | Manual T16/T17 desktop/mobile and error acceptance; no committed browser E2E suite | Bounded automated smoke, keyboard/mobile walkthrough and explicit limits on novice-user evidence |
| Thesis conclusions | Dated component evidence exists | AC/NFR/RQ matrix and defensible answers linked to exact artifacts |

The dated T17 results are 579 fast passes and 57 service passes with two dedicated
T7-S live projection checks skipped. They are not rerun during planning. Determine
the relevance of those gates and retained prior history evidence before adding
Odoo setup requirements. The current hybrid model remains synthetic regardless
of the live quotation source.

## Confirmed measurement contract

Use integrated synthetic HTTP workloads with **3/5/10 suppliers** and **1/3
epsilon requests**, within the current 1–10 supplier/1–3 epsilon API limits and
the saved model's declared quantity/time/domain validity. Keep the fixed
three-supplier live Odoo validation separate; larger synthetic workloads must
not be presented as larger observed Odoo samples.

Use **two warm-up runs and 30 measured runs per workload**. Distinguish operation
measurements inside each run; use fresh case/decision keys where new writes are
required and exact keys where replay is being measured. Do not benchmark cached
idempotent creation as fresh inference/optimization.

| Operation | Accepted local target: observed p95 |
| --- | --- |
| Fresh creation and each stress calculation | At most 5 s |
| Stored GET, exact replay, approval and cached PDF | At most 1 s |
| First PDF rendering/storage | At most 3 s |

Measure request/response wall time from the local HTTP client, including relevant
API/database/solver work. Record offline preparation/training, startup, browser
task time and rendering/display separately; none disappears into an API number.
Retain raw timings, successes/failures, solver outcomes, environment/hardware,
SHA, dataset/model/input/policy hashes and workload sizes. Report median,
observed p95 and maximum with sample count and the stated percentile method.
Thirty observations are descriptive PoC evidence, not a production distribution
or confidence guarantee. Failures/timeouts remain visible; thresholds must not
be quietly relaxed after seeing results.

Use nearest-rank p95, the 29th sorted latency for 30 attempts with measured
elapsed times, and report failures separately. Include timed-out/failed attempt
latencies; a fast error is not a successful operation. If an attempt has no
reliable elapsed time, report the incomplete measurement rather than silently
dropping it. Percentiles must not conceal failed outcomes.
Report whether processes/fonts/models are warmed and distinguish first artifact
generation from process cold start. Sequential latency measurements are separate
from already implemented contending-transaction correctness checks.

Current safety timeouts are not evaluation targets: MILP has a shared 30 s budget;
Reflex POST/PDF clients allow 45 s and stored GET 7 s. At ten suppliers and three
distinct epsilons the feasible tie-breaking path can require up to 43 CBC solves
inside that shared budget. The accepted 5 s target is experimental, not yet
established at that size; retain partial/unproven solver outcomes in the report.

## Browser smoke implementation boundary

Current Python 3.11/Reflex tooling has neither Playwright nor Selenium installed;
there is no existing browser runner to reuse. Reflex's optional Selenium harness
would also add a dependency. The accepted local-first choice is optional
`pytest-playwright` tooling with Chromium and the existing `e2e` marker. Missing
prerequisites must fail a deliberately selected E2E gate, without making ordinary
fast-test collection depend on the optional browser packages.

Serve real FastAPI/Reflex with bounded readiness and teardown and an explicitly
identified disposable helper database. Use the controlled synthetic creation
path for repeatable smoke; keep the fixed live Odoo demonstration separate.
The frontend's prepared-file paths are currently fixed: preparation must not
silently overwrite owner evidence. Choose a test-only composition or verified
backup/restore rather than adding browser-selected artifacts.

For backend-unavailable behavior, stop only the harness-owned FastAPI process;
Reflex calls it from its Python server, so browser request interception would not
exercise that boundary. Verify the saved result and error/recovery state, not
just button presence. Compare actual downloaded PDF bytes/content identity to
the stored backend artifact. Retain useful failure traces/screenshots/service
logs with secrets excluded. Browser/runtime installation and Windows execution
remain unverified until implementation. Ubuntu/browser CI is explicitly deferred.

Primary tooling sources: [Playwright installation](https://playwright.dev/python/docs/intro),
[pytest plugin](https://playwright.dev/python/docs/test-runners),
[CI setup](https://playwright.dev/python/docs/ci). These establish tool capability,
not project execution evidence or a new deployment requirement.

## Buyer usability investigation

Current code and historical screenshots were inspected, not a new running
browser session. The following are evaluation candidates, not measured novice
failures or a formal accessibility finding.

| Priority and observation | Evidence | Buyer task and candidate later improvement |
| --- | --- | --- |
| High: reopening requires a retained UUID | `frontend/planning/inputs.py:263–280`; only `/planning` route in `frontend/app.py` | Return to a previous decision without developer assistance; evaluate recent cases or stored-case links as a later API-scoped capability |
| High: setup/help precedes results, including Odoo single-column layout | `frontend/planning/page.py:218–249,315–320`; historical Odoo input screenshot | Find created results and return from child to base; evaluate completed-setup collapse, focus/scroll and current-case navigation |
| High: plan comparison and finalization are spatially separated | `frontend/planning/results.py:265–299`; `decision.py:100–159` | Explain the exact cost/allocation/premium being approved; evaluate a nearby review summary and clearer final action |
| Medium: PDF has nested scrolling and no page navigation | `frontend/planning/pdf.py:60–74`; historical `.artifacts/t22/approved-workspace.jpg` | Locate allocation/reason/audit, zoom and download on desktop/mobile; evaluate page position/navigation |
| Medium: uncertain-save recovery exposes technical payload/key copying | `frontend/planning/page.py:53–88` | Understand an unknown save outcome and safely retry the same intent; improve explanation without hiding uncertainty or automatic resubmission |
| Medium: scenario context and minimum-plan comparison need comprehension evidence | `frontend/planning/scenarios.py:270–305` | Distinguish original/child, changed demand and approvable terms; evaluate navigation/context rather than invent broader scenario scope |
| Medium: full keyboard/accessibility evidence is incomplete | `docs/T16_HANDOFF.md`; T17 PDF mobile/Page Down acceptance | Keyboard-only tasks, focus/announcements, text zoom, contrast and touch controls; fix observed failures |
| Lower: developer/test guidance is prominent | `frontend/planning/page.py:13–49`; audit language in `decision.py` | Determine which guidance belongs beside the task versus help/Audit; refine hierarchy, terminology, spacing and consistent states |

The existing typography/palette/cards already have a coherent direction. A
modern experience requires clear next actions, understandable comparison,
recoverable workflows and accessible interaction; cosmetic restyling alone
cannot answer these observations. Fixed quotation discovery, synthetic history,
caller identity and one-product scope are declared boundaries, not defects to
silently remove.

Task set: create from the prepared comparison; explain cost/exposure/allocation;
make and interpret a disruption; understand infeasibility; return to the original
base; approve an alternative or make No-award on a separate base; reopen; recover
uncertain save/backend/PDF failure; locate and download approved content.
Record completion, assistance, critical mistakes, task time, comprehension and
comments separately from API runtime. External novice sessions remain pending;
agent/user walkthrough results must be labelled accordingly.

## Planning delivery areas — refined into published tickets

1. Evaluation contract and evidence matrix, reusing existing test/report seams.
2. Bounded repeated HTTP/runtime/stress evaluation and raw/summary reporting.
3. Browser smoke and task-based usability/recovery assessment; fix actual blockers
   in bounded slices and rerun affected checks.
4. Controlled-scope AC/NFR/RQ report, limitations and prioritized UX/UI follow-up.

Use the existing HTTP seam for application outcomes, genuine PostgreSQL for
transaction claims, and the real browser for user interactions. Add no mock-only
replacement for an integrated claim. Reset only a separately identified disposable
helper database; never Odoo or the user's application database. Odoo UI changes
remain manual user operations if a verified prerequisite later requires them.

## Completion and follow-up boundary

The scoped T18 output is a reproducible technical assessment: existing coverage
mapped to canonical identifiers; measured workloads and operation targets with
honest PASS/FAIL/limited/not-assessed results; local browser smoke; agent/user
task observations; blocker fixes and affected rechecks; and a prioritized UX/UI
follow-up. A report containing failed targets is not a passing evaluation gate:
resolve blockers or explicitly retain an accepted limited conclusion rather than
silently marking the corresponding AC/NFR satisfied.

External unfamiliar-participant sessions remain **NOT ASSESSED**. T18 closure
must not be labelled validated first-time-user usability, finished modern UI,
observed-model acceptance or complete thesis acceptance. The follow-up UX
increment can use these findings to improve return journeys, result/approval
clarity, forms/navigation, PDF interaction and visual consistency. Its precise
design and ticket priorities are later planning work; reassess affected tasks
after changes before final acceptance.

The user confirmed the shared understanding in round 4 (Q9). The subsequent
user-invoked to-spec stage published [specification #25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25)
with `ready-for-agent`; its [repository copy](T18_EVALUATION_SPEC.md) preserves
the contract and completion criteria. The subsequent user-invoked to-tickets
stage refined the four areas above into five bounded slices, separating automated
browser coverage from task assessment and proving measurement on a complete flow
before expanding it. The user approved the granularity and dependencies; the
[published breakdown](T18_TICKET_BREAKDOWN.md) links #26–#30. The user subsequently
authorized #26 implementation; its [local handoff](T18_26_HANDOFF.md) records a
complete three-supplier HTTP evaluation. After review/publication, #27 extends
the proven mechanism to the supported workload/stress matrix.

No new domain meaning was resolved: `GLOSSARY.md` already distinguishes planning
case/base/scenario/final decision/approved snapshot. Keep these meanings intact.
No new hard-to-reverse architecture decision warrants an ADR at this point.

Thesis mapping: chapter 7 owns measured evaluation and limitations; chapters 3/4/6
receive only changed behavior/architecture evidence; conclusions and further work
follow actual RQ results. Follow-up UX changes require affected reassessment before
the final thesis acceptance statement.
