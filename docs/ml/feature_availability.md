# V3-07 — Point-in-Time Features and Chronological Split

## Purpose and frozen interface

This task consumes the V3-06 eligible delivered-order population and creates one reproducible feature row per order that the frozen request schema can represent. It does not train an estimator, choose model settings, or inspect test metrics. The canonical predictor order is fixed by [Shared Contracts v1](../planning/v3/SHARED_CONTRACTS.md#5-delivery-prediction-contract):

| Order | Name | Raw type | Derivation |
|---:|---|---|---|
| 1 | `purchase_hour` | integer | source-naive purchase wall-time hour, 0–23 |
| 2 | `purchase_weekday` | integer | Python weekday, Monday=0 through Sunday=6 |
| 3 | `purchase_month` | integer | purchase calendar month, 1–12 |
| 4 | `promised_lead_days` | integer | promised calendar date minus purchase calendar date |
| 5 | `customer_state` | string | uppercase Brazilian UF |
| 6 | `item_price_total` | numeric BRL | sum of item `price` values for the order |
| 7 | `freight_total` | numeric BRL | sum of item `freight_value` values for the order |
| 8 | `item_count` | integer | count of physical order-item rows, not quantity values |

The one pure transformation is `src/ml/features.py::derive_model_features`. Historical row construction and future inference call this function. It accepts either strict source-naive purchase timestamp representation at its boundary (`YYYY-MM-DD HH:MM:SS` in Olist or `YYYY-MM-DDTHH:MM:SS` at the API), a normalized strict `YYYY-MM-DD` promised date, an uppercase UF supported by the frozen Shared Contracts v1 enum, and a nonempty list of item objects containing exactly finite nonnegative numeric `price` and `freight_value`. It rejects timezone-bearing/fractional/malformed timestamps, impossible dates, promise dates before purchase, valid UFs omitted by the contract enum, empty carts, extra item fields, booleans, strings, negative values and non-finite amounts. Each item object is one item row.

The V3-06 `order_id` is retained only as a grouping/audit key; `purchase_ts` is retained only for chronological splitting/audit; `late` is the target. The generated model matrix is selected only by the exact eight names above. It excludes `delivered_date`, estimated date, final status, review/payment fields, customer/order IDs, and all other post-purchase or future-derived fields. Target dates are used only to validate V3-06 label reconciliation before feature construction.

## Historical joins and data-quality accounting

Input: ignored `data/processed/delivery_population.csv`, raw orders, raw order items and raw customers. Orders are keyed one row per `order_id`; customer state is reached through `orders.customer_id` to the unique `customers.customer_id`. Item rows are validated at (`order_id`, `order_item_id`) grain and grouped by `order_id` before they are combined with an order. The implementation never joins raw item rows into the order/customer frame, so item multiplicity cannot replicate labels. It fails on duplicate keys, orphan item references, missing V3-06 orders, or a mismatch between the population and source order dates/status/label.

Feature construction makes no silent value substitutions. An eligible order with no item rows, a missing/invalid amount, missing/unmatched customer, missing/invalid state, or invalid feature input is assigned exactly one exclusive feature-exclusion reason in `data/processed/delivery_feature_audit.json`. Invalid raw item amounts are also counted as source-row diagnostics. If a source key/join mismatch or V3-06 target inconsistency appears, the build fails for investigation instead of silently dropping or relabeling rows. The existing V3-06 output and raw CSVs are never modified.

### Availability caveats

- Purchase calendar fields are available at order creation in the extract; the source has no timezone declaration, so values remain source-naive.
- The final estimated date has no version history. Its availability as the original promise at purchase is not proven.
- The final item/cart rows and amounts have no event history. Their availability at purchase is also a retrospective assumption.
- Customer state is present in the linked customer row, but the extract does not prove that address/state was versioned as of order creation.
- Actual delivery, final status, reviews, payments, seller performance and future customer aggregates are not predictors. The outcome is conditional on eventual delivery, not operational failure risk.

These are limitations of the historical extract, not grounds to add proxy fields or redefine the frozen request. The output is an educational retrospective dataset, not proof of live deployability.

## Split policy (fixed before any model work)

Split by purchase **calendar date**, not by random sampling or label. Equal dates and timestamps always stay in the same interval. The boundaries are constants in `src/ml/split.py`:

| Partition | Inclusive start | Exclusive end |
|---|---|---|
| Train | 2017-01-01 | 2018-01-01 |
| Validation | 2018-01-01 | 2018-04-01 |
| Test | 2018-04-01 | 2018-09-01 |

This keeps the primary evaluation window within the January 2017–August 2018 period identified by T-00. Pre-2017 eligible rows are recorded as `excluded_pre_window`, rather than used as a separate period: T-00 reports only 1 eligible September 2016 order, 265 in October and 1 in December. Eligible rows after the test end are recorded as `excluded_post_window`.

T-00 reports 16 source orders in September 2018 and 4 in October, with no delivered orders; these cannot be assigned on-time labels and do not enter V3-06. August 2018 is included as the last test month because T-00 names it in the primary window. The split manifest separately reports test counts/prevalence with August removed as a maturity sensitivity. It does not use either result to optimize boundaries. The dataset has no extraction timestamp, so complete follow-up cannot be proven. Delivered-only cohorts omit unresolved/non-delivered orders, and the reported test distribution is conditional on eventual delivery.

Split labels, actual date ranges, row counts, positive/negative counts, prevalence, pre/post-window exclusions, monthly tail audit and an input file checksum are in ignored `data/processed/delivery_split_manifest.json`. No random seed is needed because the split is date-boundary deterministic.

## Preprocessing contract

`src/ml/preprocessing.py::make_preprocessor` returns a fresh scikit-learn `ColumnTransformer`. Numeric features use median imputation then `StandardScaler`; `customer_state` uses most-frequent imputation then `OneHotEncoder(handle_unknown="ignore")`. It accepts exactly the eight raw feature columns in contract order and rejects metadata/leakage columns. In V3-07, it is fitted **only** on the train partition; validation and test are transformed with that fitted object. It is saved locally as ignored `data/processed/delivery_preprocessor.joblib` for later reuse. This task fits no classifier/regressor and trains no model.

V3-08/V3-09 consume `delivery_feature_splits.csv`, the frozen boundaries and train-fitted preprocessing interface. They must use the existing row labels and date split; do not rerandomize, tune on test, or add predictors. V3-13 can call the same pure feature derivation and load the fitted preprocessor after a model pipeline is separately approved.

## Local outputs and reproduction

All outputs below are ignored by Git; they contain authentic local data and must not be staged or committed:

- `data/processed/delivery_features.csv` — metadata (`order_id`, `purchase_ts`, `late`) plus the exact eight feature columns.
- `data/processed/delivery_feature_audit.json` — input counts, label reconciliation, exclusive feature exclusions, join/amount diagnostics, missingness and monthly cohort audit.
- `data/processed/delivery_feature_splits.csv` — the same rows plus a split/exclusion label.
- `data/processed/delivery_split_manifest.json` — fixed boundaries, populations, prevalence, date ranges, maturity note, checksums and preprocessing record.
- `data/processed/delivery_preprocessor.joblib` — train-fitted transformer only; no estimator or model weights.

Both generators reject output paths outside `data/processed/`, refuse to overwrite their inputs, and require distinct output paths.

From the repository root, with the existing Python 3.10 environment and local raw data:

```bash
.venv/bin/python -m src.ml.features
.venv/bin/python -m src.ml.split
```

The feature build verifies V3-06 target labels against calendar dates and raw orders. Expected V3-06 source/eligible/late counts are reconciled from the actual generated input; no population counts are hard-coded as builder results. The exact observed feature and split counts for this checkout are recorded below after reproduction.

## Verified local results

**Team-lead-approved contract erratum (2026-11-15):** Shared Contracts v1's customer_state input enum omitted valid UF PR (Paraná). The dated erratum adds PR in the canonical enum; the same canonical 27-UF validation set is used by both historical feature construction and the request derivation boundary. This changes only accepted UF input validation. API paths, the exact eight features and their order, delivery target/eligibility rules, output schemas, population_version=v1, and KPI definition_version=v1 remain unchanged. Before the correction, 4,923 otherwise feature-ready eligible orders were excluded solely for valid PR, including 199 late orders. After rebuilding from the local original data, all 4,923 are recovered; no other scope or feature rule changed.

The V3-06 population input contains **96,470** unique eligible orders: **6,534 late** and **89,936 on-time/early** (6.77309008% late). A fresh V3-06 rebuild to a temporary location was byte-identical to the existing ignored target CSV. All nine raw CSV SHA-256 digests matched the T-00 raw-hash manifest and the raw files were not modified.

The source checks found 99,441 orders, 112,650 item rows and 99,441 customer rows. Order IDs, customer IDs, and (order_id,order_item_id) keys were unique; all population order keys joined to raw orders and customer records; there were no orphan item rows. Raw item rows had no missing/invalid price or freight amounts. **775** source orders across all statuses had no item rows; none of the 96,470 eligible orders was among them. No eligible state was missing; all 27 Brazilian UFs occur, including PR.

After the erratum, **all 96,470 eligible orders are feature-ready** in a generated **96,470 × 11** CSV (three metadata/target columns plus the eight contract features). Labels reconcile to **6,534 late** and **89,936 on-time/early**. Every exclusive feature-exclusion reason is zero: customer_not_found, estimated_date_before_purchase_date, invalid_customer_state, invalid_estimated_delivery_date, invalid_item_amount, invalid_item_rows, invalid_purchase_timestamp, missing_customer_id, missing_customer_state, missing_estimated_delivery_date, missing_item_amount, missing_item_rows, missing_purchase_timestamp, and unsupported_customer_state. The last audit category remains available for diagnostic compatibility and has count zero. No feature missingness was present before preprocessing.

The V3-06 source-level exclusive exclusions remain **2,971** of 99,441 source orders: 2,963 non-delivered/missing-status orders and 8 delivered rows missing an actual delivery timestamp. The source audit found zero missing/invalid purchase timestamps, zero missing/invalid estimated timestamps, zero malformed nonmissing delivered timestamps, and zero chronology exclusions. These are target-population dispositions, separate from V3-07 feature exclusions.

### Frozen split results

The predeclared purchase-calendar windows are unchanged: train 2017-01-01 through 2017-12-31; validation 2018-01-01 through 2018-03-31; test 2018-04-01 through 2018-08-31 (exclusive end dates remain 2018-01-01, 2018-04-01, and 2018-09-01 respectively). Counts below were recomputed from the regenerated feature file and split manifest.

| Split/window | Rows | Late | On-time/early | Late prevalence | Observed purchase range |
|---|---:|---:|---:|---:|---|
| Train, 2017-01-01–2017-12-31 | 43,426 | 2,453 | 40,973 | 5.64869% | 2017-01-05 11:56:06 – 2017-12-31 23:29:31 |
| Validation, 2018-01-01–2018-03-31 | 20,627 | 2,657 | 17,970 | 12.88118% | 2018-01-01 02:48:41 – 2018-03-31 23:54:10 |
| Test, 2018-04-01–2018-08-31 | 32,150 | 1,421 | 30,729 | 4.41991% | 2018-04-01 00:11:32 – 2018-08-29 15:00:37 |
| Excluded pre-window | 267 | 3 | 264 | 1.12360% | 2016-09-15 12:16:38 – 2016-12-23 23:16:47 |
| Excluded post-window | 0 | 0 | 0 | n/a | n/a |

The August-removed test sensitivity is **25,799** orders (**1,028** late; **3.98465%** prevalence). Held-out periods show substantial prevalence variation, especially validation; later work must disclose this cohort drift and must not retune the fixed boundaries to obtain a preferred score. No model scores are reported here.

The split is chronological and deterministic by purchase calendar date; no row crosses a boundary. The regenerated manifest confirms **43,426** train rows were used to fit preprocessing, and validation/test were transform-only (validation_or_test_fit=false). Seven numeric features are imputed/scaled using training-only learned values; customer_state is imputed/one-hot encoded with categories learned only from train. Each split transforms to **34 columns**: seven numeric plus the 27 UF categories present in the training data, including PR. No classifier or estimator was trained. The preprocessor remains an ignored local artifact.

### Maturity and right-censoring limitations

T-00 reports 6,512 source orders / 6,351 delivered-status and V3-06 eligible orders in August 2018; September has 16 source orders and zero delivered/eligible labels; October has 4 and zero. The latest recorded actual delivery event is 2018-10-17, but there is no extraction timestamp proving complete follow-up. Unresolved orders are excluded, not labeled negative. Therefore test results are retrospective and conditional on eventual delivery; they do not measure all-order operational failure risk. Final estimated-date version history, item/cart event history, and point-in-time customer-state history are unavailable, so their availability at order creation is not established.

The generated manifest records actual counts, date ranges, population/feature checksums, missingness, maturity assessment, and preprocessing metadata. V3-08/V3-09 must preserve target eligibility and must not use the test interval to select features, models, thresholds, or hyperparameters.
