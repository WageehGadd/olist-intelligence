# V3 Shared Contracts

**Status: FROZEN — Shared Contracts v1, approved 2026-11-14 by the team leader under the team's reported delegation of planning and contract decisions.** This is the canonical interface document for V3. The three members' plan agreement and delegation are team-leader-reported; this status does not claim individual explicit acknowledgements of the contract text. Teammate-specific dataset/environment checks remain required before their first implementation tasks, and no implementation may start before separate team-lead coordination. Master plan: [`MASTER_EXECUTION_PLAN_V3.md`](MASTER_EXECUTION_PLAN_V3.md). See [`V3-01_CONTRACT_FREEZE_AND_KICKOFF.md`](V3-01_CONTRACT_FREEZE_AND_KICKOFF.md).

## 1. Data sources, grains, and joins

The original nine Olist CSVs are obtained separately by each contributor. Never commit, redistribute, or copy them into a tracked fixture. Core project tables:

| Source table | Key/grain | V3 use | Notes |
|---|---|---|---|
| `olist_orders` | `order_id`, one row/order | status, purchase, promise, actual delivery | target and delivery metrics; actual outcome is label only |
| `olist_order_items` | (`order_id`,`order_item_id`), one row/item | item count, price/freight, product/seller IDs | aggregate to order before joins |
| `olist_order_payments` | (`order_id`,`payment_sequential`), one row/payment | optional SQL payment summary only | aggregate first; not purchase-time model input |
| `olist_customers` | `customer_id`, one order-linked customer row | customer and state counts | `customer_unique_id` is repeat-customer identity; never model ID |
| `olist_products` | `product_id` | category descriptions | 610 products lack category; label unknown |
| `olist_sellers` | `seller_id` | optional SQL description | multi-seller orders need aggregation |
| category translation | Portuguese category unique | readable category labels | unmatched category remains `unknown` |
| `olist_geolocation` | ZIP prefix is nonunique | excluded from MVP unless approved | never direct raw ZIP join; T-00 reports >1M rows |
| `olist_order_reviews` | source-row grain; `review_id` nonunique | out of mandatory V3 | do not use in delivery feature/model |

All order analytics must state grain/population. `customer_id` and `customer_unique_id` are not interchangeable. Do not join raw item and payment rows together and then sum amounts. Produce separate `order_id`-grain item and payment aggregates first. Any row count, missingness, uniqueness, and join mismatch is reported; no silent many-to-many join is accepted.

## 2. Shared time and quality rules

Parse Olist timestamps explicitly and document their timezone limitation; this dataset has no reliable timezone declaration. Keep timestamps as source-naive values unless a documented conversion rule is agreed. For the label, compare calendar dates only. Purchase-time predictors are limited to data plausibly available at order creation. T-00 flags the final cart, original promised date, geography/catalog snapshot availability as retrospective assumptions without version histories. The model is therefore a retrospective academic exercise, not proven online-feasible inference.

Required checks: expected columns; candidate-key uniqueness at declared grain; null/malformed date counts; invalid chronology; missing join coverage; item/payment aggregate conservation; allowed statuses; no direct identifiers in model matrix; outputs reproducible. Missing values are retained/flagged where meaningful; imputation is fitted on training data only for ML.

## 3. Clean analytical outputs

Generated output paths below are local and ignored by Git. UTF-8 CSV is sufficient for this small project; do not introduce Parquet unless a measured need and team decision justify it.

### `data/processed/orders_clean.csv` (Hasnaa)

One row/order. Required columns: `order_id` (string, join/group only), `customer_id` (string, join only), `order_status` (string), `purchase_ts` (parsed source timestamp), `estimated_delivery_ts` (nullable timestamp), `delivered_customer_ts` (nullable timestamp), `purchase_date` (ISO calendar date), `estimated_delivery_date` (nullable ISO date), `delivered_date` (nullable ISO date), `customer_state` (nullable string), `row_quality_flags` (optional delimited labels). Preserve exclusion-relevant rows and document any filter.

### `data/processed/order_items_clean.csv` (Hasnaa)

One row/order item. Required: `order_id`, `order_item_id`, `product_id`, `seller_id`, `price` (numeric), `freight_value` (numeric), `product_category_name_english` (string or `unknown`), optional dimensions with nulls preserved. Do not explode a row through geolocation joins.

### `data/processed/sql_kpis.csv` (Hamza)

