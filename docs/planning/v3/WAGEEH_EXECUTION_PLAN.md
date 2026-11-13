# Wageeh Execution Plan — Proposed V3

**Owner:** Wageeh Hussain Wageeh (Team Leader). **Status:** proposal only; no implementation is authorized. Wait until the team lead and instructor confirm the revised V3 scope and V3-01 is complete. Follow the [Master Plan](MASTER_EXECUTION_PLAN_V3.md), [Shared Contracts](SHARED_CONTRACTS.md), and [Transition Plan](V2_TO_V3_TRANSITION_PLAN.md). Your workstream is delivery ML, a small MLP comparison, FastAPI backend, and final integration. Do not take over SQL ownership (Hamza), cleaning/EDA (Hasnaa), or UI templates (Rana).

## Start conditions and independent work

The V3 scope approval is a hard start gate. After V3-01 freezes the contracts, you can begin V3-06 directly from `olist_orders_dataset.csv` and T-00 evidence; you do not wait for Hamza's database or Hasnaa's cleaned outputs. ML features use raw CSVs and T-00 leakage constraints. For FastAPI scaffolding, start from the frozen JSON contract and clearly synthetic fixtures; use them only in preview/test mode until source data arrives. Model-backed routes wait for V3-09. Final integration waits for all named artifacts.

## Task V3-01 — Scope, contracts, local setup and kickoff (4h)

Review instructor/team-lead approval status before any technical work. Confirm one version of each contract, the task owners, local raw-data availability, Python 3.10 baseline, existing dependencies, Git ignore behavior, and the weekly coordination time. Do not install dependencies or change repository settings as part of planning. Freeze the exact KPI, feature, request/response, error, output path and mock schemas in `SHARED_CONTRACTS.md`. Make unresolved decisions explicit. Send owners their specific contracts and record acknowledgements. **Deliverable:** accepted contract version and kickoff note. **Verification:** member plans' IDs, ownership, schemas and estimates agree. **DoD:** all four owners know their independent start and handoffs; scope and instructor gate are recorded accurately.

## Delivery prediction workstream (V3-06–09)

### V3-06 — Target and eligible population (5h)

Use orders at one row per `order_id`. Read the T-00 final audit and especially temporal quality and delivery target findings before coding. Preserve delivered-only eligibility, non-null purchase/estimated/actual dates, and valid chronology (actual delivery not before purchase). Compare normalized calendar dates; late means actual calendar date strictly after the estimated calendar date. Do not switch to timestamp lateness or a 30-day threshold. Write exclusion reason counts for non-delivered, missing dates, and chronology failures. T-00's 96,470/6,534 is a reconciliation point, not a value to hard-code; explain any changed counts. Proposed files: `src/ml/build_delivery_population.py`, `docs/ml/target_definition.md`, generated ignored `data/processed/delivery_population.csv`.

Example logic (illustrative only):

```python
actual_day = pd.to_datetime(orders["order_delivered_customer_date"]).dt.date
promise_day = pd.to_datetime(orders["order_estimated_delivery_date"]).dt.date
purchase = pd.to_datetime(orders["order_purchase_timestamp"])
eligible = delivered & actual_day.notna() & promise_day.notna() & (actual >= purchase)
late = (actual_day[eligible] > promise_day[eligible]).astype("int8")
```

Ensure pandas' null behavior cannot accidentally label missing values false. Add tests for same calendar day, next-day late, delivery before purchase, missing promise, non-delivered status, and stable row count. Handoff the population schema, actual counts, exclusion report, and label function to your own V3-07 and, as a descriptive cross-check, Hasnaa.

### V3-07 — Features and chronological split (6h)

Build at order grain with these fixed ordered features and types: `purchase_hour` (integer 0–23), `purchase_weekday` (integer Monday=0 through Sunday=6), `purchase_month` (integer 1–12), `promised_lead_days` (nonnegative calendar-day integer), `customer_state` (UF string), `item_price_total` (sum in BRL), `freight_total` (sum in BRL), and `item_count` (positive integer). Request rows contain only `price` and `freight_value`; each array element is exactly one item. Do not require product/seller IDs, quantity, distinct-item keys, or customer/order identifiers. T-00 says original cart and promise snapshot availability is unverified; disclose this retrospective assumption. Exclude distance/geolocation, payments/installments, actual outcome, review fields, final status, and future seller/customer aggregates. Keep order key only for grouping and drop before fitting. Implement one pure `src/ml/features.py::derive_model_features` transformation over normalized purchase timestamp, promised calendar date, state, and item rows; historical training/evaluation-row construction and API inference must call this same function. Apply the same strict parsing, calendar difference, sum, count, feature order, and units in both paths, then use the fitted preprocessing pipeline at inference.

