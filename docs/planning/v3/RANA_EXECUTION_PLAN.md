# Rana Execution Plan — Proposed V3

**Owner:** Rana Ibrahim Abdel Fattah Mohammad. **Workstream:** dashboard UI and data visualization. **Status:** proposal only; begin only after team-lead/instructor V3 scope confirmation and V3-01 contract kickoff.** You build Jinja2/HTML/Bootstrap/Plotly templates and static assets. You do not own SQL, FastAPI routes, or ML models. Read [`MASTER_EXECUTION_PLAN_V3.md`](MASTER_EXECUTION_PLAN_V3.md) and [`SHARED_CONTRACTS.md`](SHARED_CONTRACTS.md).

## What you deliver

- V3-10: template shell, navigation, reusable components and mock fixtures (8h).
- V3-11: four dashboard pages, selected charts and prediction form (8h).

Total 16 hours, around 4 hours/week in the four-week planning scenario, including local tests and handoffs. This estimate may change after team availability is confirmed.

The Master Plan reserves one calendar week and 19 team hours (about 20% of base task effort) for integration/debugging. This is schedule buffer, not extra Rana task effort or an automatic assignment. You fix UI-owned defects only within availability agreed with the team lead; otherwise the team extends the calendar. Your five-week task average is 3.2h/week, distinct from the assumed 4–6h/week availability.

## Independent start: mock-first UI

After contracts freeze, start without waiting for Hamza, Hasnaa, or Wageeh's server. Use JSON examples from Shared Contracts and keep the preview visibly labeled **Synthetic example data — not verified Olist results**. All fixture files must also carry `fixture_status: "SYNTHETIC ONLY — not a verified dataset result"`. Never use verified dataset figures as mock fixture values. During integration, Wageeh replaces the fixture provider with actual route responses; missing real data remains an unavailable state, never a fixture fallback.

## V3-10 — Shell, components and fixtures (8h)

### Suggested structure

```text
templates/
  base.html
  partials/_nav.html
  partials/_kpi_card.html
  partials/_empty_state.html
  pages/overview.html
  pages/sales.html
  pages/delivery.html
  pages/predict.html
static/css/site.css
static/js/charts.js
tests/ui/fixtures/*.json
```

Wageeh owns the FastAPI application and template rendering context. Agree the context keys with him; do not create backend routes or database access. Bootstrap should provide a simple responsive grid, readable contrast and navigation. Keep custom CSS small. Chart.js is not part of the stack: use Plotly only where a chart clarifies a comparison; otherwise use semantic HTML tables/cards.

### Step-by-step

1. Create base layout with page title, navigation links, responsive container, footer/academic disclaimer.
2. Add reusable KPI cards with label, formatted value, unit and optional denominator/context.
3. Add consistent empty/error states that distinguish missing data from zero observations.
4. Prepare `tests/ui/fixtures/synthetic_dashboard.json` with the explicit synthetic marker and invented values only.
5. Use a proposed helper `scripts/ui/render_mock_preview.py` (planned deliverable, **not implemented in this repository**) to load templates with Jinja2 `Environment`/`FileSystemLoader` and `autoescape`, render fixture context, and write `index.html`, `sales.html`, `delivery.html`, and `predict.html` under ignored `data/processed/ui_preview/`. The helper copies `static/` to `data/processed/ui_preview/static/`, supplies relative `asset_prefix="static"` and `page_urls={"overview":"index.html","sales":"sales.html","delivery":"delivery.html","predict":"predict.html"}`; every preview navigation link must use those relative filenames (no leading `/`). These names make `/` resolve to `index.html` and page links work when served from the output root by Python's built-in static HTTP server. It visibly injects the synthetic-data banner.
6. Once Jinja2 is available in the approved environment, run `python scripts/ui/render_mock_preview.py`, then in another terminal run `python -m http.server 8000 --directory data/processed/ui_preview`; open `http://localhost:8000/`. This uses Python's built-in HTTP server and does not require Wageeh's FastAPI app. The commands and helper are proposed and untested until V3-10 implementation.
7. For FastAPI contexts later, Wageeh passes `asset_prefix="/static"` and actual route URLs; templates must use those injected values rather than FastAPI-only `url_for` calls so the static preview remains renderable.
8. Send Wageeh route names, required context, fixture files and preview instructions.

