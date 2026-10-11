# T-00 — 04 DELIVERY TARGET FEASIBILITY

**CONDITIONAL GO — MVP with explicit prediction contract.** Target A: actual delivery calendar date > promised estimated calendar date. This is better aligned to customer promises than an arbitrary duration threshold. Literal timestamps would count 1,292 additional purchase-population same-day deliveries as late. Target B: purchase-to-delivery >30 elapsed days; this threshold is an illustrative audit configuration, not a business-approved service level. Separate carrier-transit or approval-to-delivery targets need their own thresholds and population.

Purchase eligibility: status delivered, actual and estimated dates present, delivery at/after purchase. Approval adds known approval between purchase and delivery. Carrier adds known handoff between approval and delivery. Known historical label population is not the full online population; unknown/canceled records do not become negatives.

Purchase predictors: calendar features, promised lead time, customer state, cart prices/freight/counts, catalog dimensions/categories, seller/customer locations. Availability of final cart records and original estimated date at purchase is an assumption because the extract has no version history. Approval may add elapsed approval duration; payments require instrumentation for when records were known. Carrier may add elapsed fulfillment duration, but excludes subsequent delivery outcomes. Historical seller/regional lateness must use only outcomes actually observed before prediction and exclude current order.

Prohibit actual delivery, eventual status, review fields, future aggregate performance, identifiers as numeric features and any target-derived duration at purchase. Train dummy and logistic before RF/gradient boosting; evaluate CatBoost/XGBoost/LightGBM only after their dependencies and contracts are justified. MLP is a comparison, not a promised improvement. Use chronological folds, point-in-time histories, group all item rows of each order, calibrated probabilities and validation-selected thresholds. Report AP (a PR summary), ROC-AUC, precision/recall/F1, Brier/reliability curves and top-K capture; accuracy is insufficient.

```json
{
  "approval": {
    "calendar_lateness": {
      "n": 96395,
      "negative": 89862,
      "positive": 6533,
      "positive_pct": 6.777322475232118
    },
    "literal_timestamp_lateness": {
      "n": 96395,
      "negative": 88571,
      "positive": 7824,
      "positive_pct": 8.116603558275843
    },
    "over_30_days": {
      "n": 96395,
      "negative": 91845,
      "positive": 4550,
      "positive_pct": 4.720161834120027
    }
  },
  "carrier": {
    "calendar_lateness": {
      "n": 95082,
      "negative": 88573,
      "positive": 6509,
      "positive_pct": 6.845670053217223
    },
    "literal_timestamp_lateness": {
      "n": 95082,
      "negative": 87290,
      "positive": 7792,
      "positive_pct": 8.195031656885636
    },
    "over_30_days": {
      "n": 95082,
      "negative": 90546,
      "positive": 4536,
      "positive_pct": 4.770619044614122
    }
  },
  "monthly_purchase_labels": [
    {
      "mean": 1.0,
      "order_purchase_timestamp": "2016-09",
      "size": 1,
      "sum": 1
    },
    {
      "mean": 0.007547169811320755,
      "order_purchase_timestamp": "2016-10",
      "size": 265,
      "sum": 2
    },
    {
      "mean": 0.0,
      "order_purchase_timestamp": "2016-12",
      "size": 1,
      "sum": 0
    },
    {
      "mean": 0.029333333333333333,
      "order_purchase_timestamp": "2017-01",
      "size": 750,
      "sum": 22
    },
    {
      "mean": 0.029643073200241985,
      "order_purchase_timestamp": "2017-02",
      "size": 1653,
      "sum": 49
    },
    {
      "mean": 0.04556166535742341,
      "order_purchase_timestamp": "2017-03",
      "size": 2546,
      "sum": 116
    },
    {
      "mean": 0.06556665219279201,
      "order_purchase_timestamp": "2017-04",
      "size": 2303,
      "sum": 151
    },
    {
      "mean": 0.029901269393511988,
      "order_purchase_timestamp": "2017-05",
      "size": 3545,
      "sum": 106
    },
    {
      "mean": 0.030303030303030304,
      "order_purchase_timestamp": "2017-06",
      "size": 3135,
      "sum": 95
    },
    {
      "mean": 0.027892561983471075,
      "order_purchase_timestamp": "2017-07",
      "size": 3872,
      "sum": 108
    },
    {
      "mean": 0.02909611256856666,
      "order_purchase_timestamp": "2017-08",
      "size": 4193,
      "sum": 122
    },
    {
      "mean": 0.04385542168674699,
      "order_purchase_timestamp": "2017-09",
      "size": 4150,
      "sum": 182
    },
    {
      "mean": 0.041759714158106295,
      "order_purchase_timestamp": "2017-10",
      "size": 4478,
      "sum": 187
    },
    {
      "mean": 0.12403951701427003,
      "order_purchase_timestamp": "2017-11",
      "size": 7288,
      "sum": 904
    },
    {
      "mean": 0.07455106112824234,
      "order_purchase_timestamp": "2017-12",
      "size": 5513,
      "sum": 411
    },
    {
      "mean": 0.05700947800254633,
      "order_purchase_timestamp": "2018-01",
      "size": 7069,
      "sum": 403
    },
    {
      "mean": 0.14126620900076278,
      "order_purchase_timestamp": "2018-02",
      "size": 6555,
      "sum": 926
    },
    {
      "mean": 0.18963301442239042,
      "order_purchase_timestamp": "2018-03",
      "size": 7003,
      "sum": 1328
    },
    {
      "mean": 0.04501323918799647,
      "order_purchase_timestamp": "2018-04",
      "size": 6798,
      "sum": 306
    },
    {
      "mean": 0.06563935397836716,
      "order_purchase_timestamp": "2018-05",
      "size": 6749,
      "sum": 443
    },
    {
      "mean": 0.011646981627296589,
      "order_purchase_timestamp": "2018-06",
      "size": 6096,
      "sum": 71
    },
    {
      "mean": 0.03378817413905133,
      "order_purchase_timestamp": "2018-07",
      "size": 6156,
      "sum": 208
    },
    {
      "mean": 0.061880018894662256,
      "order_purchase_timestamp": "2018-08",
      "size": 6351,
      "sum": 393
    }
  ],
  "purchase": {
    "calendar_lateness": {
      "n": 96470,
      "negative": 89936,
      "positive": 6534,
      "positive_pct": 6.7730900798175595
    },
    "literal_timestamp_lateness": {
      "n": 96470,
      "negative": 88644,
      "positive": 7826,
      "positive_pct": 8.112366538820359
    },
    "over_30_days": {
      "n": 96470,
      "negative": 91920,
      "positive": 4550,
      "positive_pct": 4.716492173732767
    }
  }
}
```
Approximate geographic support and missingness:

```json
{
  "product_category_name": {
    "item_missing": 1603,
    "orders_any_missing": 1451
  },
  "product_weight_g": {
    "item_missing": 18,
    "orders_any_missing": 16
  },
  "product_length_cm": {
    "item_missing": 18,
    "orders_any_missing": 16
  },
  "product_height_cm": {
    "item_missing": 18,
    "orders_any_missing": 16
  },
  "product_width_cm": {
    "item_missing": 18,
    "orders_any_missing": 16
  },
  "distance_km": {
    "item_missing": 555,
    "orders_any_missing": 494
  }
}
```