Freeze date boundaries in a split manifest before comparing models. Use earlier purchases for train, a later period for validation, and the latest sufficiently mature interval for test; state label maturity and sparse tail exclusions. Whole orders cannot cross splits. Do not duplicate item rows into multiple labeled observations. Fit imputers/encoders/scalers on training only, using a shared sklearn pipeline at inference. Verify chronological order, no order overlap, feature availability, null handling, and reproducibility. Handoff feature names/dtypes, selection rationale, split boundaries/counts, class balance and pipeline interface to V3-08/09.

### V3-08 — Classical models (6h)

Start with `DummyClassifier` for context, then `LogisticRegression` as baseline and one `RandomForestClassifier`. Reuse the same train/validation/test indices. Use class weighting only if justified and fitted within training. Choose any threshold on validation only; report threshold-free AP and ROC-AUC plus precision/recall/F1/confusion matrix at the declared threshold. Include class prevalence and calibration limitations. Keep the final test untouched until model/feature/threshold decisions are frozen. Save estimator/preprocessor locally under ignored `models/local/`, and persist version, features, seed, split and metrics in metadata (not binary artifacts in Git).

### V3-09 — Small MLP and model choice (6h)

Use one small feed-forward network on exactly the same rows and fixed split. Scale numeric inputs and encode categoricals using train-only fit. Limit width/depth, use early stopping based on validation, one modest configuration, and no hyperparameter search. Confirm TensorFlow/Keras (or another justified lightweight framework) actually installs/runs within agreed environment before implementation; this plan does not install it. If dependency access is unavailable, record the blocker and ask for a coordinated solution; do not omit the mandatory experiment silently. Compare MLP with LR/RF using the same metrics/test interval; report results honestly even if DL is worse. Select final deployed inference model based on validation/selection policy, then evaluate the test once. Document the MLP's different preprocessing where relevant, resource limits, and no claim of general superiority. Handoff a loadable local inference function, feature schema and artifact checksum/version to V3-13.

## FastAPI backend (V3-12–13)

### V3-12 — App and analytics routes (8h)

Create one FastAPI app that serves HTML through Jinja2 and JSON. Suggested modules: `src/app/main.py`, `routes/pages.py`, `routes/analytics.py`, `schemas.py`, `services/analytics.py`. Implement `GET /health`, page routes `/`, `/sales`, `/delivery`, `/predict`, `/api/v1/analytics/summary?period=all`, `/api/v1/analytics/delivery-monthly?period=all`, `/api/v1/analytics/category-item-value?period=all`, `/api/v1/charts/category-item-counts`, and `/api/v1/charts/item-price-distribution` exactly as frozen in Shared Contracts. Each HTML route calls the same services and renders a server-side Jinja2 `TemplateResponse` with initial typed context; if authentic source files are absent, render the page in `data_state="unavailable"`. JSON analytics routes return `503 DATA_UNAVAILABLE`; neither path uses synthetic fallback data. Rana implements browser fetch only for Sales period changes (category-value JSON endpoint), Delivery period changes (monthly-delay JSON endpoint), and prediction form submission (`POST /api/v1/predict`). She owns templates/client interaction; you own page context, all handlers/services, and JSON endpoints. Use synthetic fixtures during development only. Map Hamza's `data/processed/sql_kpis.csv`/`data/processed/sql_category_item_value.csv` and Hasnaa's `data/processed/eda_category_item_counts.csv`/`data/processed/eda_item_price_distribution.csv` using exact schemas in Shared Contracts. Expose OpenAPI. Preserve Hamza as sole authoritative KPI owner. Do not add authentication, background jobs, separate services, or endpoints without a consuming page. Use `TestClient` for route schemas, source-file mapping, empty/error states, and template rendering. Send Rana exact paths/context/error behavior early.

