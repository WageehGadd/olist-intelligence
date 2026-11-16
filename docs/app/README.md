# FastAPI analytics backend (V3-12)

This backend serves the frozen V3-12 read-only analytics API and the V3-13 prediction endpoint, plus server-rendered page contexts. It does not calculate or replace Hamza's KPIs, substitute test fixtures when producer files are absent, or contain Rana's finished UI/browser interaction.

## Environment and startup

Use Python 3.10.20. Install the app/runtime dependencies into the project environment with:

```sh
.venv/bin/python -m pip install -r requirements-app.txt
.venv/bin/python -m uvicorn src.app.main:app --reload
```

TestClient tests use only explicitly synthetic temporary CSV fixtures. The current local environment was verified with FastAPI 0.162.5, Starlette 1.7.0, Pydantic 2.14.3, Jinja2 3.1.6, HTTPX 0.28.1 and Uvicorn 0.54.0. The producer files are expected under ignored `data/processed/`; the four authentic files were absent during V3-12 implementation, so live producer integration is pending.

## Routes and data states

`GET /health` returns exactly `{"status":"ok"}` and does not indicate model readiness. The JSON routes include the five read-only analytics/chart endpoints in Shared Contracts and `POST /api/v1/predict`. The four HTML routes (`/`, `/sales`, `/delivery`, `/predict`) render Jinja2 on the server. Period parameters accept `all` or a real `YYYY-MM` calendar month; invalid values return 422 `INVALID_PERIOD`.

A missing authoritative source yields HTTP 503 `DATA_UNAVAILABLE` from the relevant JSON endpoint. Pages stay HTTP 200, preserve other available sources, and set `data_state="unavailable"` with a safe message when one or more files are missing. Existing malformed or contract-incompatible data yields HTTP 500 `DATA_INVALID`; internal paths/details are not returned. Empty chart files are not replaced with values. No synthetic fixture is read by production services.

## V3-13 prediction endpoint and Rana handoff

`POST /api/v1/predict` accepts only the frozen request fields: source-naive `purchase_timestamp` in exact `YYYY-MM-DDTHH:MM:SS` form, real `estimated_delivery_date` in `YYYY-MM-DD` form on or after the purchase calendar date, uppercase Brazilian `customer_state` from the Shared Contracts enum (including `PR`), and a nonempty `items` array. Each item is exactly one row with finite, nonnegative JSON-number fields `price` and `freight_value`. Unknown fields are rejected. Item count is the number of array elements; no quantity, order/customer/product/seller identifiers, final status, reviews, payments, or actual outcomes are accepted. The API sends these validated raw values to the same `src/ml/features.py::derive_model_features` function used by historical feature construction, then calls the V3-09 `predict_one` interface.

The successful response exposes only `prediction` (`late|on_time`), `probability_late` (finite number from 0 to 1), SHA-256-derived `model_version`, and the academic-use `notice`. The threshold and artifact details are not returned. The example below is **synthetic only** and is not a measured model output:

```json
{
  "purchase_timestamp": "2018-05-10T12:30:00",
  "estimated_delivery_date": "2018-06-01",
  "customer_state": "SP",
  "items": [{"price": 29.90, "freight_value": 10.20}]
}
```

```json
{
  "prediction": "late",
  "probability_late": 0.62,
  "model_version": "synthetic-example-version",
  "notice": "Retrospective academic estimate conditional on historically eligible delivered orders. It is not validated for live all-order predictions, and probability calibration has not been established."
}
```

All request validation and canonical feature-input errors return HTTP 422 `{"detail":"Invalid prediction request","code":"INVALID_INPUT"}`. Missing, checksum-mismatched, or incompatible verified model artifacts return HTTP 503 `{"detail":"Model artifact is unavailable","code":"MODEL_UNAVAILABLE"}`. No fallback model or synthetic score is produced; unexpected software failures remain server errors. Rana owns the browser form and should show a loading state during submission, display `late`/`on_time` with the returned probability and notice on success, show a safe correction message for `INVALID_INPUT`, and an unavailable state for `MODEL_UNAVAILABLE`. The backend does not add prediction JavaScript or redesign the page.

Real predictions require the ignored local selection manifest `data/processed/v3_09_model_selection.json`, its validation/provenance files, and the checksum-matching selected joblib artifact at the manifest's repository-relative path under `models/local/`. `src/ml/inference.py` verifies the manifest, candidate, feature order, artifact SHA-256, fitted pipeline interface, and frozen threshold before inference. A fresh Git clone does not contain these ignored files and therefore returns `MODEL_UNAVAILABLE` until they are separately and safely supplied. No model binary or generated manifest is included in Git.

## Rana template handoff

Wageeh owns the page handlers, template context construction, services, and API routes. When Rana's templates are present, the app loads these exact paths:

- `templates/pages/overview.html`
- `templates/pages/sales.html`
- `templates/pages/delivery.html`
- `templates/pages/predict.html`

Until then, the neutral temporary templates are `src/app/templates/backend_fallback/{overview,sales,delivery,predict}.html`; they visibly identify themselves as backend fallbacks and are separate from Rana's owned template paths. Rana templates receive `request`, `page_urls` (`overview:/`, `sales:/sales`, `delivery:/delivery`, `predict:/predict`), `asset_prefix="/static"`, `data_state`, nullable `message`, and page-specific context: Overview `period,kpis`; Sales `period,category_item_value,category_item_counts,item_price_distribution`; Delivery `period,kpis,delivery_monthly`; Prediction `request_schema,notice,result,error` (`result` and `error` start null; Rana's browser interaction owns their post-response state). Each chart value is `{definition_version,series}`. The source files and JSON routes are mapped in Shared Contracts; templates never read files directly.

Static assets are served from the repository `static/` directory only when it exists. Rana's browser interactions remain her responsibility: Sales period changes consume `GET /api/v1/analytics/category-item-value`, Delivery period changes consume `GET /api/v1/analytics/delivery-monthly`, and her prediction form consumes the V3-13 `POST /api/v1/predict`. The backend adds no prediction JavaScript.

## Current integration limits

Hamza's `sql_kpis.csv` and `sql_category_item_value.csv`, and Hasnaa's `eda_category_item_counts.csv` and `eda_item_price_distribution.csv` were not present during implementation. The V3-12 backend foundation is accepted and its ledger status is Completed; its tests establish analytics contract behavior with synthetic fixtures only. V3-13 prediction-route changes are under review. Authentic producer/UI integration remains deferred to V3-14.

V3-14 integration acceptance checks: (1) validate the actual Hamza KPI and category CSVs against the frozen schemas; (2) compare each KPI's unit, population, and business definition with the authoritative contract, without inventing unstated literal strings; (3) validate Hasnaa's actual EDA outputs; (4) replace these fallback templates with Rana's approved templates; and (5) run authentic local end-to-end integration tests. A nonblocking V3-12 review observation is that the service does not enforce exact unit/population strings for most non-delay KPIs; resolve this through the V3-14 comparison against the frozen contract, not new assumptions.