Acceptance: four navigation destinations, reusable layout, accessible labels, synthetic fixtures, explicit empty/error/loading behavior, no React/Streamlit or backend work, and preview can run before real API is ready.

## V3-11 — Pages and prediction flow (8h)

### Page specifications

1. **Overview:** `orders_total`, `customers_unique`, `delivered_item_value_plus_freight` as clearly named item-value proxy, plus one selected KPI. Include period and denominator context.
2. **Sales and Products:** category item-value proxy from Hamza's KPI route, plus Hasnaa's category item-count and item-price-distribution charts. Categories use English translation or `unknown`. Do not say revenue/profit.
3. **Delivery Analytics:** Hamza-owned delivered/eligible counts and calendar delay rate, with numerator and denominator. Consume the Hamza KPI API values; do not calculate a competing rate in the browser.
4. **Delivery Prediction:** form exactly matching the shared schema keys `purchase_timestamp`, `estimated_delivery_date`, `customer_state`, and `items`. `customer_state` is a dropdown using the frozen two-letter UF enum. `items` is nonempty; each item object has only numeric `price` and `freight_value`. One array entry is one item row. Do not request product/seller IDs, quantity, actual delivery, payments or review fields. Display a result only when API responds; show validation or unavailable errors clearly.

### Plotly and UI behavior

Use Plotly charts with equal-length arrays, explicit axis titles/units, and informative hover labels. Hide or replace charts when the response is empty; do not draw zero bars when no eligible data exists. Avoid confusing category truncation; label top-N if used. Keep filters limited to agreed date range and category unless a real route contract supports them. Do not calculate authoritative KPIs in browser JavaScript; backend/SQL output owns values.

Exact page-to-API handoff (Wageeh owns every endpoint):

| Page | Endpoint(s) | Producer source |
|---|---|---|
| Overview | SSR context from `GET /`; source JSON shape is summary `{period,definition_version,kpis}` | Hamza `data/processed/sql_kpis.csv` |
| Sales and Products | SSR initial context; period selector fetches `GET /api/v1/analytics/category-item-value?period=all|YYYY-MM`; initial EDA arrays are SSR | Hamza category CSV; Hasnaa's two EDA CSVs |
| Delivery Analytics | SSR initial context; period selector fetches `GET /api/v1/analytics/delivery-monthly?period=all|YYYY-MM` | Hamza `sql_kpis.csv`, sole authoritative KPI source |
| Delivery Prediction | SSR form from `GET /predict`; form submit fetches JSON from `POST /api/v1/predict` | Wageeh model/inference; request fields defined below |

On each initial page request, Wageeh's FastAPI route renders a Jinja2 response and passes typed initial context; Rana does not fetch JSON on page load. Rana implements these browser fetch interactions only: Sales period selector → `GET /api/v1/analytics/category-item-value?period=all|YYYY-MM`; Delivery period selector → `GET /api/v1/analytics/delivery-monthly?period=all|YYYY-MM`; Prediction form submit → JSON `POST /api/v1/predict`. The Sales EDA charts and initial KPIs/chart series arrive in server-rendered context. Browser code must not open local CSV files or recalculate shared KPI values. Wageeh owns route/service code.

Use the exact context keys Wageeh passes: all pages receive `page_urls` (`overview:"/"`, `sales:"/sales"`, `delivery:"/delivery"`, `predict:"/predict"` in FastAPI), `asset_prefix`, `data_state` (`ready|unavailable`), and nullable `message`; Overview also receives `period,kpis`; Sales receives `period,category_item_value,category_item_counts,item_price_distribution`; Delivery receives `period,kpis,delivery_monthly`; Prediction receives `request_schema,notice,result,error`. Each chart object is `{definition_version,series}` and series fields are as specified immediately below. HTML pages render with an unavailable state/message when a source file is missing; do not replace unavailable values with fixtures outside explicitly labeled preview mode.

