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

The local V3-06 population input contains **96,470** unique eligible orders: **6,534 late** and **89,936 on-time/early**. The V3-07 builder reconciles the target and dates, but not every eligible order can be represented under the frozen customer-state request enum: the original Olist data contains Paraná (`PR`) rows, while Shared Contracts v1's explicit UF enum omits `PR`. V3-07 does not change that frozen contract or silently broaden inference support. **91,547** orders are feature-ready; **4,923** eligible orders (including **199 late labels**) receive the distinct `unsupported_customer_state` exclusion reason. This is an acceptance blocker pending team-lead resolution.

The V3-06 source-level exclusive exclusions remain **2,971** of 99,441 orders: 2,963 non-delivered/missing-status orders and 8 delivered rows missing an actual delivery timestamp. The source audit found zero missing/invalid purchase timestamps, zero missing/invalid estimated timestamps, zero malformed nonmissing delivered timestamps, and zero chronology exclusions. These are target-population dispositions, separate from V3-07 feature exclusions.

The source checks found 99,441 orders, 112,650 item rows, and 99,441 customer rows. Order IDs, customer IDs, and (`order_id`,`order_item_id`) keys were unique; all population order keys joined to raw orders and customer records; no orphan item row referenced a nonexistent order. Raw item rows have no missing/invalid price or freight amounts. **775 source orders across all statuses have no item rows; none of the 96,470 V3-06 eligible orders is among them.** No eligible state was missing; all 27 real Brazilian UFs occur, including `PR`. The frozen request enum contains only 26 UFs and omits `PR`; the local feature code recognizes the valid state but excludes rows using it as unsupported by the contract. There were no feature missing values before preprocessing among retained rows. These counts are from the local original files and are not hard-coded in the builders.

Every exclusive feature-exclusion reason was zero except `unsupported_customer_state`: `missing_customer_id`, `customer_not_found`, `missing_customer_state`, `invalid_customer_state`, `missing_item_rows`, `invalid_item_rows`, `missing_item_amount`, `invalid_item_amount`, `missing_purchase_timestamp`, `invalid_purchase_timestamp`, `missing_estimated_delivery_date`, `invalid_estimated_delivery_date`, and `estimated_date_before_purchase_date` all had no rows. The `unsupported_customer_state` count is **4,923**, representing valid `PR` customers omitted by the frozen contract; 199 carry a late label. The source diagnostics report zero orphan item rows and zero malformed item amounts. The split policy also excludes 247 pre-2017 eligible feature rows and zero post-window rows; these are temporal-window exclusions, not feature-quality exclusions.

The target independently reconciles to the V3-06 output and its original source: 96,470 eligible; 6,534 late; 89,936 on-time/early; 6.77309008% late prevalence. A fresh V3-06 rebuild to a temporary path was byte-identical to the ignored existing target CSV. All nine raw CSV SHA-256 digests matched the existing T-00 raw-hash manifest.

The generated feature CSV has **91,547 rows × 11 columns**: metadata `order_id` (string), `purchase_ts` (source-naive timestamp string), `late` (integer); then the eight contract features in order: four integers, `customer_state` (string), two numeric BRL totals, and integer `item_count`. All numeric/target fields were complete before preprocessing. The model input selection is exactly the eight contract feature columns; metadata is excluded. The supported rows retain 6,335 late and 85,212 on-time/early labels.

### Frozen split results

| Split/window | Rows | Late | On-time/early | Late prevalence | Observed purchase range |
|---|---:|---:|---:|---:|---|
| Train, 2017-01-01–2017-12-31 | 41,234 | 2,383 | 38,851 | 5.77921% | 2017-01-05 15:32:59 – 2017-12-31 23:29:31 |
| Validation, 2018-01-01–2018-03-31 | 19,552 | 2,572 | 16,980 | 13.15466% | 2018-01-01 02:48:41 – 2018-03-31 23:54:10 |
| Test, 2018-04-01–2018-08-31 | 30,514 | 1,377 | 29,137 | 4.51268% | 2018-04-01 00:11:32 – 2018-08-29 15:00:37 |
| Excluded pre-window | 247 | 3 | 244 | 1.21457% | 2016-09-15 12:16:38 – 2016-10-10 18:09:39 |
| Excluded post-window | 0 | 0 | 0 | n/a | n/a |

Removing August 2018 from test as a maturity sensitivity leaves 24,490 orders (994 late, 4.05880% prevalence). The held-out periods show substantial prevalence variation, especially the validation window; V3-08/V3-09 must disclose this cohort drift and not retune the frozen boundaries to obtain a preferred score. This task reports no model scores.

For maturity assessment, the source monthly audit confirms 6,512 source orders / 6,351 delivered-status and V3-06 eligible orders in August 2018; September has 16 source orders and zero delivered/eligible labels; October has 4 and zero. T-00's latest recorded actual delivery event is 2018-10-17, but there is no extraction timestamp proving complete follow-up. Unresolved orders are excluded, not labeled negative. The test result is therefore conditional on eventual delivery and retrospective, not a measure of all-order operational failure risk.

The train-only preprocessing fit used 41,234 training rows. Seven numeric features receive train-fitted median imputation and standardization; the categorical UF receives train-fitted most-frequent imputation and one-hot encoding with unknown-category tolerance. All three splits transformed to 33 columns (seven numeric plus 26 train-observed contract-supported UF categories). No classifier or estimator was trained. The fitted transformer is ignored local output for the V3-08/V3-09/V3-13 handoff, conditional on a decision about the `PR` contract gap.

The generated manifest records the actual counts, exact dates, population/feature checksums, missingness, maturity assessment, and preprocessor metadata. V3-08/V3-09 may not alter target eligibility or use the test interval to select features, model, thresholds, or hyperparameters.
