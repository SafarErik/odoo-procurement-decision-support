# V2 Odoo business-input capability spike

Assessment: 2026-09-30. **GO WITH CONDITIONS** for a hybrid V2 input model using
validated contextual Odoo facts, explicit business terms and application policies.
This does not promote V2 to the thesis baseline. Native automatic sourcing of
demand, capacity, commitments and price tiers has not been established.

Branch: `spike/v2-odoo-input-capability`, based on local preservation commit
`0a316f8cbbe18ced5bce8eeffcd8af4eb1a5bc3a`. That commit captures the complete previous
optimization spike on `spike/v2-procurement-optimization`; its main base is
`71396e8924f6a1f60daf8b45f02861adf21a25e5`. Previous handoff statements about being
uncommitted describe that earlier handoff. This follow-up remains uncommitted.
No push, PR, merge, main change or Google Drive edit occurred.

## A. Proven facts and evidence boundaries

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| Accepted [T5 evidence](odoo-comparison-case-enablement.md), [T6 design](../T6_DESIGN.md) and [handoff](../T6_HANDOFF.md) | Installed comparison capability and controlled read-only group/line/supplier/product/price contracts at their recorded acceptance dates | Current unrestricted access, authoritative independent demand, supply commitments |
| Accepted [T8 handoff](../T8_HANDOFF.md) and historical adapter/calculator tests | Bounded Expected Arrival adherence, sample-size withholding and separate provenance | Supplier-promise performance or future delivery probabilities |
| Current full fast suite on Python 3.14.7 | 314 passed, 37 deselected; existing assembly, adapter, history and optimizer reference tests pass | Live Odoo behavior or Python 3.11 execution |
| Current unauthenticated configured `/web/login` read | Connection failed with `ConnectError` | Installed schema, live fixture values or current ACL state |
| Current Podman machine listing | Existing `podman-machine-default` is stopped; no services started | VM/container business-data state |
| Upstream Odoo 19.0 documentation and source review below | Standard model intent and explicit selection/pricing code paths | Equivalence to the stopped local image or locally reproduced tier behavior |

No live JSON-2 model introspection or new business fixture could be verified in this
run. Installed models/fields below are identified as **accepted repository evidence**,
not newly observed live facts. The [evidence record](v2-odoo-input-capability-evidence.json)
stores these distinctions, runtime search, solver checks and source URLs without
credentials. Upstream 19.0 branches were inspected on the assessment date, not
treated as the local build's immutable source revision.

## B. Existing project decisions preserved

- T5 found comparison grouping and company-scoped line reads, but stopped on
  supplier-promise/MOQ semantics. T6 subsequently accepted a hybrid input path;
  T12 now uses it. T5's earlier NO-GO is not a blanket rejection of later work.
- T6 accepts one common variant/UoM/currency/company/quantity, one line per RFQ,
  at least three RFQs, supported open states, zero discount and no taxes. Group
  identity is explicit; names, timestamps and coincident products are not joins.
- Hard MOQ and supplier-promised lead time remain attributed supplemental terms.
  Vendor-pricelist `min_qty` is not hard MOQ; `delay` and Expected Arrival are not
  supplier commitments.
- T8 uses the accepted bounded projection, not generic Inventory reads or direct
  database access. Attribution records origin/time without certifying truth.
- The [optimization spike](v2-procurement-optimization-feasibility.md) is unchanged:
  integer units, one offer per supplier, two-decimal positive prices, optional
  all-units tiers, four-decimal adherence, complete usable history for risk mode,
  deterministic ties, and no business actions. Its defaults are synthetic
  conveniences, not evidence of availability, deadline eligibility or no MOQ.

## C. New capability findings

### Authoritative procurement demand

Outcome **C: supplemental/application-level authoritative input required** for this
supported V2 scenario. Equal T6 RFQ quantities describe the compared offers; their
equality does not prove an independent buyer-approved total. Summing alternative
RFQ quantities would count competing requests repeatedly.

