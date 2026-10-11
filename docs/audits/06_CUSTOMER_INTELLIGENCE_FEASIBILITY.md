# T-00 — 06 CUSTOMER INTELLIGENCE FEASIBILITY

**Descriptive intelligence: GO; traditional RFM clustering: CONDITIONAL GO; future CLV: NO-GO for current scope.** Customer IDs are anonymized marketplace identifiers, not a complete omnichannel customer ledger. 96,096 unique customers; 3.12% have multiple recorded orders. Frequency is nearly constant, so do not present K-Means as validated loyal-customer discovery.

RFM reference date is 2018-09-01, delivered orders only; monetary is summed recorded payment, not net revenue or profit. Raw all-status customer payment summaries are separately provided. No refunds, margins or cancellation payment reversals exist. Missing payment must remain explicitly unknown in production instead of blindly treated as zero. Apply log transforms/robust scaling on training data, compare descriptive recency/monetary bands to K-Means, assess silhouette, bootstrap stability and interpretable segment sizes. Consider seller reliability/value segmentation, category mix and order behavior, avoiding features that merely encode the proposed label.

Future windows use preceding 180 days of purchase activity and following 90 days of purchases at three cutoffs. A no-purchase label means no purchase observed in this extract, not no purchase anywhere. All horizons finish before conservative September coverage, but completeness is still an assumption. Window populations overlap; do not sum their counts as independent examples or random-split person/window rows. Amounts are future recorded payment proxies; they are not lifetime CLV. Positive labels are fewer than 300 per window with >99% zeros in two windows. Defer regression and repeat-purchase modeling; optional exploratory work needs grouped rolling windows, horizon maturity and PR metrics.

