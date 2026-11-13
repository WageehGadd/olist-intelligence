# Hamza Execution Plan — Proposed V3

**Owner:** Hamza Ayman Saad Eid. **Workstream:** SQLite and business analytics. **Status:** proposal only; wait for team-lead and instructor confirmation of V3 scope and completion of V3-01.** Follow [`MASTER_EXECUTION_PLAN_V3.md`](MASTER_EXECUTION_PLAN_V3.md) and [`SHARED_CONTRACTS.md`](SHARED_CONTRACTS.md). Your work can start directly from original Olist CSV files after approval; you do not wait for Hasnaa's cleaning work. You do not own FastAPI, ML, or frontend.

## What you deliver

V3-02 creates a small local SQLite database and repeatable CSV importer. V3-03 defines and reconciles SQL business measures. Total owner estimate: 14 hours (approximately 3.5h/week over four weeks). This includes testing/debugging and your handoff. These are planning estimates, not a commitment.

The Master Plan reserves one calendar week and 19 team hours (about 20% of base task effort) for integration/debugging. This is a schedule buffer, not extra Hamza task effort or an automatic assignment. You fix SQL-owned defects only within availability agreed with the team lead; otherwise the team moves the date. Your five-week task average is 2.8h/week, distinct from your 4–6h/week assumed availability.

## Source tables and relationships

Start with `olist_orders` (one row/order; `order_id` unique), `olist_order_items` (one row/order item; (`order_id`,`order_item_id`) unique), `olist_order_payments` (one row/payment; (`order_id`,`payment_sequential`) unique), `olist_customers` (`customer_id` unique per order-linked row; `customer_unique_id` groups people across orders), products (`product_id` unique), category translation, and sellers only if required. Olist also has reviews and geolocation, but neither is needed for the core SQL deliverable. `review_id` is not unique (T-00 found 814 duplicate excess); ZIP prefix is not unique in geolocation. Avoid those tables unless a separately approved need arises.

Relationships: one order has many items and may have many payments; each order row references a customer record; items reference products and sellers. A join of raw items and raw payments can produce item-count × payment-count rows per order and inflate sums. Aggregate each child independently to one row/order before joining or query the child table separately.

## V3-02 — SQLite schema and CSV loading (6h)

### Step-by-step

1. Inspect CSV filenames, headers, row counts, key nulls, and duplicate candidate keys. Use T-00 inventory as an expectation to reconcile, not as hard-coded data.
2. Create `src/sql/schema.sql` with explicit types (`TEXT` IDs/timestamps/categories, `INTEGER` counts/sequential numbers, `REAL` amounts; dates remain text until parsed by analysis code). Declare keys and foreign keys where valid. Turn SQLite foreign-key enforcement on for connections.
3. Write `src/sql/load_sqlite.py` to load only selected columns/tables from `data/raw/`. Read identifiers as strings to avoid accidental numeric conversion or lost formatting. Use parameterized operations or Pandas `to_sql` safely; do not build SQL from untrusted string data.
4. Write to `data/local/olist.sqlite`, which must be ignored. Provide a command that recreates the database from source CSVs and a clear missing-input error.
5. Check imported table counts, candidate key uniqueness, null foreign keys, and representative joins. A test fixture must be small, synthetic, and contain no authentic Olist rows.

### Suggested shape (illustrative)

```sql
CREATE TABLE orders (
  order_id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL,
  order_status TEXT NOT NULL,
  order_purchase_timestamp TEXT,
  order_estimated_delivery_date TEXT,
  order_delivered_customer_date TEXT
);
CREATE TABLE order_items (
  order_id TEXT NOT NULL,
  order_item_id INTEGER NOT NULL,
  product_id TEXT,
  seller_id TEXT,
  price REAL,
  freight_value REAL,
  PRIMARY KEY (order_id, order_item_id),
  FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
```

The example is not a complete schema. Add only needed columns, table keys, and documented nullable behavior. Use `PRAGMA foreign_keys=ON` on every connection if enforcing foreign keys.

