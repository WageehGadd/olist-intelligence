# T-00 — 08 FEATURE LEAKAGE MATRIX

The matrix distinguishes observed source missingness from unknown point-in-time missingness. The extract has no event history for cart, catalog, address or estimated-promise revisions. Purchase-time feature availability is a retrospective assumption, not proven online feasibility. Source aggregates are measured in supplement.json; historical feature coverage was not computed and must not be presented as known.

Direct leakage: target score, actual delivery for delivery target, review text for future review. Temporal leakage: elapsed fulfillment before handoff, final status, late-recorded payments. Aggregation leakage: full-history seller rates, unsafe item/payment/review joins. Identity leakage: memorizing customer/order IDs. Cross-validation leakage: full-data scaling/vocabulary/history, overlapping customer windows and repeated text. Duplicate-order leakage: item rows or multiple reviews split independently. Split whole orders, purge unavailable labels and fit transformations on training only.

## catalog category/dimensions

- **source_table:** products
- **source_columns:** product_category_name; product_weight_g; product_length_cm; product_height_cm; product_width_cm
- **transformation:** item-level then count/weighted summaries
- **grain:** order
- **earliest_availability:** Before purchase (static snapshot assumption)
- **target_task:** delivery/review
- **missingness:** {"product_category_name": {"item_missing": 1603, "orders_any_missing": 1451}, "product_weight_g": {"item_missing": 18, "orders_any_missing": 16}, "product_length_cm": {"item_missing": 18, "orders_any_missing": 16}, "product_height_cm": {"item_missing": 18, "orders_any_missing": 16}, "product_width_cm": {"item_missing": 18, "orders_any_missing": 16}, "distance_km": {"item_missing": 555, "orders_any_missing": 494}}
- **leakage_risk:** catalog updates not timestamped
- **complexity:** medium
- **recommendation:** retain with missing indicators; verify version availability

## purchase calendar

- **source_table:** orders
- **source_columns:** order_purchase_timestamp
- **transformation:** hour/weekday/month
- **grain:** order
- **earliest_availability:** At purchase creation
- **target_task:** delivery/review
- **missingness:** 0
- **leakage_risk:** low; timezone unspecified
- **complexity:** low
- **recommendation:** retain

## promised lead time

- **source_table:** orders
- **source_columns:** order_estimated_delivery_date; order_purchase_timestamp
- **transformation:** elapsed days
- **grain:** order
- **earliest_availability:** At purchase creation (assumption)
- **target_task:** delivery/review
- **missingness:** 0
- **leakage_risk:** estimated promise may have changed
- **complexity:** low
- **recommendation:** verify original promise contract

## cart totals/counts

- **source_table:** order_items
- **source_columns:** price; freight_value; order_item_id; seller_id; product_id
- **transformation:** sum/count/distinct
- **grain:** order
- **earliest_availability:** At purchase creation (assumption)
- **target_task:** delivery/review
- **missingness:** 775 orders missing items
- **leakage_risk:** final cart snapshot lacks event history
- **complexity:** medium
- **recommendation:** retain only confirmed purchase-known values

## customer geography

- **source_table:** customers
- **source_columns:** customer_state; customer_zip_code_prefix
- **transformation:** state/ZIP lookup
- **grain:** order
- **earliest_availability:** At purchase creation
- **target_task:** delivery/review
- **missingness:** no missing state/ZIP; 278 ZIP lookup misses
- **leakage_risk:** static identity; geography reidentification
- **complexity:** low
- **recommendation:** state preferred; exclude raw customer IDs

## seller geography

- **source_table:** sellers
- **source_columns:** seller_state; seller_zip_code_prefix
- **transformation:** aggregate item sellers
- **grain:** order
- **earliest_availability:** Before purchase (snapshot assumption)
- **target_task:** delivery/review
- **missingness:** 7 seller lookup misses
- **leakage_risk:** multi-seller aggregation
- **complexity:** medium
- **recommendation:** retain aggregate, not arbitrary first seller

## approximate distance

- **source_table:** geolocation; customers; sellers
- **source_columns:** ZIP prefix; latitude; longitude
- **transformation:** deduplicate/screen/median then Haversine
- **grain:** item to order
- **earliest_availability:** At purchase creation (static proxy)
- **target_task:** delivery/review
- **missingness:** {"item_missing": 555, "orders_any_missing": 494}
- **leakage_risk:** raw ZIP join amplification; version unknown
- **complexity:** medium
- **recommendation:** conditional retain

