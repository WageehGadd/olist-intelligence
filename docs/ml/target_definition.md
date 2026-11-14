# V3-06 — Delivery Target and Eligible Population

## Objective

Create a reproducible, order-grain historical population for predicting whether an order that was eventually delivered arrived after its promised **calendar date**. For each eligible order, `late = 1` only when the delivered calendar date is strictly later than the estimated delivery calendar date. Same-day deliveries are `late = 0`, even when delivery time is later than the promise timestamp. No elapsed-hour or 30-day threshold is used.

This is a conditional historical label for delivered orders. It does not turn cancelled, unavailable, shipped, or otherwise unresolved orders into on-time negatives and is not a complete operational-failure target.

## Source and timestamp interpretation

The input is the original, locally held `data/raw/olist_orders_dataset.csv`. The file is read without modifying it. The implementation requires `order_id`, `order_status`, `order_purchase_timestamp`, `order_estimated_delivery_date`, and `order_delivered_customer_date`.

The original Olist timestamps are parsed strictly as source-naive `%Y-%m-%d %H:%M:%S`. No timezone is attached, inferred, or converted. Calendar dates are obtained by normalizing the parsed naive timestamp to midnight, preserving the source's displayed date. Missing, blank, malformed, fractional-format, and timezone-bearing timestamp strings do not produce labels; they are excluded and counted. The original purchase time is retained as a naive `YYYY-MM-DD HH:MM:SS` string, while the promise and delivery outputs contain ISO calendar dates.

## Eligibility and target

Include an order only when all of these hold:

1. `order_status` is exactly `delivered`.
2. Purchase, estimated delivery, and delivered-customer timestamps are present and parse under the source format.
3. Estimated delivery calendar date is on or after purchase calendar date.
4. Actual delivery calendar date is on or after purchase calendar date.

Among eligible rows:

```text
late = int(delivered_date > estimated_delivery_date)
```

These eligibility exclusions apply only to the delivery-delay KPI and ML target population. They do not automatically filter revenue proxies, customer counts, or other commercial measures. This V3-06 output independently implements Hamza's authoritative population definition for reconciliation; Hamza remains the sole publisher of shared dashboard KPI values.

## Output contract

Generated file: `data/processed/delivery_population.csv` (ignored by Git). Rows are sorted by `order_id` for deterministic output. The file contains eligible rows only.

| Column | CSV value/type | Meaning |
|---|---|---|
| `order_id` | string | Unique audit/grouping key; never a model predictor |
| `purchase_ts` | source-naive timestamp string, `YYYY-MM-DD HH:MM:SS` | Original purchase wall-time, without timezone conversion |
| `estimated_delivery_date` | ISO date string, `YYYY-MM-DD` | Normalized promised calendar date |
| `delivered_date` | ISO date string, `YYYY-MM-DD` | Normalized actual calendar date |
| `late` | integer `0` or `1` | Calendar-day target |
| `population_version` | string, constant `v1` | Frozen population definition version |

`exclusion_reason` is deliberately not an output column. The generated output has one row per unique eligible `order_id`; duplicate or blank IDs in the source are fatal input errors rather than silently deduplicated.

## Reproducible generation

From the repository root, with the existing project environment:

```bash
.venv/bin/python -m src.ml.build_delivery_population \
  --input data/raw/olist_orders_dataset.csv \
  --output data/processed/delivery_population.csv
```

The script validates the required schema, parses timestamps explicitly, reports one exclusive exclusion reason per source row, reports independent timestamp-quality counts (which may overlap those reasons), and writes only the eligible output. It refuses to overwrite its input or write anywhere inside the repository's protected `data/raw/` directory. Exclusion-reason precedence is: non-delivered/missing status; missing then invalid purchase timestamp; missing then invalid estimated timestamp; missing then invalid delivered timestamp; estimated date before purchase; actual date before purchase. Therefore exclusive reason counts plus eligible rows equal the source row count. The independent missing/malformed diagnostics are not summed into that accounting.

## Recomputed local results

These counts were computed from the original local CSV by the documented script; none is hard-coded as an expected result in the builder or unit tests.

| Exclusive disposition | Rows |
|---|---:|
| `not_delivered_or_missing_status` | 2,963 |
| `missing_purchase_timestamp` | 0 |
| `invalid_purchase_timestamp` | 0 |
| `missing_estimated_delivery_timestamp` | 0 |
| `invalid_estimated_delivery_timestamp` | 0 |
| `missing_delivered_customer_timestamp` | 8 |
| `invalid_delivered_customer_timestamp` | 0 |
| `estimated_date_before_purchase_date` | 0 |
| `actual_date_before_purchase_date` | 0 |
| **Exclusive exclusions** | **2,971** |
| **Eligible population** | **96,470** |
| **Source rows** | **99,441** |

The accounting is `2,971 + 96,470 = 99,441`. The order file has 96,478 `delivered` status rows. Eight delivered orders lack a valid delivered-customer timestamp. Across the full source file, the delivered-customer timestamp column has 2,965 missing values: 2,957 occur in the non-delivered group and 8 in delivered rows. These diagnostic counts overlap exclusive exclusions and are not added again.

| Eligible label | Rows |
|---|---:|
| Late (`late = 1`) | 6,534 |
| On-time or early (`late = 0`) | 89,936 |
| Late prevalence | 6.7730900798175595% |

There were no malformed nonmissing timestamps and no eligible chronology violations in this snapshot. The reproduced 96,470 eligible / 6,534 late / 6.7730900798175595% results match the T-00 reconciliation values. T-00 values are a comparison point, not implementation constants.

## Tests and integrity checks

Focused unit tests use only small synthetic rows. They cover exact promised day, later time on the same day, following-day lateness, early delivery, missing and malformed timestamps, non-delivered status, both invalid chronologies, duplicate and blank IDs, required columns, deterministic sorting/output, schema, labels, and empty input. The real output was separately checked for the exact schema, 96,470 unique order IDs, binary labels, chronology, and byte-for-byte repeatability. Raw source files were not modified.

## Limitations and handoff

- The label is conditional on eventual delivery; it excludes failures and unresolved orders.
- The extract does not establish timezone history or version history for the original estimated promise. Availability of the final cart and estimated date at purchase is a retrospective assumption, not proven live availability.
- The target is historical and does not establish future service performance or deployable model performance.
- `order_id` is for audit and later joins only. V3-07 must drop it from the model feature matrix.
- Hand `data/processed/delivery_population.csv`, this definition, exclusion counts, and the label function to V3-07. Hasnaa may independently reconcile descriptive counts. Hamza remains authoritative for `delay_rate_calendar`; report any discrepancy to Hamza rather than publishing a competing dashboard KPI.
