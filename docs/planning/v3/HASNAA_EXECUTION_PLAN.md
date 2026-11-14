# Hasnaa Execution Plan — V3

**Owner:** Hasnaa Mohamed Mohamed Darwish. **Workstream:** data cleaning, preprocessing and EDA. **Status:** official V3 planning baseline; V3-01 is completed, but implementation requires Hasnaa's local setup check and separate team-lead task-start coordination. Instructor approval is team-leader-reported, without written evidence.** Read [`MASTER_EXECUTION_PLAN_V3.md`](MASTER_EXECUTION_PLAN_V3.md), the relevant raw-data and output sections of [`SHARED_CONTRACTS.md`](SHARED_CONTRACTS.md), and the per-member pre-start checks in [`V3-01_CONTRACT_FREEZE_AND_KICKOFF.md`](V3-01_CONTRACT_FREEZE_AND_KICKOFF.md). You work independently from the original CSVs and do not wait for Hamza's SQL database. You do not own the ML model, SQL schema, or FastAPI.

## Your tasks and estimated workload

- V3-04 — Data profiling and cleaning outputs: 8h.
- V3-05 — EDA, charts and findings: 6h.

Total 14 owner hours, about 3.5h/week over a four-week scenario; test/debug and handoff are included. This is a proposal, not a deadline.

The Master Plan reserves one calendar week and 19 team hours (about 20% of base task effort) for integration/debugging. This is schedule buffer, not extra Hasnaa task effort or an automatic assignment. You fix EDA-owned defects only within availability agreed with the team lead; otherwise the team reforecasts. Your five-week task average is 2.8h/week, distinct from the assumed 4–6h/week availability.

## Start and inputs

Once V3 is authorized and V3-01 freezes the contracts, use local originals: `olist_orders_dataset.csv`, `olist_order_items_dataset.csv`, `olist_customers_dataset.csv`, `olist_products_dataset.csv`, `product_category_name_translation.csv`. Sellers/geolocation are optional; do not add geolocation just to make more charts. Validate filenames/columns against the T-00 audit. Raw datasets are not in the repository and must never be committed. Begin directly from CSVs—Hamza's database and outputs are not prerequisites.

T-00 reports 99,441 orders, 112,650 item rows, 99,441 customer rows, 32,951 products, 71 translated categories; 610 products have missing category names; there are 2 missing values in each product dimension/weight field; geolocation is nonunique on ZIP prefix; `customer_unique_id` represents repeat customers while `customer_id` maps to an order-linked customer row. Treat those as checks to reconcile, not fabricated outputs. T-00 also found 96,470 eligible delivery records, but your descriptive population need not equal that target population; always name the denominator.

## V3-04 — Profiling and cleaning (8h)

### Beginner workflow

1. **Inspect:** read headers and dtypes; record row/column counts; never print or export personal/raw IDs. Check CSV encoding, missing values, candidate key duplicates, and malformed values.
2. **Declare grain:** orders are one per `order_id`; items per (`order_id`,`order_item_id`); customer rows per `customer_id`; products per `product_id`. Do not assume review or geolocation key uniqueness.
3. **Profile nulls and duplicates:** report null counts/percent by required field. Distinguish exact duplicate rows from repeated keys with differing content. Do not drop rows without a stated rule and before/after count.
4. **Parse types:** use explicit `pd.to_datetime(..., errors="coerce")`; count parse failures. Preserve source timestamp semantics and note timezone is unspecified. Keep IDs as strings. Convert price/freight to numeric with invalid-value counts.
5. **Join narrowly:** translate product categories and fill absent/unmatched categories with `unknown` plus a missingness flag. Avoid raw geolocation joins. Keep item table at item grain and orders at order grain. If deriving one order-level item output, use `groupby("order_id")` and name each aggregate; never attach raw payments or unaggregated geolocation.
6. **Write reproducible outputs:** `data/processed/orders_clean.csv` and `order_items_clean.csv`, both ignored. The exact required columns/grains are in Shared Contracts. Keep exclusion reason counts in a Markdown/JSON report, not silently discarded rows.
7. **Test:** small synthetic fixtures with nulls, duplicate rows, invalid dates, unmatched category, multi-item order and date boundaries. Test order grain, item grain, stable schema and deterministic output.

Illustrative Pandas pattern:

```python
orders = pd.read_csv(path, dtype={"order_id": "string", "customer_id": "string"})
orders["purchase_ts"] = pd.to_datetime(
    orders["order_purchase_timestamp"], errors="coerce"
)
date_parse_failures = orders["purchase_ts"].isna().sum()
duplicate_order_ids = orders["order_id"].duplicated(keep=False).sum()
```

This example is not a complete pipeline. Record original and cleaned row counts before resolving duplicates. Do not replace missing values with zero unless zero has a valid business meaning. For ML, do not fit imputers/scalers using all data; Wageeh owns the training-only model pipeline.

### Deliverables and acceptance

Proposed files: `src/data/clean_eda.py`, `docs/eda/data_quality.md`, generated ignored CSV outputs. The report states input files, observed rows, columns, dtypes, nulls, duplicates, invalids, decisions, exclusions, output grain/schema, and command to recreate. Acceptance: decisions are justified and traceable; output schemas exactly match Shared Contracts; raw files remain unchanged; generated outputs stay ignored; synthetic tests pass; all unsupported assumptions are called out. Handoff output schemas and row-count report to Hamza and Wageeh even though they do not depend on your code to start.

## V3-05 — EDA, visualizations and findings (6h)

Use cleaned order/item data and choose a small set of useful questions:

- How do order counts and item-value proxy vary over time?
- Which translated categories have highest item value/count under an explicit order-status filter?
- How do item price/freight and order-item counts distribute, with outliers visible?