## payment features

- **source_table:** order_payments
- **source_columns:** payment_value; payment_type; payment_installments
- **transformation:** order-level sums/count/max
- **grain:** order
- **earliest_availability:** After payment approval (unverified)
- **target_task:** delivery/review
- **missingness:** 1 order missing payments
- **leakage_risk:** no record timestamps; future payment additions
- **complexity:** medium
- **recommendation:** excluded from purchase baseline; instrument first

## approval elapsed

- **source_table:** orders
- **source_columns:** order_approved_at; order_purchase_timestamp
- **transformation:** elapsed days
- **grain:** order
- **earliest_availability:** After payment approval
- **target_task:** delivery/review
- **missingness:** 160 missing approval
- **leakage_risk:** post-purchase leakage
- **complexity:** low
- **recommendation:** approval/carrier only

## fulfillment elapsed

- **source_table:** orders
- **source_columns:** order_delivered_carrier_date; order_approved_at
- **transformation:** elapsed days
- **grain:** order
- **earliest_availability:** After carrier handoff
- **target_task:** delivery/review
- **missingness:** 1783 missing carrier; 1359 negative intervals
- **leakage_risk:** post-purchase leakage; chronology errors
- **complexity:** low
- **recommendation:** carrier only after chronology validation

## actual duration/lateness

- **source_table:** orders
- **source_columns:** order_delivered_customer_date; order_estimated_delivery_date
- **transformation:** duration/calendar comparison
- **grain:** order
- **earliest_availability:** After delivery
- **target_task:** post-delivery review risk
- **missingness:** 2965 missing actual
- **leakage_risk:** direct delivery-target leakage
- **complexity:** low
- **recommendation:** prohibit delivery model; conditional post-delivery review only

## review text

- **source_table:** order_reviews
- **source_columns:** review_comment_message; review_comment_title
- **transformation:** TF-IDF/tokenization
- **grain:** review
- **earliest_availability:** After review creation, specifically answer submission
- **target_task:** NLP
- **missingness:** 58247 missing messages
- **leakage_risk:** direct future-review leakage
- **complexity:** medium
- **recommendation:** NLP only; never pre-review risk

## review score/answer

- **source_table:** order_reviews
- **source_columns:** review_score; review_answer_timestamp
- **transformation:** label and maturity only
- **grain:** review/order
- **earliest_availability:** After review creation, specifically answer submission
- **target_task:** review/NLP
- **missingness:** 768 orders missing review
- **leakage_risk:** direct target leakage
- **complexity:** low
- **recommendation:** labels/split eligibility only

## historical seller/region performance

- **source_table:** orders; order_items; customers
- **source_columns:** seller_id; state; actual_delivery; promise
- **transformation:** as-of outcome-known aggregates excluding current order; smoothing
- **grain:** seller/state to order
- **earliest_availability:** Before purchase only for prior observed outcomes
- **target_task:** delivery/review
- **missingness:** not computed; cold-start coverage unknown
- **leakage_risk:** future aggregation/CV leakage
- **complexity:** high
- **recommendation:** future work with point-in-time joins

## historical customer behavior

- **source_table:** customers; orders; payments
- **source_columns:** customer_unique_id; purchase; payment
- **transformation:** past-only RFM window
- **grain:** customer
- **earliest_availability:** Before purchase for known prior activity
- **target_task:** future purchase
- **missingness:** few repeats; window evidence in customer report
- **leakage_risk:** identity/CV/window overlap leakage
- **complexity:** high
- **recommendation:** defer prediction; descriptive RFM

## final status/identifiers

- **source_table:** orders; customers
- **source_columns:** order_status; order_id; customer_id; customer_unique_id
- **transformation:** none
- **grain:** order
- **earliest_availability:** After outcome (final status); IDs at purchase
- **target_task:** delivery/review
- **missingness:** 0
- **leakage_risk:** future status; identity memorization; duplicate-order CV
- **complexity:** low
- **recommendation:** exclude final status/IDs from predictors; IDs for grouping only