Authoritative scalar KPI output. UTF-8 CSV, one row per (`kpi_name`,`period`), columns and logical types: `kpi_name` string; `period` string (`all` or ISO `YYYY-MM` purchase month); `value` decimal number or empty only for an undefined rate; `unit` string; `population` string; `numerator_count` nullable integer; `denominator_count` nullable integer; `definition_version` string (`v1`). Counts/sums leave numerator/denominator empty; rates populate both. Unique key is (`kpi_name`,`period`). Producer Hamza (V3-03), consumer Wageeh (V3-12/14) for API and Rana through Wageeh's API. Hasnaa/Wageeh may recalculate for reconciliation, but Hamza owns the authoritative dashboard value.

**Synthetic example rows only; these numbers are invented for schema illustration and are not Olist results:**

```csv
kpi_name,period,value,unit,population,numerator_count,denominator_count,definition_version
orders_total,all,120,orders,all source orders,,,v1
delay_rate_calendar,all,0.1,fraction,eligible delivered orders,2,20,v1
```

Empty `numerator_count`/`denominator_count` cells above are CSV nulls. Never copy these values into a report as observed results.

### `data/processed/sql_category_item_value.csv` (Hamza)

Authoritative category chart/KPI detail output. Exact header: `period,category_name,item_value_brl,definition_version`. One row per (`period`,`category_name`); types string (`all` or ISO purchase month), string (English translation or `unknown`), decimal, string constant `v1`. It uses delivered-order items and item-grain `price`, with no payment join. Producer Hamza; consumer Wageeh V3-12/14 and Rana via the API. Synthetic sample: `all,synthetic-example,125.50,v1` — invented values only. Hasnaa's category-item-count file is a separate descriptive distribution and does not duplicate this KPI value.

### Hasnaa chart-ready EDA outputs

These describe distributions, not shared KPI values. Producer Hasnaa (V3-05); consumer Rana (V3-11/14) through Wageeh's API. Files are local ignored generated outputs and are not committed.

#### `data/processed/eda_category_item_counts.csv`

Exact header: `category_name,item_count,population,definition_version`. One row/category among item rows whose order is delivered. Types: string (English or `unknown`), integer (count of item rows, not orders), string constant `delivered_order_items`, string constant `v1`. Sort by count descending then category name ascending. Synthetic row: `synthetic-example,3,delivered_order_items,v1`.

#### `data/processed/eda_item_price_distribution.csv`

Exact header: `bin_label,bin_lower_brl,bin_upper_brl,item_count,population,definition_version`. One row/fixed price bin over all item rows with finite nonnegative `price`, regardless of order status. Types: string; decimal; nullable decimal (empty only for open-ended final bin); integer; string constant `all_items_finite_nonnegative_price`; string constant `v1`. Bins are `[0,25)`, `[25,50)`, `[50,100)`, `[100,250)`, `[250,500)`, `[500,+∞)` BRL. Synthetic row: `0-25,0,25,3,all_items_finite_nonnegative_price,v1`.

These examples use invented counts and category labels. They are schema examples only and must never be described as verified dataset results.

### `data/processed/delivery_population.csv` (Wageeh)

One row/order, eligible labeled population only. Audit `order_id` may be included for grouping only and dropped from predictive features. Required columns: `purchase_ts`, `estimated_delivery_date`, `delivered_date`, `late` (integer 0/1), and `population_version`. `exclusion_reason` is not a column in this eligible-only file; V3-06 records excluded-row counts by reason in `docs/ml/target_definition.md`. For the delivery-delay KPI and ML target population, exclude an order if its estimated delivery calendar date is earlier than its purchase calendar date or its actual delivery calendar date is earlier than its purchase calendar date. Preserve delivered-order eligibility and valid required timestamps. This exclusion applies only to the delivery-delay analytical population, not automatically to unrelated commercial KPIs such as revenue proxies or customer counts. `late=1` only when actual delivery calendar date is strictly later than estimated delivery calendar date. The labeled output should not be exposed as a prediction input.

## 4. KPI definitions and authoritative owner

Freeze a `definition_version` and exact SQL/pandas expression in V3-01. No KPI may be relabeled without a documented contract change.