Frozen prediction form fields (no extra inputs): `purchase_timestamp` strict source-naive `YYYY-MM-DDTHH:MM:SS`; `estimated_delivery_date` strict real `YYYY-MM-DD`, on or after the purchase calendar date; `customer_state` uppercase Brazilian UF; and nonempty `items`, each with only finite nonnegative numeric `price` and `freight_value` (one entry per item row). Reject malformed values, timezone/offset timestamps, unknown fields, or unsupported types; show HTTP 422 `INVALID_INPUT` details. A valid response has `prediction` (`late|on_time`), `probability_late` (0–1), `model_version`, and `notice`; 503 `MODEL_UNAVAILABLE` is an unavailable state, not a score. This example is synthetic only: `{"purchase_timestamp":"2018-05-10T12:30:00","estimated_delivery_date":"2018-06-01","customer_state":"SP","items":[{"price":29.90,"freight_value":10.20}]}`. Shared Contracts remains canonical for the full enum and field-level contract.

Required chart response fields for template bindings: category-value rows are `{period: string, category_name: string, item_value_brl: number, definition_version: string}`; category-count rows are `{category_name: string, item_count: integer, population: "delivered_order_items", definition_version: string}`; item-price rows are `{bin_label: string, bin_lower_brl: number, bin_upper_brl: number|null, item_count: integer, population: "all_items_finite_nonnegative_price", definition_version: string}`. These are wrapped as `{definition_version: string, series: [...]}`. Delivery rows are `{period: "YYYY-MM", value: number, numerator_count: integer, denominator_count: integer, unit: "fraction", population: string, definition_version: string}`. Summary is `{period, definition_version, kpis}`, where each KPI has `value`, `unit`, `population`, `numerator_count`, `denominator_count`, and `definition_version`. Shared Contracts remains canonical for full payload examples. Any mock values are invented synthetic fixtures, never verified dataset results.

### Acceptance and output

Paths: `templates/pages/*.html`, `static/css/site.css`, `static/js/*.js`, `tests/ui/fixtures/synthetic_dashboard.json`, and proposed helper `scripts/ui/render_mock_preview.py` (planned, not yet present). Pages render with mock fixtures; preview helper writes ignored static HTML; form serializes exactly `POST /api/v1/predict`; chart fields match their named routes; synthetic banner appears; error/empty states are visible. Provide page-to-contract map and test/demo steps to Wageeh. Do not mark integration done until API responses and source files have been verified.

## Contracts and dependency ledger

| Input | Source/owner | Dependency type and when needed | Fallback | Handoff/verification |
|---|---|---|---|---|
| Scope gate and UI/API contracts | Team lead/instructor; V3-01 Wageeh | Hard blocker before implementation | None | Agree and freeze page names, keys, field constraints, errors |
| Jinja2 render context | Wageeh V3-12 | Integration-only; not needed for mock build | Frozen template fixtures | Same keys/types; TestClient renders every page |
| Prediction request/response | Wageeh V3-01/13 | Exact form can start from frozen schema; live integration later | Marked synthetic JSON fixture | Pydantic parity for `/api/v1/predict`; four top-level inputs, item has only price/freight |
| SQL KPIs and category value | Hamza V3-03; Wageeh V3-12 | Integration-only at V3-14; Hamza is authoritative owner | Marked synthetic KPI fixture | Summary/category API fields, units, denominator and version match contract |
| EDA chart arrays | Hasnaa V3-05; Wageeh V3-12 | Integration-only at V3-14 | Marked synthetic chart fixtures | Exact CSV-to-API-series-to-template field parity |
| Model artifact/result | Wageeh V3-09/13 | No dependency for UI shell; live score requires model service | Mock-only fixture clearly labeled | Do not present mock as measured performance |