Pass these exact common Jinja context keys on every page: `page_urls`, `asset_prefix`, `data_state` (`ready|unavailable`), and nullable `message`. Overview additionally gets `period,kpis`; Sales gets `period,category_item_value,category_item_counts,item_price_distribution`; Delivery gets `period,kpis,delivery_monthly`; Prediction gets `request_schema,notice,result,error`. Each chart object has `{definition_version,series}`. An HTML route renders HTTP 200 with `data_state="unavailable"` and user-safe message when source files are absent; corresponding JSON analytics route returns 503 `DATA_UNAVAILABLE`. Query `period` accepts `all` or a valid `YYYY-MM`; unknown/malformed values return 422. The category-value period route returns all rows for `all`, otherwise only matching purchase-month rows. The delivery-monthly period route returns all monthly rows for `all`, otherwise the matching month row. JSON response row fields and synthetic examples are exactly those in Shared Contracts.

### V3-13 — Prediction route (6h)

Implement `POST /api/v1/predict` with Pydantic validation for exactly `purchase_timestamp` (strict source-naive `YYYY-MM-DDTHH:MM:SS`), `estimated_delivery_date` (strict valid `YYYY-MM-DD`), `customer_state` (uppercase two-letter Brazilian UF enum in Shared Contracts), and nonempty `items` list where each element has exactly finite nonnegative numeric `price` and `freight_value`. Every array element is one item row. Require `estimated_delivery_date >= purchase_timestamp` calendar date. Reject malformed, timezone-bearing, unsupported, or extra inputs with HTTP 422 JSON containing `code: "INVALID_INPUT"`; do not request product/seller IDs, quantity, actual outcome, review, payment, or identifiers. This schema derives precisely the eight ordered V3-07 features using the same `src/ml/features.py::derive_model_features` function called during historical feature construction; add synthetic parity tests for the derived row and serialized API request. Use the exact train-fitted preprocessing/model pipeline. If the model file is missing, return documented 503 (`MODEL_UNAVAILABLE`) rather than a fabricated probability. Send Rana the exact request, response, and validation errors. Never stage model binaries.

## Integration and final delivery (V3-14–15)

### V3-14 — Integration (5h)

Integrate exact files: Hamza `data/processed/sql_kpis.csv` and `data/processed/sql_category_item_value.csv`; Hasnaa `data/processed/eda_category_item_counts.csv` and `data/processed/eda_item_price_distribution.csv`; Rana templates; your model. Map these to the exact API routes and JSON fields in Shared Contracts. Confirm version/meaning and producer acceptance; do not recalculate Hamza-owned KPIs in UI or change denominators. Replace synthetic fixtures only after contract tests pass; keep visible `DATA_UNAVAILABLE`/`MODEL_UNAVAILABLE` states until authentic local outputs exist. Test all page/API paths and the exact prediction request. If an input is delayed, continue with marked synthetic fixtures and list the blocked integration criterion.

### V3-15 — Verification, report and demonstration (4h)

Run the agreed lightweight test suite and a local end-to-end smoke; record exact commands and outputs. Verify a clone can follow setup instructions once data/dependencies are separately supplied, but do not claim a raw-data-free demo trains the model. Scan Git status and staged diff for CSV datasets, generated outputs, SQLite, model binaries, secrets, `.venv`, and caches. The final report should state population/label, chronology, features/availability caveats, model selection/evaluation, SQL/EDA outputs, app pages, errors/limitations, and each member's contributions. Rehearse: launch local app; visit Overview, Sales, Delivery, submit valid prediction input, demonstrate invalid/missing-model state; explain no live service commitment. Publish README/report changes only under a separately authorized task/PR.

## Dependency ledger and handoffs

| Need | Owner/source | Your receiving task | Type/start rule | Fallback and compatibility test |
|---|---|---|---|---|
| Approved scope and frozen contract | You/team lead + instructor | All tasks | hard blocker before V3-01/implementation | none; do not treat V2.2 approval as V3 scope approval |
| Raw order/item/customer inputs | individually acquired Olist CSVs | V3-06/07 | no external member dependency | T-00 audit fixtures for unit logic; reconcile real counts locally |
| SQL KPIs | Hamza V3-03 | V3-12/14 | integration-only; do not wait to scaffold | synthetic contract fixture; compare API values/denominators at integration |
| EDA chart data and findings | Hasnaa V3-05 | V3-14 | integration-only | mock chart fixture; validate shape, units, population |
| Page/context schemas | Rana V3-10/11 | V3-12/14 | integration-only | contract-defined Jinja mock; render every state |
| Model artifact and transform | your V3-09 | V3-13 | hard blocker for real inference | explicit 503 until available; API schema work can proceed |
| Route schemas/examples | you V3-01/12/13 | Rana V3-11/14 | contract first; API implementation later | frozen request/response fixture; contract test on replacement |