| Name | Exact definition and population | Sole authoritative owner | Consumer / independent check |
|---|---|---|---|
| `orders_total` | count distinct `order_id`; all source orders; period by purchase month | Hamza | Overview; others may reconcile |
| `customers_unique` | count distinct `customer_unique_id` among customers attached to selected orders | Hamza | Overview; others may reconcile |
| `delivered_orders` | count distinct orders with status `delivered`; period by purchase month | Hamza | Delivery; others may reconcile |
| `item_value_delivered` | sum item `price` for delivered-order items, item grain | Hamza | Overview/Sales; Hasnaa may verify |
| `freight_charged_delivered` | sum item `freight_value` for delivered-order items, item grain | Hamza | Sales; Hasnaa may verify |
| `delivered_item_value_plus_freight` | sum of the preceding two; item-value proxy, not company revenue/net revenue/profit | Hamza | Overview; others may verify |
| `category_item_value` | sum item `price` by translated category (`unknown` for missing), delivered-order population | Hamza | Sales; Hasnaa's category item-count chart is a different measure |
| `delay_rate_calendar` | numerator / denominator among delivered orders with valid required timestamps, estimated calendar date on or after purchase calendar date, and actual calendar date on or after purchase calendar date; numerator: actual calendar date strictly later than estimated calendar date | **Hamza** | Delivery; Wageeh independently verifies against V3-06 target labels |
| `eligible_late_orders` | numerator count for `delay_rate_calendar` | **Hamza** | Delivery; Wageeh independently verifies |

Only Hamza publishes these authoritative shared KPI values. Wageeh's V3-06 label builder is an independent implementation used for reconciliation, not the dashboard source of truth. Hasnaa may check a sample or totals but must not publish a competing `delay_rate_calendar` value. For monthly rows, `period` is purchase month and applies to both numerator and denominator.

Date filters are inclusive-start/exclusive-end ISO dates and apply consistently to numerator and denominator. Empty period returns zero-valued KPI only for additive counts/sums; rate is `null` with `no eligible orders`, not 0%. Price/freight totals are explicitly GMV-like item-value proxies and not accounting revenue.

## 5. Delivery prediction contract

Target: delivered orders with valid required timestamps, estimated delivery calendar date on or after purchase calendar date, and actual delivery calendar date on or after purchase calendar date. This exclusion is specific to the delivery-delay KPI and ML target population; unrelated commercial KPIs such as revenue proxies and customer counts retain their own documented populations. `late=1` iff normalized actual calendar date is strictly later than normalized estimated calendar date. Timezone and original-promise version are unknown caveats. T-00 observed 96,470 eligible and 6,534 late; the project's actual reproduced counts must be reported and reconciled, not hard-coded.

Prediction moment is order creation. The frozen minimal request schema is:

```json
{
  "purchase_timestamp": "2018-05-10T12:30:00",
  "estimated_delivery_date": "2018-06-01",
  "customer_state": "SP",
  "items": [
    {"price": 29.90, "freight_value": 10.20},
    {"price": 15.00, "freight_value": 5.00}
  ]
}
```

This is a **synthetic schema example only**; values are invented and are not an Olist order. Exact types/constraints: require full-string regex match `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$` before parsing `purchase_timestamp` as source-naive (no timezone suffix, offset, alternate separator, fractional seconds, or rollover); require `^\d{4}-\d{2}-\d{2}$` before parsing `estimated_delivery_date` as a real calendar date. `customer_state` must be an uppercase two-letter Brazilian UF from the enum (`AC, AL, AP, AM, BA, CE, DF, ES, GO, MA, MT, MS, MG, PA, PB, PE, PI, PR, RJ, RN, RS, RO, RR, SC, SP, SE, TO`); `items` is a nonempty array; each item has only `price` and `freight_value`, both finite nonnegative JSON numbers. Extra keys and unsupported input types/fields are rejected. `estimated_delivery_date` must be on or after the calendar date in `purchase_timestamp`; otherwise return HTTP 422 with code `INVALID_INPUT`. Malformed timestamps/dates, timezone-bearing timestamps, unknown UF values, empty items, booleans/strings/null/non-finite amounts, negative amounts, or extra keys are also rejected with HTTP 422. `quantity`, product/seller IDs, and identifiers are not accepted. Each array element represents exactly one item row. The derived model features, in fixed order, are `purchase_hour` (0–23 integer), `purchase_weekday` (Monday=0 through Sunday=6 integer), `purchase_month` (1–12 integer), `promised_lead_days` (calendar-day difference, nonnegative integer), `customer_state` (UF string), `item_price_total` (sum of item prices in BRL), `freight_total` (sum of item freight in BRL), and `item_count` (number of item rows, positive integer). The one pure transformation `src/ml/features.py::derive_model_features` receives these normalized raw values and is used by both historical training/evaluation row construction and inference; both paths use the same strict parsing, calendar rules, item aggregation, feature names/order, and units. Historical rows with malformed timestamps/dates or a promised date before the purchase calendar date are excluded with an explicit reason count; inference rejects the corresponding request. Fit learned imputers/encoders/scalers on training rows only; inference applies the saved fitted pipeline to the exact ordered feature output. Training and inference parity is verified on the same synthetic raw-input fixture. Do not maintain a second inference-only derivation.