### Deliverables and acceptance

Paths: `src/sql/schema.sql`, `src/sql/load_sqlite.py`, local ignored DB, `docs/sql_schema.md`, synthetic fixture tests. Acceptance: repeatable import; declared row grain/keys/relations; imported counts and constraints checked; no raw CSV/database added to Git; reproducible command and exact local requirements documented. Handoff to Hasnaa/Wageeh includes schema version, columns/types, row counts, joins, generator command, test output and limitations.

## V3-03 — KPIs and reconciliation (8h)

### KPI work

Implement the definitions in the shared contract. You are the **sole authoritative owner of every shared dashboard KPI**, including `delay_rate_calendar` and `eligible_late_orders`. Wageeh's independently built V3-06 label is a reconciliation check only; Hasnaa may verify totals but must not publish a competing shared rate. Minimum measures:

- Distinct source orders by month and overall.
- Unique people counted by `customer_unique_id` within the selected order population.
- Delivered order counts and eligible delivery delay numerator/denominator; the exact eligibility/calendar-date rule in Shared Contracts applies.
- Delivered-order item price total and charged freight total at item grain.
- Category item price totals using the category translation table; null/untranslated category becomes `unknown`.
- Optional payment summary only as separately named recorded-payment amounts, not as a join to raw items or as model input.

For every query, write down the grain, source filters, date window, null behavior, unit, and meaning. The combined item price plus freight amount is an item-value proxy, not Olist revenue, accounting revenue, net revenue, or profit. Ensure canceled/undelivered orders are not accidentally mixed into delivered-only measures. Use `COUNT(DISTINCT order_id)` where the selected row grain may repeat an order.

### Safe aggregate example

```sql
WITH item_by_order AS (
  SELECT order_id, SUM(price) AS item_value,
         SUM(freight_value) AS freight, COUNT(*) AS item_count
  FROM order_items GROUP BY order_id
), payment_by_order AS (
  SELECT order_id, SUM(payment_value) AS recorded_payment
  FROM order_payments GROUP BY order_id
)
SELECT o.order_status, COUNT(*) AS orders,
       SUM(i.item_value) AS item_value,
       SUM(i.freight) AS freight
FROM orders o
LEFT JOIN item_by_order i USING (order_id)
GROUP BY o.order_status;
```

Do not include `payment_by_order` in this query unless there is a clear need; if joined, it is one row/order and cannot multiply item rows. Handle orders with no items explicitly. Query syntax should be tested against SQLite.

### Exact output files and consumers

Produce both ignored files with exactly the Shared Contracts schemas:

- `data/processed/sql_kpis.csv`: exact header `kpi_name,period,value,unit,population,numerator_count,denominator_count,definition_version`; one row per (`kpi_name`,`period`). Types: string, `all|YYYY-MM` string, decimal or empty only for undefined rate, string, string, nullable integer, nullable integer, `v1` string. Counts/sums leave both count cells empty; rates populate both. Synthetic example only: `delay_rate_calendar,all,0.1,fraction,eligible delivered orders,2,20,v1` (invented, not an Olist result). You own all authoritative KPI values, including `delay_rate_calendar` and its numerator `eligible_late_orders`.
- `data/processed/sql_category_item_value.csv`: exact header `period,category_name,item_value_brl,definition_version`; one row per (`period`,`category_name`). Types: `all|YYYY-MM` string, English category or `unknown` string, decimal BRL, constant `v1`. Synthetic example only: `all,synthetic-example,125.50,v1` (invented). It has no item-count field.

Wageeh V3-12 reads these local files and maps them to `GET /api/v1/analytics/summary?period=all`, `GET /api/v1/analytics/delivery-monthly?period=all`, and `GET /api/v1/analytics/category-item-value?period=all`. Rana consumes typed JSON, never your CSVs directly. The Shared Contracts file is canonical if a discrepancy is found; the synthetic rows above are schema examples, not expected outputs and must not enter a real-data report.

