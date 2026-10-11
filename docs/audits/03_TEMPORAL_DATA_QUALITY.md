# T-00 — 03 TEMPORAL DATA QUALITY

Durations below are days, computed only when both timestamps exist. Negative durations are reported, not silently clipped. There are 1,359 carrier handoffs before approval and 23 deliveries before carrier handoff. Purchase-to-review creation is negative for 74 orders. Same-day midnight review creation can precede actual delivery hours; compare both calendar and exact times. Creation is not answer time.

Sparse early and final months are unsuitable standalone holdouts. September 2018 has 16 orders and October has 4, none delivered. Use January 2017–August 2018 for primary chronological evaluation, with sensitivity around August maturity. Missing outcomes are unknown, not on-time or good-rating labels. Canceled/unavailable are competing outcomes; shipped/processing could be unresolved or omitted outcomes. No extraction timestamp establishes definitive follow-up, and maximum observed event date does not prove complete observation.

Delivered-only evaluation estimates risk conditional on eventual delivery; it omits failures and can bias operational conclusions. Outcome-maturity purging also removes long-duration outcomes near boundaries and can bias rate estimates. The baseline reports below are therefore conditional diagnostics; future validation should use fixed follow-up, purge/embargo boundaries and compare monthly excluded versus retained cohorts.