**Team-lead-approved contract erratum (2026-11-15):** the original Shared Contracts v1 `customer_state` input enum accidentally omitted `PR` (Paraná), a valid Brazilian UF present in the original Olist data. Add `PR` to the frozen prediction-request validation enum and accept it in the shared V3-07 historical/inference feature derivation. This corrects the affected input-validation contract only. API paths, the exact eight feature definitions/order, delivery target and eligibility rules, output schemas, `population_version=v1`, and KPI `definition_version=v1` are unchanged. This erratum does not change V3 scope or authorize any other task.

Forbidden request fields: actual delivery, final status, review values/text, post-purchase payments/installments, future seller performance, customer/order identifiers, arbitrary server-time defaults. Missing model artifact returns an explicit unavailable response; it never generates a synthetic score. Pydantic rejects unknown keys. Request/response examples are fixtures, not evidence of performance.

Response types: `prediction` enum string `late|on_time`; `probability_late` float in [0,1]; `model_version` string; `notice` string. Example values must be marked synthetic in fixture documentation. Semantic/schema validation errors use HTTP 422 JSON with stable `code: "INVALID_INPUT"` and a user-safe `detail`; unavailable model uses 503 JSON `{"detail":"Model artifact is unavailable","code":"MODEL_UNAVAILABLE"}`. Do not put a made-up prediction in an unavailable response.

## 6. API and page contracts

| Route | Purpose | Response contract |
|---|---|---|
| `GET /health` | app status, not model readiness | `{"status":"ok"}` |
| `GET /` | Overview page | server-side Jinja2 `TemplateResponse`; initial KPI map, period, state/message |
| `GET /sales` | Sales/products page | server-side Jinja2 `TemplateResponse`; initial category/time series arrays, labels/units |
| `GET /delivery` | Delivery metrics page | server-side Jinja2 `TemplateResponse`; initial counts/rate and monthly chart data |
| `GET /predict` | prediction form | server-side Jinja2 `TemplateResponse`; field schema, notice, initial state |
| `GET /api/v1/analytics/summary?period=all` | authoritative scalar KPIs | summary schema below, sourced from Hamza `sql_kpis.csv` |
| `GET /api/v1/analytics/delivery-monthly?period=all` | monthly delay rate series | period, numerator, denominator and rate from same Hamza KPI rows; query accepts `all` or `YYYY-MM` |
| `GET /api/v1/analytics/category-item-value?period=all` | category value chart | series from Hamza `sql_category_item_value.csv` |
| `GET /api/v1/charts/category-item-counts` | category count chart | series from Hasnaa `eda_category_item_counts.csv` |
| `GET /api/v1/charts/item-price-distribution` | item price distribution | series from Hasnaa `eda_item_price_distribution.csv` |
| `POST /api/v1/predict` | prediction JSON | request/response schema in section 5 |

**Frozen page-loading strategy:** Wageeh owns all four HTML handlers (`GET /`, `/sales`, `/delivery`, `/predict`) and renders each server-side with Jinja2 `TemplateResponse`. On initial page load, handlers call Wageeh services that read the authoritative local producer CSVs and pass typed context for initial KPIs, chart series, page links, state, and message. Missing files produce an unavailable state, never fixture values. Rana owns templates, static assets, and browser interaction code. On Sales, changing the period selector fetches `GET /api/v1/analytics/category-item-value?period=<all|YYYY-MM>`; `all` returns the full series and `YYYY-MM` filters to that purchase month. The two all-time Hasnaa EDA charts remain in their initial server-rendered context. On Delivery, changing the period selector fetches `GET /api/v1/analytics/delivery-monthly?period=<all|YYYY-MM>`; `all` returns all monthly rows and `YYYY-MM` returns the matching purchase-month row. Initial summary and monthly series are server-rendered. On Prediction, submitting the form fetches JSON from `POST /api/v1/predict`. All other initial data is server-rendered; browser code does not fetch on page load, open CSV files, or calculate authoritative KPI values. Wageeh owns every route/service; Hamza and Hasnaa own their respective CSVs; Rana owns presentation/client interactions.

