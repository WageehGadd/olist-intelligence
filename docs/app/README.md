# FastAPI analytics backend (V3-12)

This backend serves the frozen V3-12 read-only analytics API and server-rendered page contexts. It does not calculate or replace Hamza's KPIs, substitute test fixtures when producer files are absent, implement the prediction POST, or contain Rana's finished UI.

## Environment and startup

Use Python 3.10.20. Install the app/runtime dependencies into the project environment with:

```sh
.venv/bin/python -m pip install -r requirements-app.txt
.venv/bin/python -m uvicorn src.app.main:app --reload
```

TestClient tests use only explicitly synthetic temporary CSV fixtures. The current local environment was verified with FastAPI 0.162.5, Starlette 1.7.0, Pydantic 2.14.3, Jinja2 3.1.6, HTTPX 0.28.1 and Uvicorn 0.54.0. The producer files are expected under ignored `data/processed/`; the four authentic files were absent during V3-12 implementation, so live producer integration is pending.

## Routes and data states

`GET /health` returns exactly `{"status":"ok"}` and does not indicate model readiness. The JSON routes are the five read-only analytics/chart endpoints in Shared Contracts. The four HTML routes (`/`, `/sales`, `/delivery`, `/predict`) render Jinja2 on the server. Period parameters accept `all` or a real `YYYY-MM` calendar month; invalid values return 422 `INVALID_PERIOD`.

A missing authoritative source yields HTTP 503 `DATA_UNAVAILABLE` from the relevant JSON endpoint. Pages stay HTTP 200, preserve other available sources, and set `data_state="unavailable"` with a safe message when one or more files are missing. Existing malformed or contract-incompatible data yields HTTP 500 `DATA_INVALID`; internal paths/details are not returned. Empty chart files are not replaced with values. No synthetic fixture is read by production services.

## Rana template handoff

Wageeh owns the page handlers, template context construction, services, and API routes. When Rana's templates are present, the app loads these exact paths:

- `templates/pages/overview.html`
- `templates/pages/sales.html`
- `templates/pages/delivery.html`
- `templates/pages/predict.html`

Until then, the neutral temporary templates are `src/app/templates/backend_fallback/{overview,sales,delivery,predict}.html`; they visibly identify themselves as backend fallbacks and are separate from Rana's owned template paths. Rana templates receive `request`, `page_urls` (`overview:/`, `sales:/sales`, `delivery:/delivery`, `predict:/predict`), `asset_prefix="/static"`, `data_state`, nullable `message`, and page-specific context: Overview `period,kpis`; Sales `period,category_item_value,category_item_counts,item_price_distribution`; Delivery `period,kpis,delivery_monthly`; Prediction `request_schema,notice,result,error` (result/error are null in V3-12). Each chart value is `{definition_version,series}`. The source files and JSON routes are mapped in Shared Contracts; templates never read files directly.

Static assets are served from the repository `static/` directory only when it exists. Rana's browser interactions remain out of scope here: Sales period changes consume `GET /api/v1/analytics/category-item-value`, Delivery period changes consume `GET /api/v1/analytics/delivery-monthly`, and the prediction form later consumes the V3-13 `POST /api/v1/predict`. No JavaScript or prediction endpoint is implemented by V3-12.

## Current integration limits

Hamza's `sql_kpis.csv` and `sql_category_item_value.csv`, and Hasnaa's `eda_category_item_counts.csv` and `eda_item_price_distribution.csv` were not present during implementation. The V3-12 backend foundation is accepted and its ledger status is Completed; its tests establish contract behavior with synthetic fixtures only. Authentic data and UI integration remain deferred to V3-14.

V3-14 integration acceptance checks: (1) validate the actual Hamza KPI and category CSVs against the frozen schemas; (2) compare each KPI's unit, population, and business definition with the authoritative contract, without inventing unstated literal strings; (3) validate Hasnaa's actual EDA outputs; (4) replace these fallback templates with Rana's approved templates; and (5) run authentic local end-to-end integration tests. A nonblocking V3-12 review observation is that the service does not enforce exact unit/population strings for most non-delay KPIs; resolve this through the V3-14 comparison against the frozen contract, not new assumptions.