Every handoff contains schema/version, generating command, assumptions, test results, local artifact location (never binary committed), and limitations. If a dependency is late, notify the receiving owner and team lead promptly, continue only against approved mocks, and name the blocked acceptance criterion.

### Per-task prerequisite and blocker cards

| Task | Prerequisite owner and required input | Dependency type / independent start | Fallback; integration and verification | Handoff; blocker response |
|---|---|---|---|---|
| V3-01 | Instructor and team lead: explicit revised-scope approval; T-00 reports; owner availability | Hard governance gate; no implementation before it | No fallback; verify all four members accept same contract version | Send frozen contracts to each owner; if approval/availability unclear, stop and record open gate |
| V3-06 | Wageeh (self): raw orders CSV and T-00 label rules | Hard predecessor to own feature/model tasks; independent of Hamza/Hasnaa | Synthetic date fixture; integrate to V3-07 via target tests/counts | Send population schema/counts/exclusions to V3-07/Hasnaa; missing authentic CSV blocks true counts, not scope gate |
| V3-07 | V3-06; T-00 leakage matrix; raw order/item/customer fields | Hard predecessor; raw files independent of teammate output | Synthetic order records; verify order-disjoint chronology, denylist and train-only transforms | Send feature/split manifest to V3-08/09; questionable availability means drop feature or disclose assumption |
| V3-08 | V3-07 fixed features/split | Hard predecessor; independent of SQL/EDA | Synthetic fixture for tests; integrate same split with V3-09 and compare validation/test protocol | Send LR/RF pipeline and metrics to V3-09/13; invalid split blocks comparison pending repair |
| V3-09 | V3-07/08 inputs and an approved functioning DL framework | Hard predecessor for deployed prediction; framework is environment dependency | Synthetic unit fixture only; not a substitute for mandatory MLP; integrate via same-split metrics and parity test | Send selected inference/model metadata to V3-13; if framework unavailable, escalate and leave task blocked |
| V3-12 | V3-01 API/UI schemas; Hamza V3-03 output only for integration | Contract is hard; SQL is integration-only; API scaffolding starts from mocks | Frozen KPI JSON; integrate after V3-03/14 and compare names/units/denominators | Send routes, contexts and errors to Rana; late SQL stays mock-backed and flagged |
| V3-13 | V3-09 selected estimator/preprocessor and V3-01 request schema | Hard model dependency for real score; route schema can be scaffolded independently | Return explicit 503 until local model exists; verify API/offline fixture parity | Send JSON examples/errors to Rana; no model means prediction acceptance remains pending, never invent output |
| V3-14 | Hamza V3-03, Hasnaa V3-05, Rana V3-11, Wageeh V3-12/13 exact contracts | Hard release integration dependency; no stream waits to start | Fixtures permit continued component testing but do not satisfy real integration | Send run command/reconciliation results to all; mismatches go to source owner and block completion |
| V3-15 | V3-14 and all members' handoff/test notes | Hard finalization dependency | Mock-only demo may show unavailable state, not dataset/model results | Send report/setup/demo record to team; retain unresolved criteria as open and do not declare DoD |

## Troubleshooting and completion checklist

- Inflated revenue/order sums: inspect row grain; aggregate items and payments separately before joins.
- Model performance suspiciously high: check actual dates, status, review fields, identifiers, target-derived durations, future aggregates, and order leakage across splits.
- Test score used to select a model: invalidate the selection, use validation, and disclose if the test is no longer untouched.
- MLP does not converge: verify train-only scaling, label encoding, class imbalance, shapes, and early stopping; do not conduct unbounded tuning.
- API differs from notebook: use the same serialized preprocessing pipeline and run parity fixture.
- UI shows zero when data missing: return null/empty plus explicit message, not false zero.
- SQLite totals drift: validate child aggregate conservation and KPI population/filter before integration.

Before handoff: tests pass; output contracts match; no forbidden file tracked; PR explains how to reproduce; team member reviews; team lead coordinates merge; results and limitations are recorded. Task totals: 50 owner hours across V3-01, V3-06–09, V3-12–15. This is 12.5h/week over four weeks or 10h/week over five; neither capacity is verified. The five-week scenario is the provisional planning baseline only if you confirm the availability; otherwise extend the timeline before implementation. The Master Plan adds one calendar week with a 19-hour integration/debug contingency reserve. You own cross-stream wiring; each teammate remains owner of fixes in their component. No reserve effort shifts automatically to a junior member, and dates move if the relevant owner lacks capacity.