Wageeh owns these FastAPI paths and maps the exact CSV files to JSON. Rana consumes JSON responses only; browser templates do not open local CSV files. Hamza owns the KPI/category source files; Hasnaa owns the EDA chart files. A missing source file yields a documented empty/unavailable state, never synthetic values in the real-data route.

Summary response shape: `period` string; `definition_version` string; `kpis` object keyed by the KPI names above. Each value object has `value` number or null; `unit` string; `population` string; `numerator_count` integer or null; `denominator_count` integer or null; `definition_version` string. For `delay_rate_calendar`, counts are required. Category/chart response shape is `{ "definition_version": string, "series": [row objects] }` with row fields matching the source file types. Monthly delivery rows use `period` string `YYYY-MM`, `value` float, `numerator_count` integer, `denominator_count` integer, `unit` string `fraction`.

| Source file / producer | API route / Wageeh-owned mapping | Dashboard consumer |
|---|---|---|
| `sql_kpis.csv` / Hamza | `/api/v1/analytics/summary?period=all` | Overview, Delivery |
| `sql_kpis.csv` rows with `kpi_name=delay_rate_calendar` / Hamza | `/api/v1/analytics/delivery-monthly?period=all` | Delivery Analytics chart |
| `sql_category_item_value.csv` / Hamza | `/api/v1/analytics/category-item-value?period=all` | Sales and Products |
| `eda_category_item_counts.csv` / Hasnaa | `/api/v1/charts/category-item-counts` | Sales and Products |
| `eda_item_price_distribution.csv` / Hasnaa | `/api/v1/charts/item-price-distribution` | Sales and Products |
| JSON request / Rana form → Wageeh validation and inference | `POST /api/v1/predict` | Delivery Prediction |

The HTML page routes (`/`, `/sales`, `/delivery`, `/predict`) use the same Wageeh-owned service mapping as JSON routes. Rana's templates receive typed context from Wageeh; templates/browser code do not read CSV or SQLite directly. Common template context is `page_urls` (`overview:"/"`, `sales:"/sales"`, `delivery:"/delivery"`, `predict:"/predict"` in FastAPI), `asset_prefix`, `data_state` (`ready|unavailable`), and `message` (string or null). Overview additionally receives `period` and `kpis`; Sales receives `period`, `category_item_value`, `category_item_counts`, and `item_price_distribution` (each chart object has `definition_version` and `series`); Delivery receives `period`, `kpis`, and `delivery_monthly`; Prediction receives `request_schema`, `notice`, and nullable `result`/`error`. On an absent file an HTML route renders its page with `data_state="unavailable"` and a user-safe message; an API JSON route returns HTTP 503 with stable `DATA_UNAVAILABLE` code and user-safe detail. Neither may silently substitute a fixture. Query parameter `period` accepts `all` or `YYYY-MM`; unknown values return 422.

**Synthetic chart response example only — all values below are invented, not Olist results:**

```json
{
  "definition_version": "v1",
  "fixture_status": "SYNTHETIC ONLY — not a verified dataset result",
  "series": [
    {"category_name": "synthetic-example", "item_count": 3,
     "population": "delivered_order_items", "definition_version": "v1"}
  ]
}
```

In real responses the `fixture_status` marker is omitted and every row is mapped from the named producer file. The same `series` envelope is used for the item-price and category-value chart routes, with row fields exactly matching the corresponding file schema. For delivery-monthly, each series row has `period`, `value`, `numerator_count`, `denominator_count`, `unit`, `population`, and `definition_version`.

**Synthetic summary response example only — the counts and values are invented, not Olist results:**

```json
{
  "period": "all",
  "definition_version": "v1",
  "fixture_status": "SYNTHETIC ONLY — not a verified dataset result",
  "kpis": {
    "orders_total": {"value": 120, "unit": "orders", "population": "all source orders", "numerator_count": null, "denominator_count": null, "definition_version": "v1"},
    "delay_rate_calendar": {"value": 0.1, "unit": "fraction", "population": "eligible delivered orders", "numerator_count": 2, "denominator_count": 20, "definition_version": "v1"}
  }
}
```