Each handoff includes template routes, context schema, example fixture, test command/results, accessibility/empty/error behavior, and unresolved assumptions. If a teammate's output is delayed, continue on mock data and tell the receiving owner/team lead. At V3-14, remove mock values from demo context or mark any remaining simulated state prominently.

## Independent preview and test checklist

The independent preview has two explicitly **proposed, not implemented** pieces: `scripts/ui/render_mock_preview.py` and its generated output. No helper exists in the current branch. Once V3-10 is authorized and Jinja2 is available, the helper will call standard Jinja2 `Environment(loader=FileSystemLoader(...), autoescape=select_autoescape(["html","xml"]))`, render all four templates with the marked synthetic fixture, copy static assets, and write `data/processed/ui_preview/index.html`, `sales.html`, `delivery.html`, and `predict.html` (with assets under `static/`). It passes relative `page_urls` (`index.html`, `sales.html`, `delivery.html`, `predict.html`) and `asset_prefix="static"`; every static preview link is relative, so `python -m http.server 8000 --directory data/processed/ui_preview` serves `/` as `index.html` and page-to-page navigation without a FastAPI import or running backend. In the live app Wageeh injects actual route URLs and `asset_prefix="/static"`. Confirm templates do not require FastAPI `Request`/`url_for`. These commands and helper are proposed and untested; no install is authorized here. Jinja2 and any Plotly browser bundle must be present in the approved environment; if Plotly is unavailable, preview template/table states and defer interactive Plotly verification until the approved dependency exists.

- Four pages and navigation render with fixtures.
- No undefined/unsafe template variables.
- KPI units and population context visible.
- Each chart uses consistent arrays, title, axes, and empty response.
- Prediction form excludes outcome/leakage fields and submits agreed names.
- Valid result, validation error, no-data and model-unavailable states render.
- Mobile-width layout, keyboard navigation, input labels and contrast are reasonable.
- Fixtures are explicitly synthetic and no real dataset rows are committed.

Independent demonstration: show the four-page mock preview; explain one KPI card, one chart, a synthetic prediction result, and an error state. State that the mock has no model/API performance behind it. During final demo, use live API only after Wageeh confirms the route and model are ready.

## Git and boundaries

Suggested feature branches: `feature/V3-10-ui-shell` and `feature/V3-11-dashboard-pages`; use small PRs, task-ID titles, and nonauthor review when feasible. Branch rules/CI enforcement are unverified; policy does not imply settings. Stage only templates/static assets/UI tests. Check the staged diff and never include raw/generated data, DB files, model artifacts, secrets, `.venv`, caches, or notebook checkpoints. Do not change Wageeh's `src/app/` or Hamza's `src/sql/`; request contract changes through review and team coordination. Final merge timing is coordinated by Wageeh.

## Per-task dependency cards

| Task | Prerequisite owner and exact input | Type / independent start | Fallback and integration verification | Handoff and blocker response |
|---|---|---|---|---|
| V3-10 | Wageeh V3-01: approved scope, page/API context schemas and synthetic mock examples | Hard kickoff predecessor; no API/data dependency | Frozen synthetic JSON; render test against fixtures | Send shell/context keys/preview command to Wageeh; if the schema is unsettled, request a decision rather than inventing keys |
| V3-11 | Rana V3-10 shell; Wageeh V3-01 frozen KPI/chart/prediction request-response schemas | Hard own-stream predecessor; live backend not required | Continue with explicitly marked synthetic fixtures; V3-14 checks exact route-template/request parity | Send pages, fields, chart arrays and error/empty states to Wageeh; delayed API/SQL/EDA does not block UI completion, but real integration remains pending |

For both tasks, mock values remain visibly synthetic. At integration, test every success, validation, empty-data and unavailable-model state using the producer's schema. If an API field changes, pause the affected integration and request a shared-contract version update; do not silently adapt a mock and call it compatible.
