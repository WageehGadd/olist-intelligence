# T-00 — 09 BASELINE EXPERIMENTS

Three bounded experiments were executed: dummy versus logistic for purchase-time delivery and review risk, and dummy versus TF-IDF logistic for post-review NLP. Fixed seed 42, no search, no model artifact. Numeric median imputation/scaling and categorical one-hot are fit on train only; text vocabulary/IDF are fit on train only. No review text enters pre-review tasks. The tabular input fields are enumerated below; final payments were deliberately excluded.

Chronology: train before 2018-01-01, validation 2018-01-01 to before 2018-04-01, test 2018-04-01 to before 2018-09-01. Labels must be known before each partition end: delivery timestamp or latest review answer. Partitioning uses purchase time for tabular tasks and answer time for NLP. No tuning used test data. NLP excludes every globally repeated normalized message and every multi-review order before splitting; this is a conservative corpus eligibility rule using full-corpus duplicate detection, not train-fitted vocabulary. It reduces template leakage but uses later-corpus information and changes population; a prospective held-out evaluation should freeze dedup rules and report novel/repeated-text metrics separately. Customer identity overlap is possible across periods; IDs are excluded but grouped-customer sensitivity remains unrun.

Outcome maturity excludes slow deliveries at boundaries and can inflate apparent performance. Tabular sample availability at purchase is assumed; these are diagnostics, not deployment validation. AP is average precision rather than trapezoidal PR-AUC. Top-K sorts ties stably; dummy top-K capture is an incidental ordering result, not actionable ranking. Threshold is fixed 0.5, not optimized. No calibration fitting, confidence intervals, full rolling folds or fairness evaluation was performed. Delivery F1 is zero at 0.5 despite ranking lift; validation-only threshold/calibration work is mandatory. NLP baseline strength makes DL scientifically interesting only as a fair comparison, not an assumed improvement.