The `fixture_status` field is required in mock files and omitted from real API responses. Rana's preview must visibly label mock mode. Wageeh maps Hamza's authoritative data and must never use fixture values as a fallback for a missing real file.

One FastAPI app serves both HTML and API, Jinja2 templates and static assets. Add no additional route without a page/use case. OpenAPI docs come from FastAPI. Pages: Overview (KPIs), Sales and Products (category/time series), Delivery Analytics (rates/counts), Delivery Prediction (input, result/probability, limitations). Each has navigation, loading/empty/error state. Plotly chart structures use arrays of equal length and explicit labels/units; chart no-data state must not imply zero observations.

**Synthetic fixture only — every value below is invented for UI development and is not a verified Olist result. Do not cite or display it as a dataset statistic.**

```json
{
  "fixture_status": "SYNTHETIC ONLY — not a verified dataset result",
  "overview": {"orders_total": 120, "customers_unique": 90,
    "delivered_item_value_plus_freight": 875.25, "period": "all"},
  "sales": {
    "category_item_value": {"series": [{"period": "all", "category_name": "synthetic-example", "item_value_brl": 125.5, "definition_version": "v1"}]},
    "category_item_counts": {"series": [{"category_name": "synthetic-example", "item_count": 3, "population": "delivered_order_items", "definition_version": "v1"}]},
    "item_price_distribution": {"series": [{"bin_label": "0-25", "bin_lower_brl": 0, "bin_upper_brl": 25, "item_count": 3, "population": "all_items_finite_nonnegative_price", "definition_version": "v1"}]}
  },
  "delivery": {"delivery_monthly": {"series": [{"period": "2099-01", "value": 0.1, "numerator_count": 2, "denominator_count": 20, "unit": "fraction", "population": "eligible delivered orders", "definition_version": "v1"}]}},
  "prediction": {"prediction": "late", "probability_late": 0.62,
    "model_version": "mock-only", "notice": "Synthetic UI fixture; not a measured result."}
}
```

All fixtures must carry the `fixture_status` marker above or equivalent filename/documentation metadata, and the UI must visibly label preview mode “Synthetic example data — not verified Olist results.” Remove that banner only when the same fields are populated from a successfully loaded authoritative local source. Never use a mock value in final findings, acceptance evidence, or claims about model performance.

## 7. Module ownership and repository layout

- Hamza owns `src/sql/`, `docs/sql_schema.md`, SQL data-loading/query tests.
- Hasnaa owns `src/data/`, `docs/eda/`, data-cleaning/EDA tests.
- Wageeh owns `src/ml/`, `src/app/`, model/API tests, integration wiring.
- Rana owns `templates/`, `static/`, UI fixtures/tests; backend routes and DB stay Wageeh/Hamza-owned.
- Shared contracts under `docs/planning/v3/`; only owner updates after team agreement. No concurrent edits to one contract section; use a PR and versioned change note.
- `data/raw/`, `data/processed/`, `data/local/`, `models/local/`, `.venv/`, caches, secrets and notebook checkpoints remain ignored. Only small synthetic fixtures with no real Olist rows may be tracked.

## 8. Environment and setup assumptions

Observed repository planning environment used Python 3.10.20. Proposed support baseline: Python 3.10; verify all dependency versions during V3-01 using installed environment. No dependency list or app entry point currently exists. Proposed entry point after implementation: `python -m uvicorn src.app.main:app --reload`; tests: `python -m pytest -q`; database builder and EDA/model commands must be documented by their owners. These commands are proposed and **not tested**. Do not install packages until V3 authorization and team-lead coordination. Obtain the nine CSVs separately after license/privacy review and verify filenames/columns with T-00 audit; GitHub clone intentionally lacks these ignored local files.

## 9. Handoffs, compatibility and blockers

Every handoff includes: branch/PR URL when available, output schema/version, generation command, input assumptions, test command/results, known limitations, and any local-only artifact location. Data/model/SQLite binaries are not transferred through Git; share reproducible code and synthetic examples. If a handoff is late, receiver keeps working against the frozen mock/synthetic fixture and records the blocking acceptance test. At final integration the producer and consumer jointly run schema/count/parity checks.

Contract change requires: proposed diff; reason; affected source/receiving owners; compatibility examples; test update; team-lead approval; instructor confirmation if learning outcomes/scope change. No private interpretation silently replaces the canonical contract.
