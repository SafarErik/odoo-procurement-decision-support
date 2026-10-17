# T3 handoff — application and HTTP decision boundary

## 1. Objective and scope

T3 exposes the existing ERP-independent Decision Core through one narrow synchronous
application use case and one versioned FastAPI endpoint:

```http
POST /api/v1/procurement/decisions/evaluate
```

The endpoint evaluates canonical procurement data supplied by its caller. It does
not read from Odoo, PostgreSQL, files, environment-specific business data, or another
service. It provides explained decision support and performs no automatic supplier
selection, persistence, order creation, or write operation.

## 2. Request and response contract

The request contains exactly the three domain inputs supported by T2: one purchase
requirement, a collection of canonical supplier offers, and one named strategic
profile. Explicit Pydantic schemas own the HTTP representation.

HTTP 200 returns:

- the requirement identifier and requested quantity;
- the profile name and both criterion weights;
- the first-ranked eligible offer identity, or `null`;
- every eligible offer with original canonical values, deterministic rank, total
  score, and criterion-level contribution trace;
- every excluded offer with its identity, failed constraint, explanation, requested
  quantity, and MOQ.

Stable criterion identifiers are `unit_price` and `lead_time_days`. Stable direction
identifiers are `cost` and `benefit`; both active T3 criteria are cost criteria. The
stable hard-constraint identifier is `minimum_order_quantity`. The response contains
no Odoo field names, upstream payloads, stack traces, or credentials.

## 3. Decimal-string decision

All decision-relevant public numeric values are JSON strings, including quantities,
prices, lead times, weights, normalization values, contributions, and total scores.
The request schema accepts plain decimal notation and rejects exponent notation,
non-finite tokens, malformed values, and numeric JSON values. Mapping converts the
validated strings directly to `Decimal`; no value passes through binary
floating-point arithmetic. Response mapping uses fixed-point Decimal formatting for
deterministic JSON and does not round, truncate, repair, or default values.

## 4. Application-layer responsibility

`application/decisions.py` provides the synchronous
`evaluate_procurement_decision` use case. It receives the existing canonical T2
objects, invokes `decision_core.evaluate_decision`, and returns the complete
`DecisionResult`. It has no FastAPI, Pydantic, HTTP, Odoo, database, persistence, or
environment dependency and contains no WSM formula or duplicated domain rule.

## 5. API-layer responsibility

`backend/app/routes/decisions.py` receives the validated request, maps it to the
existing domain objects, invokes the application use case, maps the explained result
to response schemas, and translates known domain validation failures. All
normalization, constraint evaluation, scoring, and ranking remain in
`decision_core/`. The route has no Odoo or RFQ dependency.

## 6. Error mapping

Malformed JSON, missing fields, wrong structural types, non-string decision numbers,
and malformed decimal strings use FastAPI/Pydantic's normal HTTP 422 response.
Semantic failures raised as `DomainValidationError` use HTTP 422 with this stable
shape:

```json
{
  "detail": {
    "code": "invalid_decision_input",
    "message": "A safe, relevant domain validation message."
  }
}
```

Tests cover empty and duplicate offers, invalid quantities, price, lead time, MOQ,
weights, malformed decimals, malformed structure, and the absence of stack traces.

## 7. All-excluded behavior

All offers failing MOQ is a valid business outcome. The endpoint returns HTTP 200,
`recommended_offer: null`, an empty `ranked_offers` list, and every constraint
failure in `excluded_offers`. It never fabricates a recommendation.

## 8. OpenAPI evidence

The generated document registers `DecisionEvaluationRequest` and
`DecisionEvaluationResponse`, declares the operation as POST, documents HTTP 200 and
422, and embeds the T2 reference request. Field descriptions identify decimal-string
values. The operation description explains relative WSM scoring, eligible-only
scoring, the absence of persistence and Odoo writes, and the human decision-support
boundary. Contract tests assert these public OpenAPI facts.

## 9. Reference scenario result

For quantity `100`, Offer A and Offer B are eligible and Offer C is excluded because
its MOQ is `150`. Offer C does not affect normalization. With cost-focused weights:

| Rank | Offer | Price contribution | Lead-time contribution | Score |
| ---: | --- | ---: | ---: | ---: |
| 1 | Offer A | `1 x 0.7 = 0.7` | `0 x 0.3 = 0.0` | `0.7` |
| 2 | Offer B | `0 x 0.7 = 0.0` | `1 x 0.3 = 0.3` | `0.3` |

`recommended_offer` identifies Offer A. Balanced weights produce a deterministic tie
resolved as A then B by offer ID. Urgent weights rank Offer B first.

## 10. Tests and commands executed

Local verification used the existing Python 3.14.7 project environment; Python 3.11
remains the project and CI baseline.

| Check | Result |
| --- | --- |
| T2 prerequisite `tests/test_decision_core.py -v` | 39 passed |
| `ruff format --check .` | Passed; 45 files already formatted |
| `ruff check .` | Passed |
| `python -m compileall application backend frontend decision_core odoo_adapter` | Passed |
| `pytest -m "not integration and not e2e" -v` | 80 passed, 5 deselected |
| Focused served health and decision integration tests | 2 passed |
| `python -m pip check` | Passed |
| `git diff --check` | Passed |
| `podman compose ... config --quiet` | Passed |
| Static architecture boundary scans | Passed; no forbidden imports found |

Pytest also reported existing upstream TestClient deprecations and a local
`.pytest_cache` write warning; neither affected test results.

## 11. CI results

GitHub Actions had not yet run when this local handoff record was created. The final
external handoff and pull request must report `quality` and
`container-api-integration` separately and must not claim merge readiness while a
required check is pending or failing.

## 12. Architectural boundary confirmation

The implemented direction is strictly:

```text
backend -> application -> decision_core
```

The Decision Core was not modified. It still imports only Python standard-library
and internal Decision Core modules. The application use case is independent from
HTTP and Odoo. The new backend route does not import the Odoo adapter, the RFQ use
case, `RfqSummary`, persistence code, or frontend code. Existing health and RFQ
contract tests remain green.

## 13. Known limitations

The public decision endpoint has no authentication or authorization. It accepts only
the two T2 criteria and the MOQ constraint and relies on caller-supplied canonical
data. There is no rate-limit or new request-size middleware, persistence, history,
currency conversion, tax or total-cost model, quality/reliability criterion,
confidence score, frontend, automated supplier action, or cloud deployment.

The local Podman containers reached running/healthy state, but the known Windows
`win-sshproxy.exe` forwarding failure prevented localhost access to Odoo. The new
health and decision endpoints were served and verified locally; Odoo-dependent tests
and the RFQ HTTP smoke call were not rerun in this T3 session.

## 14. Deferred Odoo mapping

T3 introduces no Odoo-to-`SupplierOffer` mapping and does not connect the existing
RFQ list to evaluation. Purchase lines, products, matching, receipts, supplier
history, and all Odoo write behavior remain explicitly deferred pending separate
evidence and scope.

## 15. Branch and commit

- Branch: `codex/t3-decision-api`
- Base: fetched `origin/main` at `b39e2d4a9703d043c08615b0bf7004abd856007d`
- Final commit SHA: reported in the external handoff and pull request because a
  commit cannot contain its own final content-derived SHA.
- Merge state: not merged into `main`; intended to remain open for review.