```json
{
  "activity_span_days": {
    "count": 96096,
    "iqr_outliers": 2740,
    "mean": 2.723023456698587,
    "negative": 0,
    "quantiles": {
      "0.0": 0.0,
      "0.01": 0.0,
      "0.25": 0.0,
      "0.5": 0.0,
      "0.75": 0.0,
      "0.95": 0.0,
      "0.99": 96.89463136574088,
      "1.0": 633.0841898148149
    },
    "std": 25.446011525220857,
    "zero": 93356
  },
  "cohort_sizes": {
    "2016-09": 4,
    "2016-10": 321,
    "2016-12": 1,
    "2017-01": 764,
    "2017-02": 1752,
    "2017-03": 2636,
    "2017-04": 2352,
    "2017-05": 3596,
    "2017-06": 3139,
    "2017-07": 3894,
    "2017-08": 4184,
    "2017-09": 4130,
    "2017-10": 4470,
    "2017-11": 7304,
    "2017-12": 5487,
    "2018-01": 7025,
    "2018-02": 6451,
    "2018-03": 6965,
    "2018-04": 6711,
    "2018-05": 6622,
    "2018-06": 5940,
    "2018-07": 6071,
    "2018-08": 6271,
    "2018-09": 5,
    "2018-10": 1
  },
  "delivered_customer_rfm": {
    "frequency": {
      "count": 93358,
      "iqr_outliers": 2801,
      "mean": 1.0334197390689603,
      "negative": 0,
      "quantiles": {
        "0.0": 1.0,
        "0.01": 1.0,
        "0.25": 1.0,
        "0.5": 1.0,
        "0.75": 1.0,
        "0.95": 1.0,
        "0.99": 2.0,
        "1.0": 15.0
      },
      "std": 0.2090974396818856,
      "zero": 0
    },
    "monetary": {
      "count": 93358,
      "iqr_outliers": 7402,
      "mean": 165.19700261359495,
      "negative": 0,
      "quantiles": {
        "0.0": 0.0,
        "0.01": 22.75,
        "0.25": 63.052499999999995,
        "0.5": 107.78,
        "0.75": 182.5575,
        "0.95": 469.61649999999935,
        "0.99": 1097.0616999999986,
        "1.0": 13664.08
      },
      "std": 226.31401249105576,
      "zero": 1
    },
    "recency": {
      "count": 93358,
      "iqr_outliers": 46,
      "mean": 239.84194391940963,
      "negative": 0,
      "quantiles": {
        "0.0": 2.3745717592592595,
        "0.01": 11.051993171296296,
        "0.25": 116.27598668981481,
        "0.5": 220.99152199074075,
        "0.75": 348.23246527777775,
        "0.95": 521.6205966435185,
        "0.99": 577.154925462963,
        "1.0": 715.4884490740741
      },
      "std": 152.5932648341026,
      "zero": 0
    }
  },
  "future_windows": [
    {
      "cutoff": "2017-10-01",
      "eligible_customers": 21178,
      "fully_inside_conservative_purchase_coverage": true,
      "future_buyers": 210,
      "future_order_count": 229,
      "future_recorded_payment_brl": {
        "count": 21178,
        "iqr_outliers": 210,
        "mean": 1.4878071583718953,
        "negative": 0,
        "quantiles": {
          "0.0": 0.0,
          "0.01": 0.0,
          "0.25": 0.0,
          "0.5": 0.0,
          "0.75": 0.0,
          "0.95": 0.0,
          "0.99": 0.0,
          "1.0": 1391.79
        },
        "std": 22.038445155682645,
        "zero": 20968
      },
      "horizon_end": "2017-12-30",
      "observation_start": "2017-04-04",
      "positive_pct": 0.991595051468505
    },
    {
      "cutoff": "2018-01-01",
      "eligible_customers": 29290,
      "fully_inside_conservative_purchase_coverage": true,
      "future_buyers": 233,
      "future_order_count": 253,
      "future_recorded_payment_brl": {
        "count": 29290,
        "iqr_outliers": 233,
        "mean": 1.2349743939911233,
        "negative": 0,
        "quantiles": {
          "0.0": 0.0,
          "0.01": 0.0,
          "0.25": 0.0,
          "0.5": 0.0,
          "0.75": 0.0,
          "0.95": 0.0,
          "0.99": 0.0,
          "1.0": 834.12
        },
        "std": 18.924224462734387,
        "zero": 29057
      },
      "horizon_end": "2018-04-01",
      "observation_start": "2017-07-05",
      "positive_pct": 0.7954933424376921
    },
    {
      "cutoff": "2018-04-01",
      "eligible_customers": 37866,
      "fully_inside_conservative_purchase_coverage": true,
      "future_buyers": 299,
      "future_order_count": 323,
      "future_recorded_payment_brl": {
        "count": 37866,
        "iqr_outliers": 299,
        "mean": 1.2790675011884012,
        "negative": 0,
        "quantiles": {
          "0.0": 0.0,
          "0.01": 0.0,
          "0.25": 0.0,
          "0.5": 0.0,
          "0.75": 0.0,
          "0.95": 0.0,
          "0.99": 0.0,
          "1.0": 1402.32
        },
        "std": 20.957228022580313,
        "zero": 37567
      },
      "horizon_end": "2018-06-30",
      "observation_start": "2017-10-03",
      "positive_pct": 0.7896265779327101
    }
  ],
  "geographic_state": {
    "AC": {
      "customers": 77,
      "orders": 81,
      "recorded_payment": 19680.62
    },
    "AL": {
      "customers": 401,
      "orders": 413,
      "recorded_payment": 96962.06
    },
    "AM": {
      "customers": 143,
      "orders": 148,
      "recorded_payment": 27966.93
    },
    "AP": {
      "customers": 67,
      "orders": 68,
      "recorded_payment": 16262.8
    },
    "BA": {
      "customers": 3277,
      "orders": 3380,
      "recorded_payment": 616645.82
    },
    "CE": {
      "customers": 1313,
      "orders": 1336,
      "recorded_payment": 279464.03
    },
    "DF": {
      "customers": 2075,
      "orders": 2140,
      "recorded_payment": 355141.08
    },
    "ES": {
      "customers": 1964,
      "orders": 2033,
      "recorded_payment": 325967.55
    },
    "GO": {
      "customers": 1952,
      "orders": 2020,
      "recorded_payment": 350092.31
    },
    "MA": {
      "customers": 726,
      "orders": 747,
      "recorded_payment": 152523.02
    },
    "MG": {
      "customers": 11259,
      "orders": 11635,
      "recorded_payment": 1872257.26
    },
    "MS": {
      "customers": 694,
      "orders": 715,
      "recorded_payment": 137534.84
    },
    "MT": {
      "customers": 876,
      "orders": 907,
      "recorded_payment": 187029.29
    },
    "PA": {
      "customers": 949,
      "orders": 975,
      "recorded_payment": 218295.85
    },
    "PB": {
      "customers": 519,
      "orders": 536,
      "recorded_payment": 141545.72
    },
    "PE": {
      "customers": 1609,
      "orders": 1652,
      "recorded_payment": 324850.44
    },
    "PI": {
      "customers": 482,
      "orders": 495,
      "recorded_payment": 108523.97
    },
    "PR": {
      "customers": 4882,
      "orders": 5045,
      "recorded_payment": 811156.38
    },
    "RJ": {
      "customers": 12384,
      "orders": 12852,
      "recorded_payment": 2144379.69
    },
    "RN": {
      "customers": 474,
      "orders": 485,
      "recorded_payment": 102718.13
    },
    "RO": {
      "customers": 240,
      "orders": 253,
      "recorded_payment": 60866.2
    },
    "RR": {
      "customers": 45,
      "orders": 46,
      "recorded_payment": 10064.62
    },
    "RS": {
      "customers": 5277,
      "orders": 5466,
      "recorded_payment": 890898.54
    },
    "SC": {
      "customers": 3534,
      "orders": 3637,
      "recorded_payment": 623086.43
    },
    "SE": {
      "customers": 342,
      "orders": 350,
      "recorded_payment": 75246.25
    },
    "SP": {
      "customers": 40302,
      "orders": 41746,
      "recorded_payment": 5998226.96
    },
    "TO": {
      "customers": 273,
      "orders": 280,
      "recorded_payment": 61485.33
    }
  },
  "orders_per_customer": {
    "count": 96096,
    "iqr_outliers": 2997,
    "mean": 1.0348089410589412,
    "negative": 0,
    "quantiles": {
      "0.0": 1.0,
      "0.01": 1.0,
      "0.25": 1.0,
      "0.5": 1.0,
      "0.75": 1.0,
      "0.95": 1.0,
      "0.99": 2.0,
      "1.0": 17.0
    },
    "std": 0.21438375479444627,
    "zero": 0
  },
  "recency_anchor": "2018-09-01",
  "recorded_payment_per_customer": {
    "count": 96096,
    "iqr_outliers": 7656,
    "mean": 166.5924920912421,
    "negative": 0,
    "quantiles": {
      "0.0": 0.0,
      "0.01": 22.77,
      "0.25": 63.12,
      "0.5": 108.0,
      "0.75": 183.53,
      "0.95": 476.15,
      "0.99": 1122.4635000000007,
      "1.0": 13664.08
    },
    "std": 231.4283317084283,
    "zero": 3
  },
  "repeat_customers": 2997,
  "repeat_pct": 3.1187562437562435,
  "unique_customers": 96096
}
```