```json
{
  "approval_to_carrier": {
    "count": 97644,
    "iqr_outliers": 5660,
    "mean": 2.8050381811449983,
    "negative": 1359,
    "quantiles": {
      "0.0": -171.21900462962964,
      "0.01": -0.06948229166666665,
      "0.25": 0.8755092592592593,
      "0.5": 1.818396990740741,
      "0.75": 3.5804687499999996,
      "0.95": 8.097952546296293,
      "0.99": 17.15094618055554,
      "1.0": 125.76256944444444
    },
    "std": 3.54942704957967,
    "zero": 0
  },
  "carrier_to_delivery": {
    "count": 96475,
    "iqr_outliers": 5071,
    "mean": 9.330546923017861,
    "negative": 23,
    "quantiles": {
      "0.0": -16.096168981481483,
      "0.01": 0.8119300925925925,
      "0.25": 4.099947916666666,
      "0.5": 7.099768518518519,
      "0.75": 12.029114583333333,
      "0.95": 24.209711805555557,
      "0.99": 40.9830469907407,
      "1.0": 205.19097222222223
    },
    "std": 8.760121783191707,
    "zero": 9
  },
  "estimate_to_delivery": {
    "count": 96476,
    "iqr_outliers": 4875,
    "mean": -11.179119879819465,
    "negative": 88649,
    "quantiles": {
      "0.0": -146.0161226851852,
      "0.01": -35.15423900462963,
      "0.25": -16.244383680555558,
      "0.5": -11.948940972222221,
      "0.75": -6.390000000000001,
      "0.95": 3.8184577546296294,
      "0.99": 18.939305555555556,
      "1.0": 188.97508101851852
    },
    "std": 10.18611321741384,
    "zero": 0
  },
  "max_delivery": "2018-10-17 13:22:46",
  "max_purchase": "2018-10-17 17:30:18",
  "max_review_answer": "2018-10-29 12:27:35",
  "missing_timestamps": {
    "order_approved_at": 160,
    "order_delivered_carrier_date": 1783,
    "order_delivered_customer_date": 2965,
    "order_estimated_delivery_date": 0,
    "order_purchase_timestamp": 0,
    "review_answer": 768,
    "review_creation": 768
  },
  "monthly": [
    {
      "actual_delivery_known": 1,
      "delivered": 1,
      "order_purchase_timestamp": "2016-09",
      "orders": 4
    },
    {
      "actual_delivery_known": 270,
      "delivered": 265,
      "order_purchase_timestamp": "2016-10",
      "orders": 324
    },
    {
      "actual_delivery_known": 1,
      "delivered": 1,
      "order_purchase_timestamp": "2016-12",
      "orders": 1
    },
    {
      "actual_delivery_known": 750,
      "delivered": 750,
      "order_purchase_timestamp": "2017-01",
      "orders": 800
    },
    {
      "actual_delivery_known": 1653,
      "delivered": 1653,
      "order_purchase_timestamp": "2017-02",
      "orders": 1780
    },
    {
      "actual_delivery_known": 2546,
      "delivered": 2546,
      "order_purchase_timestamp": "2017-03",
      "orders": 2682
    },
    {
      "actual_delivery_known": 2303,
      "delivered": 2303,
      "order_purchase_timestamp": "2017-04",
      "orders": 2404
    },
    {
      "actual_delivery_known": 3545,
      "delivered": 3546,
      "order_purchase_timestamp": "2017-05",
      "orders": 3700
    },
    {
      "actual_delivery_known": 3135,
      "delivered": 3135,
      "order_purchase_timestamp": "2017-06",
      "orders": 3245
    },
    {
      "actual_delivery_known": 3872,
      "delivered": 3872,
      "order_purchase_timestamp": "2017-07",
      "orders": 4026
    },
    {
      "actual_delivery_known": 4193,
      "delivered": 4193,
      "order_purchase_timestamp": "2017-08",
      "orders": 4331
    },
    {
      "actual_delivery_known": 4150,
      "delivered": 4150,
      "order_purchase_timestamp": "2017-09",
      "orders": 4285
    },
    {
      "actual_delivery_known": 4478,
      "delivered": 4478,
      "order_purchase_timestamp": "2017-10",
      "orders": 4631
    },
    {
      "actual_delivery_known": 7288,
      "delivered": 7289,
      "order_purchase_timestamp": "2017-11",
      "orders": 7544
    },
    {
      "actual_delivery_known": 5513,
      "delivered": 5513,
      "order_purchase_timestamp": "2017-12",
      "orders": 5673
    },
    {
      "actual_delivery_known": 7069,
      "delivered": 7069,
      "order_purchase_timestamp": "2018-01",
      "orders": 7269
    },
    {
      "actual_delivery_known": 6556,
      "delivered": 6555,
      "order_purchase_timestamp": "2018-02",
      "orders": 6728
    },
    {
      "actual_delivery_known": 7003,
      "delivered": 7003,
      "order_purchase_timestamp": "2018-03",
      "orders": 7211
    },
    {
      "actual_delivery_known": 6798,
      "delivered": 6798,
      "order_purchase_timestamp": "2018-04",
      "orders": 6939
    },
    {
      "actual_delivery_known": 6749,
      "delivered": 6749,
      "order_purchase_timestamp": "2018-05",
      "orders": 6873
    },
    {
      "actual_delivery_known": 6096,
      "delivered": 6099,
      "order_purchase_timestamp": "2018-06",
      "orders": 6167
    },
    {
      "actual_delivery_known": 6156,
      "delivered": 6159,
      "order_purchase_timestamp": "2018-07",
      "orders": 6292
    },
    {
      "actual_delivery_known": 6351,
      "delivered": 6351,
      "order_purchase_timestamp": "2018-08",
      "orders": 6512
    },
    {
      "actual_delivery_known": 0,
      "delivered": 0,
      "order_purchase_timestamp": "2018-09",
      "orders": 16
    },
    {
      "actual_delivery_known": 0,
      "delivered": 0,
      "order_purchase_timestamp": "2018-10",
      "orders": 4
    }
  ],
  "order_status": {
    "approved": 2,
    "canceled": 625,
    "created": 5,
    "delivered": 96478,
    "invoiced": 314,
    "processing": 301,
    "shipped": 1107,
    "unavailable": 609
  },
  "purchase_to_approval": {
    "count": 99281,
    "iqr_outliers": 9141,
    "mean": 0.4341289292466538,
    "negative": 0,
    "quantiles": {
      "0.0": 0.0,
      "0.01": 0.0,
      "0.25": 0.008958333333333334,
      "0.5": 0.014305555555555556,
      "0.75": 0.6075347222222223,
      "0.95": 2.0193171296296297,
      "0.99": 3.756937499999999,
      "1.0": 187.88252314814815
    },
    "std": 1.0849168182679145,
    "zero": 1296
  },
  "purchase_to_delivery": {
    "count": 96476,
    "iqr_outliers": 4899,
    "mean": 12.558702304032053,
    "negative": 0,
    "quantiles": {
      "0.0": 0.5334143518518518,
      "0.01": 1.8252025462962962,
      "0.25": 6.766403356481481,
      "0.5": 10.21775462962963,
      "0.75": 15.720326967592593,
      "0.95": 29.276015625,
      "0.99": 46.04991319444444,
      "1.0": 209.6286111111111
    },
    "std": 9.546529874135482,
    "zero": 0
  },
  "purchase_to_review": {
    "count": 98673,
    "iqr_outliers": 3170,
    "mean": 12.648028803800507,
    "negative": 74,
    "quantiles": {
      "0.0": -111.8444675925926,
      "0.01": 2.085572685185185,
      "0.25": 7.15619212962963,
      "0.5": 10.650844907407407,
      "0.75": 16.448425925925925,
      "0.95": 28.04020138888886,
      "0.99": 36.44939537037036,
      "1.0": 147.89524305555557
    },
    "std": 7.895970843842978,
    "zero": 0
  },
  "review_before_delivery_orders": 8282,
  "review_row_creation_to_answer": {
    "count": 99224,
    "iqr_outliers": 6305,
    "mean": 3.1489933993110615,
    "negative": 0,
    "quantiles": {
      "0.0": 0.08922453703703703,
      "0.01": 0.37780358796296293,
      "0.25": 1.0048697916666667,
      "0.5": 1.6749479166666665,
      "0.75": 3.1035648148148147,
      "0.95": 6.972189814814813,
      "0.99": 22.07084884259267,
      "1.0": 518.699212962963
    },
    "std": 9.890049282711049,
    "zero": 0
  },
  "review_to_answer": {
    "count": 98673,
    "iqr_outliers": 6469,
    "mean": 3.1796361819727412,
    "negative": 0,
    "quantiles": {
      "0.0": 0.08922453703703703,
      "0.01": 0.3782162037037037,
      "0.25": 1.0060069444444444,
      "0.5": 1.6825462962962963,
      "0.75": 3.116134259259259,
      "0.95": 7.10642592592592,
      "0.99": 22.613657407407402,
      "1.0": 518.699212962963
    },
    "std": 9.953233823680865,
    "zero": 0
  },
  "status_actual_delivery": {
    "False": {
      "approved": 2,
      "canceled": 619,
      "created": 5,
      "delivered": 8,
      "invoiced": 314,
      "processing": 301,
      "shipped": 1107,
      "unavailable": 609
    },
    "True": {
      "approved": 0,
      "canceled": 6,
      "created": 0,
      "delivered": 96470,
      "invoiced": 0,
      "processing": 0,
      "shipped": 0,
      "unavailable": 0
    }
  }
}
```