Define population and missing-value treatment for each chart. Avoid causal wording. Never say item value plus freight is profit/revenue. Do not publish authoritative shared KPI values from EDA: Hamza owns all dashboard KPIs, including `delay_rate_calendar`. You may independently reconcile a delay calculation for validation, but hand any discrepancy to Hamza/Wageeh rather than publishing a competing dashboard value.

Write a reproducible script at `src/data/eda.py`. Produce the exact ignored chart-ready files from Shared Contracts. `data/processed/eda_category_item_counts.csv` has exact header `category_name,item_count,population,definition_version`; types are string (English or `unknown`), integer item-row count, constant `delivered_order_items`, constant `v1`; synthetic example only: `synthetic-example,3,delivered_order_items,v1`. `data/processed/eda_item_price_distribution.csv` has exact header `bin_label,bin_lower_brl,bin_upper_brl,item_count,population,definition_version`; types are string, decimal BRL, nullable decimal BRL only for the open-ended last bin, integer item-row count, constant `all_items_finite_nonnegative_price`, constant `v1`; bins are `[0,25)`, `[25,50)`, `[50,100)`, `[100,250)`, `[250,500)`, `[500,+∞)`; synthetic example only: `0-25,0,25,3,all_items_finite_nonnegative_price,v1`. Every example above is invented and not an Olist result. Save tracked findings/captions in `docs/eda/findings.md`; derived data/figures remain ignored. Handoff these exact files to Wageeh for API mapping; Rana consumes JSON via Wageeh and never reads your CSV files directly. Shared Contracts is canonical if a discrepancy is found.

Rana consumes `/api/v1/charts/category-item-counts` and `/api/v1/charts/item-price-distribution`; she never opens these CSVs from the browser. Wageeh V3-12/14 validates and maps each file to the API series contract. The sample rows in Shared Contracts are synthetic schema fixtures, not expected counts or Olist findings.

Acceptance: selected plots have correct grain/denominators/labels; each finding is supported by computed output; no unsupported stats are invented; customer/order IDs and personal data are not exposed; tests/checks verify denominator and chart fields; generated files remain local.

## Dependency, fallback, and handoff record

| Required input/dependency | Owner | Classification/start rule | Exact output/receiver | Fallback and verification |
|---|---|---|---|---|
| V3 scope approval and shared schema | V3 scope approval is team-leader-reported; V3-01 by Wageeh | Hard gate before implementation | Agreed output columns/types | No work before V3-01 acceptance; freeze version at kickoff |
| Original local CSVs | Dataset owner obtains separately | No external teammate dependency | Clean order/item outputs | Missing files are a blocker; do not fetch/share unlicensed copy |
| Hamza SQL schema/database | Hamza | No dependency for V3-04/05; optional integration comparison | Reconciliation notes to Hamza | Continue with direct CSV; compare at V3-14 |
| Hamza authoritative KPI | Hamza V3-03 | Not a dependency for your chart outputs; reconciliation only | Optional validation of rate totals; do not publish a second KPI | Compare privately and report discrepancy to Hamza/Wageeh |
| UI/API chart schema | Wageeh V3-01; Rana V3-10/11 | Contract prerequisite; live integration-only at V3-14 | Synthetic chart fixture | Match exact CSV/API fields and category population |
| API/dashboard integration | Wageeh | Integration-only | Findings and cleaned output contract | No need to wait for backend |

Every handoff should include file schema/grain, generation command, input/version, row counts and exclusions, test results, caveats, and whether values use synthetic or authentic local data. If delayed, tell receiving owner/team lead, keep their mock work moving, and identify exactly which integration check remains blocked.

## Independent demonstration

Use a synthetic miniature CSV set to show profiling, one cleaning decision, and one chart with explicit denominator. To demonstrate real-data findings locally, use only separately authorized files, do not put them in screenshots/PRs, and describe them only with aggregate outputs. Show how `customer_id` differs from `customer_unique_id`, and why item rows must be aggregated before order-level joins. Explain that descriptive findings do not establish causality. Do not claim SQL/API integration until those tasks are complete.

## Git and safe boundaries

Suggested branches: `feature/V3-04-cleaning-eda` and `feature/V3-05-eda-findings`. Use PRs, have a nonauthor review where feasible, and coordinate merge timing with Wageeh. Actual repository branch protection/required CI has not been verified; policy text is not enforcement. Stage explicit code/docs/tests only; check `git diff --cached --name-only` and never stage `data/raw/`, `data/processed/`, `.venv/`, local DBs, notebook checkpoints, secrets, or caches. You own data prep/EDA; ask Hamza for SQL changes through contract/PR rather than editing his files.

## Per-task dependency cards

| Task | Prerequisite owner and exact input | Type / independent start | Fallback and integration verification | Handoff and blocker response |
|---|---|---|---|---|
| V3-04 | Wageeh V3-01: approved scope/output schema; local original CSVs | Hard kickoff predecessor; direct CSV start does not depend on Hamza | Synthetic rows test transforms; V3-14 verifies schema/grain and reconciles selected counts | Send cleaning rules, output schema/row counts/command to Hamza and Wageeh; missing inputs block real output and must be escalated |
| V3-05 | Hasnaa V3-04: cleaned order/item output; V3-01 chart questions/KPI semantics | Hard own-stream predecessor; no SQL or backend start dependency | Mock chart arrays while real data unavailable; V3-14 checks denominators, units and payload shape | Send chart-ready arrays/findings/definitions to Rana and Wageeh; if cleaning is late, continue mock chart implementation and identify the pending data acceptance |

For both tasks, changes to output names, grain, date handling, or denominator must be raised as a shared-contract change. A receiver's delay does not justify silent format changes; keep a versioned handoff and notify the team lead if acceptance is blocked.