Standard [purchase templates](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/manage_deals/purchase_templates.html)
are reusable and permit changed quantities/multiple vendors.
[Blanket orders](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/manage_deals/blanket_orders.html)
describe recurring purchases from one vendor. Those purposes do not establish a
one-time multi-supplier demand authority. The reviewed
[agreement model](https://github.com/odoo/odoo/blob/19.0/addons/purchase_requisition/models/purchase_requisition.py)
contains product quantities and ordered totals, but no locally demonstrated rule
freezing one procurement requirement. Agreement quantities are candidates for a
future narrowly controlled workflow, not validated V2 demand now.

Use an explicit buyer-approved requirement quantity with product/UoM/company,
case reference and observation/approval time. Equal quote quantities may be checked
against that requirement as a documented workflow invariant; they must not replace
the approval. Approval does not require implementing a new Odoo object in this spike.

### Supplier capacity / available quantity

**Supplier capacity must be an explicit source-tracked supplemental business input
for the thesis PoC.** No semantically valid per-requirement maximum was established
in accepted runtime evidence or the reviewed standard procurement/supplier models.
This is a scoped negative finding, not proof that every installed extension lacks
such a capability.

RFQ quantity is a requested amount; received quantity is past execution; internal
stock is the buyer's inventory; `min_qty` is a pricing qualification; master data
and planning delay do not state deliverable supply. None is an acceptable capacity
fallback. Require a supplier offer/confirmation identifying product, quantity,
requirement, validity, delivery condition and unit. An explicit zero capacity or
unavailable response is valid; an absent response is not zero or unlimited capacity.

### Quantity pricing and exact restrictions

The standard vendor-pricelist [field definitions](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/products/pricelist.html)
describe price qualification by quantity. The reviewed
[supplier model](https://github.com/odoo/odoo/blob/19.0/addons/product/models/product_supplierinfo.py)
provides template/optional variant, vendor, company, currency, unit, validity dates,
discount and priority. A template-wide row can cover variants; that does not authorize
mixing variants in this single-product model.

In [seller selection](https://github.com/odoo/odoo/blob/19.0/addons/product/models/product_product.py),
company/active-vendor/product filtering precedes quantity, date, unit and partner
qualification. Default selection compares discounted prices, then priority and ID,
within the selected vendor; preparation order is not the final price rule. Therefore
sorting rows by descending threshold is insufficient. A more expensive high-threshold
row can lose to an eligible cheaper low-threshold row. This conclusion comes from
source inspection, not a live tier experiment.

The ordinary [purchase-line pricing path](https://github.com/odoo/odoo/blob/19.0/addons/purchase/models/purchase_order_line.py)
assigns a selected seller's unit price to the line, with unit/currency/tax handling
and separate discount. It does not sum marginal blocks. Manual overrides and
fallbacks can produce a different line price. The installed-module candidate
[agreement-linked pricing path](https://github.com/odoo/odoo/blob/19.0/addons/purchase_requisition/models/purchase.py)
can use agreement-line price rather than the ordinary vendor-price path. An actual
RFQ price therefore is not automatically an authoritative price curve.

Native tier extraction remains **NOT_YET_VALIDATED** locally. A defensible future
controlled subset must satisfy all of these conditions:

1. Fix one supplier, exact variant/template context, company, common currency/UoM,
   procurement/pricing date and validity interval. Reject unsupported conversions.
2. Use complete applicable rows, zero discount/taxes, explicit all-units terms and
   no unexplained competing rows or priority/variant ambiguity. A simple decreasing
   two-tier fixture is a candidate, not evidence already obtained.
3. Establish the effective price for every feasible integer allocation range using
   the verified installed selection behavior. Thresholds must be integral in the
   common unit; duplicate/overlapping rows need an explicit verified resolution.
   Do not round thresholds or prices into the spike's supported precision.
4. Cover quantities from the genuine MOQ/positive-use floor through capacity.
   A zero base threshold can normalize to one for indivisible positive orders;
   missing base coverage cannot be replaced by cost/master-price defaults.
5. Prove actual 499/500/600-unit RFQ behavior for the 1,000/920 example, including
   date/product/vendor exclusions and competing rows. Ordinary and agreement-linked
   paths must be distinguished; manual quote overrides cannot be ignored.
6. Obtain explicit commercial applicability before treating master pricing as a
   firm offer before RFQ creation. No order line is needed to read a price list,
   but pre-RFQ master prices are provisional and do not imply capacity or commitment.

This spike creates no fixture. A later required fixture must follow the human-admin
manual setup rule, remain isolated/removable, and be verified through authorized
read-only access after user confirmation. Runtime privileges must not be expanded.
Optional native quantity pricing is not yet a safe mandatory thesis dependency.

### Delivery, MOQ and historical compatibility

| Meaning | Accepted interpretation for V2 |
| --- | --- |
| Planning lead time | Scheduler/master-data interval after order confirmation; not a specific offer commitment |
| Expected Arrival | Operational scheduling reference, potentially calculated/edited; not a supplier promise |
| Supplier commitment | Explicit offer-specific promise applying to the supplied quantity range and conditions |
| Buyer-required date | Requirement constraint approved by the buyer; not a date inferred from supplier history |

No new evidence makes a standard planning field a hard commitment. Keep the buyer
date and supplier promise source-tracked. Derive eligibility in the future
application only from compatible times/time zones, an explicit reference event,
commercial validity and quantity coverage. A supplied Boolean needs the underlying
condition/reason; absence must not become `deadline_eligible=True`.

The MOQ conclusion is unchanged. Explicitly supplied no-MOQ means zero in the
experimental model; missing MOQ is not an implicit zero. Existing T6 requires a
positive hard MOQ, so a future V2 application contract would need a separate,
explicit optional/no-MOQ policy; existing T6 behavior is not changed here.

Recorded T8 `33.33%` normalizes exactly to `0.3333`; sample size remains three.
A current Python 3.14 contract smoke produced single-supplier proxy `0.6667` and
rejected risk mode with withheld sample size two as `history_unavailable`.
This reused a documented value, not a fresh Odoo read. T8 window, warnings,
supplier/company joins and provenance stay in the application envelope; the core
receives only usable normalized adherence and sample size. Risk mode requires every
usable candidate's history. Sparse history can support an explicitly requested
cost-only case, never an invented proxy or silent risk-mode fallback. Historical
schedule adherence is not a future delay probability or promise-date metric.

## D. Negative findings

| Finding | Consequence |
| --- | --- |
| No independent authoritative one-shot demand source demonstrated | Supply approved Q; do not use alternative totals or a template by default |
| No per-requirement capacity source demonstrated | Supply attributed available/committed quantities |
| No quantity-specific hard promise demonstrated | Supply delivery commitments and buyer condition |
| Tier source semantics are conditional, and local behavior untested | Keep native tiers optional/unvalidated |
| Observed quotation price was validated at the quoted quantity | Require evidence it remains applicable at allocated quantities, even with tiers disabled |
| Stopped Odoo VM | Current modules/schema/ACLs and new behavior remain unverified |
| No existing Python 3.11 located | Python 3.11 portability remains BLOCKED/UNVERIFIED |

## E. Input classification and conceptual assembly

Each row has exactly one primary category. No row is labeled unrestricted
`VALIDATED_ODOO_FACT`: all accepted project mappings have controlled-subset limits.
Confidence describes the conclusion within the evidence boundary, not fresh live
verification. “Core” means safe general requirement wording, not automatic baseline
acceptance. For source-tracked values, attribution includes field, supplier/case,
source type/reference and aware observation time; business validity/approval must
also be explicit. No generic lineage framework is proposed.

| Input / business meaning | Primary category | Odoo source or proposed origin | Provenance expectations | Restrictions | Confidence | Safe as CORE requirement? |
| --- | --- | --- | --- | --- | --- | --- |
| Requirement identity / selected comparison | VALIDATED_ONLY_IN_CONTROLLED_SUBSET | T6 `purchase.order.purchase_group_id`; application requirement reference | Selected source group, exact RFQ set, approved requirement reference/time | Technical group is not demand authority | High within T6 | Yes, with explicit case identity |
| Product / exact single variant | VALIDATED_ONLY_IN_CONTROLLED_SUBSET | T6 `purchase.order.line.product_id` | Line/product identity and observation | One exact variant; no aggregation | High within T6 | Yes |
| Authoritative required Q | SUPPLEMENTAL_SOURCE_TRACKED_INPUT | New buyer-approved requirement | Approval/reference, product/unit/company/time | Positive integer; equality alone is insufficient | High for need; native source unresolved | Yes if explicitly supplied |
| Quoted/requested line quantity | VALIDATED_ONLY_IN_CONTROLLED_SUBSET | T6 `purchase.order.line.product_qty` | Exact line/value/time | Common comparison quantity; neither supply capacity nor independent demand | High within T6 | Yes as quotation fact |
| Suppliers / stable commercial identity | VALIDATED_ONLY_IN_CONTROLLED_SUBSET | T6 order partner and `commercial_partner_id` | Stable mapping and offer join | One offer per supplier for the spike | High within T6 | Yes |
| Quotation unit price | VALIDATED_ONLY_IN_CONTROLLED_SUBSET | T6 `purchase.order.line.price_unit` | Quote/line/quantity/currency/unit/time | Zero taxes/discount; observed quote context only | High at quoted context | Yes, with scope stated |
| Price applicability across allocated quantities | SUPPLEMENTAL_SOURCE_TRACKED_INPUT | New explicit commercial offer condition | Quote reference, allowed range and validity | Cannot extrapolate from price at Q | High for need | Yes if documented |
| Native supplier pricing tiers | NOT_YET_VALIDATED | Candidate `product.supplierinfo`; no accepted V2 mapping | Complete row set, context/date, rule/build and observation | Conditions in C; all-units proof is not local extraction proof | Medium; local behavior blocked | Not mandatory yet |
| Supplier capacity / per-case maximum | SUPPLEMENTAL_SOURCE_TRACKED_INPUT | New supplier response/commitment | Supplier/case/product/unit/validity/reference/time | Never RFQ quantity, stock, history or `min_qty` | High for PoC fallback decision | Yes if supplied |
| Availability / usable supplier response | SUPPLEMENTAL_SOURCE_TRACKED_INPUT | Explicit supplier response | Same context as capacity | Missing is not false, true or unlimited | High for design | Yes if supplied |
| Buyer-required date/condition | SUPPLEMENTAL_SOURCE_TRACKED_INPUT | New approved buyer requirement | Deadline, time zone, reference event, approval/time | Separate from Expected Arrival | High for design | Yes if supplied |
| Promise / derived deadline eligibility | SUPPLEMENTAL_SOURCE_TRACKED_INPUT | Existing promised lead-time attribution, extended with quantity-specific offer condition | Condition, covered quantity range, basis and reference/time | No `delay`/`date_planned` fallback | High for PoC fallback decision | Yes if supplied |
| Hard MOQ or explicit absence | SUPPLEMENTAL_SOURCE_TRACKED_INPUT | Existing T6 attributed hard MOQ; explicit V2 optionality | Supplier offer/absence statement and observation | `min_qty` stays a tier threshold | High | Yes, optional when explicit |
| Historical schedule adherence | VALIDATED_ONLY_IN_CONTROLLED_SUBSET | T7-S projection and T8 calculator | Existing source, exact window/line selection, warnings/time | Percent divided by 100; not probability | High in accepted subset | Yes as bounded historical indicator |
| Historical sample size | VALIDATED_ONLY_IN_CONTROLLED_SUBSET | T8 eligible completed-line count | Same bounded history/window evidence | Below three withheld; not confidence certification | High in accepted subset | Yes with withholding |
| Common company/currency/UoM | VALIDATED_ONLY_IN_CONTROLLED_SUBSET | T6 order/line context | Exact identity and value agreement | No conversions in spike | High within T6 | Yes as context validation |
| Maximum supplier count | APPLICATION_POLICY | Explicit application/caller configuration | Policy identity/version/time outside core | Not an ERP fact | High | Yes |
| Concentration limit | APPLICATION_POLICY | Optional application/caller configuration | Policy attribution/version | Integer rounding matters | High | Yes, optional |
| Epsilon / allowed cost premium | APPLICATION_POLICY | Explicit alternative-generation policy | Policy/caps and request attribution | No hard-coded business plan labels | High | Yes, implementation-neutral |
| Forecast / inventory target / safety stock | NOT_REQUIRED_FOR_INITIAL_V2 | No source needed | Not applicable | Multi-period planning excluded | High | No initial requirement |

Conceptual architecture remains:

```text
bounded Odoo facts + explicitly sourced business terms + explicit policies
    -> future application assembler and separate provenance/context envelope
    -> ERP-neutral optimization input -> human-reviewed alternatives
```

**Assembly is conceptually feasible, conditionally; no production assembler was
built.** The table gives every requested field's origin. Use Odoo for the accepted
identities/quote facts/history; existing supplements for MOQ/promised lead time;
new supplements for approved Q, capacity/availability, commercial price coverage,
buyer deadline and quantity-specific promises; application policies for count,
concentration and epsilon. Native tiers can be omitted only when an explicitly
confirmed fixed unit price covers the feasible range. If tiers are required for
that offer, unresolved tier applicability must reject the case.

The current experimental core does not carry requirement/product/company identity:
those contextual validations belong in the application envelope. Map ERP-qualified
source IDs to stable opaque canonical supplier IDs; retain source joins/attribution
outside the optimizer. A technical group alone is not the approved requirement.
Do not pretend the existing WSM/T6 assembler already supplies the new V2 fields.

Proposed fail-closed validation sequence, **design only**:

1. Establish one explicit approved requirement and a bounded complete case; validate
   identities, joins, product/company/unit/currency and supported quote states.
2. Require approved integer Q, explicit per-supplier capacity/availability, applicable
   price and price range, delivery condition/promise, and MOQ or explicit absence.
3. Reject missing attribution, ambiguity, stale/invalid commercial terms, precision
   loss, unsupported conversions, duplicate supplier offers or inconsistent contexts.
   Do not fill missing fields from the experimental model's constructor defaults.
4. Validate promises against buyer deadline over the allowed quantity range. If only
   part of a quantity can meet the deadline, an explicit defensible on-time capacity
   bound is needed; no time-indexed or split-delivery model is silently introduced.
5. For risk mode, require all usable history joins/values/sample sizes and preserve
   withholding. For an explicit cost-only mode, preserve missing history honestly.
6. Create the neutral input and separate provenance/context snapshot. A complete
   valid input can still be mathematically infeasible: return that outcome, not a
   fabricated recommendation. Human final decision remains outside optimization.

## F. Application policies

Supplier count, concentration, epsilon choices, integer quantity suitability,
numeric precision, complete-history/withholding policy and permitted commercial
freshness are application/business policies. They must be documented and explicitly
selected; none is an Odoo fact. Buyer Q/date and supplier offer terms are business
inputs requiring evidence, not arbitrary tunable score weights. This spike adopts
no permanent ADR, new API policy or workflow implementation.

## G. Python 3.11 and solver portability

**BLOCKED / UNVERIFIED on Python 3.11.** No existing 3.11 runtime was located through
PATH, PythonCore registry entries or the targeted managed/standard installation
roots recorded in the evidence JSON. The located managed runtime and project venv
are Python **3.14.7**. This was a bounded discovery, not an exhaustive disk search.
No global installation, solver substitution or new virtual environment was made.

On the unchanged current spike code/dependency, PuLP **3.3.0** imports and bundled
CBC **2.10.3** is available. The current full fast suite passed **314 tests**, with
**37 deselected**, in 38.70 s, including all focused V2 cost/epsilon/infeasibility/
tier tests. The history compatibility smoke also passed. These are Python 3.14
results; they do not satisfy the missing Python 3.11 runtime gate. Cross-platform
differences could not be measured. Python 3.11 grammar parsing from the previous
boundary tests is not a runtime portability test.

## H. Remaining risks, checks and reproducibility

Local schema/build/ACL drift remains unverified while Odoo is stopped. Native demand,
capacity and promises were not demonstrated; no universal absence claim is made.
Price-list selection, agreement pricing and actual quote overrides need a bounded
installed-build fixture before native tiers are accepted. The accepted T6/history
fixtures do not prove one complete live multi-supplier V2 risk case. Existing
50-supplier tie-breaking latency and solver-build limitations also remain.

No Odoo fixture, write, UI automation, direct DB read, privilege change, API,
persistence/migration, frontend/Reflex change, LLM, LangGraph, other adapter, cloud
deployment or production V2 integration was implemented. Optional live tests were
not run against stopped services. Services were not started for this audit.

Ruff formatting/lint, dependency consistency, evidence-JSON parsing and Git
whitespace checks passed. Runtime, optimizer, tests and `pyproject.toml` match the
preservation commit exactly. Follow-up changes are limited to this report, its
evidence JSON, README and implementation log.

Core commands executed from repository root in PowerShell:

```powershell
git status --short
git branch --show-current
git log -1 --format='%H %s'
git add -- README.md docs/IMPLEMENTATION_LOG.md pyproject.toml docs/spikes/v2-procurement-optimization-feasibility.md docs/spikes/v2-procurement-optimization-results.json tests/test_v2_optimization.py tests/test_v2_optimization_architecture.py tools/v2_optimization
git commit -m 'spike: preserve V2 procurement optimization feasibility evidence'
git switch -c spike/v2-odoo-input-capability
git rev-parse HEAD
Get-Command py,python,python3,python3.11,podman -ErrorAction SilentlyContinue | Select-Object Name,Source
Get-Content .venv/pyvenv.cfg
Get-ChildItem -LiteralPath "$env:LOCALAPPDATA\Python" -Directory | Select-Object Name
& "$env:LOCALAPPDATA\Programs\Podman\podman.exe" machine list --format json
& "$env:LOCALAPPDATA\Programs\Podman\podman.exe" system connection list --format json
.\.venv\Scripts\python.exe -c "import platform,pulp,subprocess; print('Python',platform.python_version()); print('PuLP',pulp.__version__); print('CBC available',bool(pulp.PULP_CBC_CMD().available())); print(subprocess.run([pulp.PULP_CBC_CMD().path,'-stop'],capture_output=True,text=True,check=True).stdout.splitlines()[1:4])"
.\.venv\Scripts\pytest.exe -m 'not integration and not e2e' -q -p no:cacheprovider
$env:PATH = "$env:LOCALAPPDATA\Programs\Podman;$env:PATH"
$env:PODMAN_COMPOSE_PROVIDER = (Resolve-Path .\.venv\Scripts\podman-compose.exe).Path
podman compose --env-file .env -f infra/odoo/compose.yaml config --quiet
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

The PATH/provider assignments were confined to the checking process. Podman was
located outside PATH; its config check failed on the stopped VM's refused socket.
Git and external-process/network reads required sandbox escalation and succeeded;
no automatic approval rejection occurred. The normal browser Odoo session was
not operated. Documentation website fetch failures were handled by reading the
official 19.0 RST sources listed in the evidence record.

Exact configured-endpoint read (no credentials sent):

```powershell
$spikeReadOnlyProbe = @'
import json
import httpx
from backend.app.config import settings
result = {'configured': bool(settings.odoo_base_url), 'credentials_present': bool(settings.odoo_database and settings.odoo_api_key.get_secret_value())}
if settings.odoo_base_url:
    try:
        response = httpx.get(settings.odoo_base_url.rstrip('/') + '/web/login', timeout=5, follow_redirects=False, trust_env=False)
        result['login_http_status'] = response.status_code
    except httpx.HTTPError as error:
        result['connection_error_type'] = type(error).__name__
print(json.dumps(result))
'@
.\.venv\Scripts\python.exe -c $spikeReadOnlyProbe
```

Exact history compatibility smoke (recorded T8 value; synthetic commercial inputs):

```powershell
$spikeHistorySmoke = @'
import json
from decimal import Decimal
from tools.v2_optimization.models import ProcurementOptimizationInput, Supplier
from tools.v2_optimization.solver import optimize
recorded_t8_percentage = Decimal('33.33')
adherence = recorded_t8_percentage / Decimal('100')
supplier = Supplier('fixture-supplier', Decimal('10'), 100, historical_adherence=adherence, sample_size=3)
result = optimize(ProcurementOptimizationInput(100, (supplier,), 1), epsilon=Decimal('0'))
assert str(result.status) == 'optimal' and result.plan is not None
assert result.plan.risk_proxy == Decimal('0.6667')
withheld = Supplier('fixture-supplier', Decimal('10'), 100, sample_size=2)
missing = optimize(ProcurementOptimizationInput(100, (withheld,), 1), epsilon=Decimal('0'))
assert str(missing.status) == 'history_unavailable' and missing.plan is None
print(json.dumps({'evidence_kind': 'contract smoke using recorded T8 percentage, not live read', 'normalized_adherence': str(adherence), 'sample_size': supplier.sample_size, 'risk_proxy': str(result.plan.risk_proxy), 'withheld_status': str(missing.status)}))
'@
.\.venv\Scripts\python.exe -c $spikeHistorySmoke
```

Runtime discovery also checked `HKCU/HKLM\Software\Python\PythonCore` and
`HKLM\Software\WOW6432Node\Python\PythonCore`, plus the eight locations recorded
in the evidence JSON. If an existing Python 3.11 is later located, use it to create
an ignored project-local environment, install the same `pulp==3.3.0` plus project
test dependencies, and run `tests/test_v2_optimization.py`, the two boundary tests
and the fast suite. No installation or successful result is claimed for that step.

## I. Recommendation

**GO WITH CONDITIONS** for promoting a **hybrid, source-tracked input design toward**
thesis baseline review. The conditions are approved requirement authority, explicit
capacity and commercial coverage, quantity-specific delivery terms, documented
policies, bounded live/build validation for any native tiers, Python 3.11 execution,
and an acceptable explanation/latency scope. Do not make fully native Odoo sourcing
of these inputs a mandatory baseline claim. The present result is evidence and
advice; human acceptance and living-document edits remain separate.

## Thesis task-definition readiness (advisory only)

| Proposed capability | Readiness | Implementation-independent wording / boundary |
| --- | --- | --- |
| Odoo procurement-data integration | SAFE_TO_REQUIRE | Read validated procurement facts through a bounded, least-privilege, read-only integration |
| ERP-neutral business model | SAFE_TO_REQUIRE | Define canonical procurement requirements, supplier offers and allocation plans independent of ERP representations |
| Mathematical supplier selection/order allocation | SAFE_IF_GENERALIZED | Design and implement a mathematical optimization model for single-product supplier selection and order allocation; avoid a mandatory solver brand |
| Capacity constraints | SAFE_IF_GENERALIZED | Respect explicitly sourced supplier quantity limits; automatic Odoo capacity extraction is not required |
| Quantity constraints | SAFE_TO_REQUIRE | Fulfill an approved single-product quantity and enforce explicitly documented order conditions |
| Deadline constraints | SAFE_IF_GENERALIZED | Enforce buyer delivery conditions using explicitly sourced, applicable supplier commitments |
| Quantity pricing | SHOULD_NOT_BE_MANDATORY_YET | Optional all-units tier extension after applicability and installed behavior are validated |
| Historical supplier performance | SAFE_IF_GENERALIZED | Use a documented bounded historical indicator with sample-size/withholding rules; avoid a future-probability promise |
| Cost-risk scenario analysis | SAFE_IF_GENERALIZED | Compare cost-constrained alternatives using an explicitly defined historical-performance proxy |
| What-if analysis | SAFE_TO_REQUIRE | Re-evaluate changes in supplier availability, quantity limits, demand and offer price |
| Deterministic explanation | SAFE_IF_GENERALIZED | Explain allocations, hard exclusions, reached bounds, premiums and known infeasibility causes directly from model/input evidence; disclose causal limits |
| Web-based decision-support interface | SAFE_IF_GENERALIZED | Implement a web interface for configuring procurement cases and comparing alternatives; no mandatory Reflex framework |
| Human final decision | SAFE_TO_REQUIRE | Keep the final business choice with a human decision-maker |
| Plan-vs-actual controlling | SHOULD_NOT_BE_MANDATORY_YET | Requires separate execution linkage, measurements and feedback design |
| Split deliveries / time dimension | SHOULD_NOT_BE_MANDATORY_YET | Requires a different temporal model and commitment semantics |
| LangGraph / workflow orchestration | SHOULD_NOT_BE_MANDATORY_YET | No demonstrated need for this library or expanded workflow scope |

## Final questions

1. **Authoritative Odoo demand?** Not demonstrated for this supported multi-supplier
   scenario. Outcome C: require approved supplemental Q; templates/blanket quantities
   are unvalidated candidates, not automatic demand authority.
2. **Standard per-requirement supplier capacity?** No semantically valid source was
   established in the scoped evidence. Capacity must be source-tracked supplemental
   input for the PoC; this is not a universal absence proof.
3. **Safe vendor tiers?** Conditionally compatible with the all-units mathematics,
   but native use is NOT_YET_VALIDATED. Apply every restriction in C, including full
   context, effective selection, complete quantity coverage, pricing-path/override
   checks and installed-build behavior before acceptance.
4. **Hard deadline from validated Odoo facts?** Not demonstrated. Buyer conditions
   and quantity-specific supplier commitments remain supplemental; derive eligibility
   only from explicit compatible evidence.
5. **MOQ conclusion changed?** No. Tier qualification is not hard MOQ; retain
   attributed hard MOQ or an explicit approved absence.
6. **History suitable for V2 proxy?** Yes as bounded historical schedule adherence,
   normalized by 100 with sample-size withholding and separate provenance. It is
   not a future delay probability. The contract smoke passed; no new live read occurred.
7. **Complete input without fallback?** Conceptually yes using the hybrid origins
   in E, provided every mandatory term and applicability is explicitly evidenced.
   No production assembler or complete live V2 case was implemented/verified.
8. **Runs on Python 3.11?** BLOCKED/UNVERIFIED: runtime not located. Python 3.14.7,
   pinned PuLP 3.3.0/CBC 2.10.3 and 314 passing fast tests do not substitute for it.
9. **Safe thesis capabilities?** Bounded Odoo facts, neutral modeling, approved quantity
   constraints, what-if analysis and human choice; generalized optimization/capacity/
   deadline/history/proxy/explanation/web UI wording as in the readiness matrix.
   Native tiers, feedback controlling, temporal splitting and LangGraph are not
   mandatory-ready.
10. **Before V2 baseline acceptance?** Approve business authority and supplemental
    terms/policies, prove applicability, revalidate any new live/native mapping,
    execute Python 3.11, resolve scope/latency/explanation expectations, and obtain
    explicit human thesis-baseline approval. Stop at this spike; no automatic promotion.