### Validation and handoff

Use a two-order synthetic fixture with multiple items and multiple payments on one order to prove that totals are not multiplied. Compare a sample of SQL results with an independent Pandas/manual calculation. Reconcile raw/imported row counts and key counts; quantify categories missing/unknown. Add `src/sql/analytics.sql` and/or `queries.py`. Handoff both exact files, schema/version, generation command, real computed counts, denominator/filter definitions and tests to Wageeh. Wageeh integrates the files; Rana consumes API responses. Coordinate contract changes; do not edit another workstream's files directly.

Acceptance: measures have reproducible SQL, accurate grain/filter labels, child-table sums reconcile, duplicate joins do not inflate, output names/types stable, no authentic data or DB tracked. Total estimate 14 hours; if delayed, continue SQL contracts and synthetic fixtures, notify Wageeh, and leave real artifact integration pending instead of waiting on Hasnaa.

## Dependencies and independent demonstration

| Dependency | Details |
|---|---|
| Start gate | Team lead and instructor must confirm the revised scope; V3-01 freezes SQL/KPI contracts. |
| Raw input | Original local Olist CSVs; you read them directly, independent of Hasnaa. |
| Receiver | Wageeh's V3-12/14 and Rana's V3-11/14 consume KPI outputs. |
| Exact handoff | Schema/version, query path, generation command, KPI names/values/units/period/denominator, tests and caveats. |
| Classification | No external dependency for V3-02; V3-03 hard depends on V3-02; real dashboard use is integration-only. |
| Fallback | UI and API use frozen synthetic JSON until your SQL output is ready. |
| Compatibility test | API values and UI labels reconcile exactly to SQL contracts; toy join test checks no inflation. |
| Delayed work | Tell receiver/team lead; continue query tests and documentation; don't silently send incomplete metrics. |

Independent demo: create a temporary synthetic CSV set, run schema/import, run KPI queries, show output and tests. If demonstrating real Olist locally, confirm local-data permission and do not put its content in screenshots or Git. Explain the item/payment relationship and show the inflation-prevention test. Do not claim that SQL analytics are integrated until V3-14 is complete.

## Per-task dependency cards

| Task | Prerequisite owner and exact input | Type / independent start | Fallback and integration verification | Handoff and blocker response |
|---|---|---|---|---|
| V3-02 | Wageeh V3-01: approved scope, frozen schema/KPI contracts; local original CSVs | Hard gate/contract predecessor; direct CSV work independent of Hasnaa | Synthetic sample for schema/import tests; integrate schema/output at V3-14 through row/key reconciliation | Send schema, counts, command and constraints to Hasnaa/Wageeh; if CSV/license/access missing, stop authentic import and tell team lead |
| V3-03 | Hamza V3-02: working SQLite tables; Wageeh V3-01: KPI definitions | Hard V3-02 dependency; no Hasnaa dependency | Multi-item/multi-payment synthetic fixture; integration V3-12/14 compares same KPI keys, unit and denominator | Send stable KPI output/definitions to Rana/Wageeh; if query totals do not reconcile, keep mock in UI and resolve before integration DoD |

For both tasks, a delayed external handoff never blocks their independent local start. If any contract change becomes necessary, propose it through the shared document and wait for team-lead review; do not edit consumer code or claim a changed KPI is equivalent without agreement.

## Git, testing, and scope boundaries

Use `feature/V3-02-sqlite-loader` and `feature/V3-03-sql-business-kpis` (or closely related task grouping approved by team lead), PRs into `main`, and review by someone other than author when feasible. Branch naming and PR review are intended policy; current GitHub enforcement has not been verified. Run focused tests and whitespace checks, inspect staged filenames, and never stage `data/raw/`, `data/processed/`, `data/local/`, `.venv/`, secrets or caches. You do not build API routes or pages; report interface requirements through a contract change proposal.