```json
{
  "delivery": {
    "scenario": "purchase-time retrospective proxy; static catalog and cart features assumed available",
    "features": [
      "item_count",
      "item_price",
      "freight",
      "seller_count",
      "product_count",
      "purchase_hour",
      "purchase_weekday",
      "purchase_month",
      "promise_days",
      "customer_state"
    ],
    "label_available_before_partition_end": true,
    "split_counts": {
      "train": 41197,
      "validation": 16782,
      "test": 32092
    },
    "metrics": {
      "validation": {
        "logistic": {
          "n": 16782,
          "positive": 1158,
          "average_precision": 0.12081505754771951,
          "roc_auc": 0.6423470722160761,
          "precision_05": 0.0,
          "recall_05": 0.0,
          "f1_05": 0.0,
          "brier": 0.06419577626981149,
          "top_10pct_recall": 0.229706390328152
        },
        "dummy": {
          "n": 16782,
          "positive": 1158,
          "average_precision": 0.06900250268144441,
          "roc_auc": 0.5,
          "precision_05": 0.0,
          "recall_05": 0.0,
          "f1_05": 0.0,
          "brier": 0.0649254807857694,
          "top_10pct_recall": 0.09499136442141623
        }
      },
      "test": {
        "logistic": {
          "n": 32092,
          "positive": 1363,
          "average_precision": 0.09865922753002439,
          "roc_auc": 0.726089409591963,
          "precision_05": 0.0,
          "recall_05": 0.0,
          "f1_05": 0.0,
          "brier": 0.03969576691175561,
          "top_10pct_recall": 0.2839325018341893
        },
        "dummy": {
          "n": 32092,
          "positive": 1363,
          "average_precision": 0.042471644023432634,
          "roc_auc": 0.5,
          "precision_05": 0.0,
          "recall_05": 0.0,
          "f1_05": 0.0,
          "brier": 0.04066794132728142,
          "top_10pct_recall": 0.10051357300073367
        }
      }
    }
  },
  "review": {
    "scenario": "purchase-time retrospective proxy; static catalog and cart features assumed available",
    "features": [
      "item_count",
      "item_price",
      "freight",
      "seller_count",
      "product_count",
      "purchase_hour",
      "purchase_weekday",
      "purchase_month",
      "promise_days",
      "customer_state"
    ],
    "label_available_before_partition_end": true,
    "split_counts": {
      "train": 41940,
      "validation": 16867,
      "test": 31879
    },
    "metrics": {
      "validation": {
        "logistic": {
          "n": 16867,
          "positive": 2931,
          "average_precision": 0.2866201752104033,
          "roc_auc": 0.621308280755893,
          "precision_05": 0.6944444444444444,
          "recall_05": 0.008529512111907198,
          "f1_05": 0.016852039096730706,
          "brier": 0.14061822468690113,
          "top_10pct_recall": 0.18764926646195837
        },
        "dummy": {
          "n": 16867,
          "positive": 2931,
          "average_precision": 0.17377126934250312,
          "roc_auc": 0.5,
          "precision_05": 0.0,
          "recall_05": 0.0,
          "f1_05": 0.0,
          "brier": 0.14477501819055152,
          "top_10pct_recall": 0.0992835209825998
        }
      },
      "test": {
        "logistic": {
          "n": 31879,
          "positive": 3679,
          "average_precision": 0.18845977522995852,
          "roc_auc": 0.5832095234790521,
          "precision_05": 0.4956521739130435,
          "recall_05": 0.015493340581679805,
          "f1_05": 0.030047443331576173,
          "brier": 0.10002670084910349,
          "top_10pct_recall": 0.19434628975265017
        },
        "dummy": {
          "n": 31879,
          "positive": 3679,
          "average_precision": 0.11540512563129333,
          "roc_auc": 0.5,
          "precision_05": 0.0,
          "recall_05": 0.0,
          "f1_05": 0.0,
          "brier": 0.10264952534032934,
          "top_10pct_recall": 0.09486273443870617
        }
      }
    }
  },
  "nlp": {
    "task": "post-review low-score detection, 1–2 versus 3–5; rating proxy not gold sentiment",
    "split_counts": {
      "train": 14412,
      "validation": 6987,
      "test": 12100
    },
    "excluded_all_repeated_text_and_multireview_orders": true,
    "metrics": {
      "validation": {
        "tfidf_logistic": {
          "n": 6987,
          "positive": 2473,
          "average_precision": 0.8746882428906003,
          "roc_auc": 0.939928901610141,
          "precision_05": 0.8246644295302014,
          "recall_05": 0.7949858471492115,
          "f1_05": 0.8095532221535927,
          "brier": 0.09530982380159614,
          "top_10pct_recall": 0.26283865750101093
        },
        "dummy": {
          "n": 6987,
          "positive": 2473,
          "average_precision": 0.3539430370688421,
          "roc_auc": 0.5,
          "precision_05": 0.0,
          "recall_05": 0.0,
          "f1_05": 0.0,
          "brier": 0.23426250167546328,
          "top_10pct_recall": 0.09947432268499798
        }
      },
      "test": {
        "tfidf_logistic": {
          "n": 12100,
          "positive": 3447,
          "average_precision": 0.8495874700370118,
          "roc_auc": 0.9460442424254005,
          "precision_05": 0.7956860395446375,
          "recall_05": 0.7705250942848854,
          "f1_05": 0.7829034635224761,
          "brier": 0.08546388794263977,
          "top_10pct_recall": 0.31940818102698
        },
        "dummy": {
          "n": 12100,
          "positive": 3447,
          "average_precision": 0.28487603305785125,
          "roc_auc": 0.5,
          "precision_05": 0.0,
          "recall_05": 0.0,
          "f1_05": 0.0,
          "brier": 0.2037545536089931,
          "top_10pct_recall": 0.10414853495793444
        }
      }
    }
  }
}
```
