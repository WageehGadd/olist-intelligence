# T-00 — 05 REVIEW TARGET FEASIBILITY

**CONDITIONAL GO — Advanced.** Low-score target = unanimous observed score 1–2 versus 3–5; 3-star treatment requires stakeholder sensitivity analysis. This is low-rating risk, not verified emotional sentiment. Missing reviews have no label. The 202 conflicting-score orders are excluded rather than arbitrarily averaging or selecting a favorable score.

Eligibility by scenario: purchase/handoff/delivery timestamp present and at/after purchase, unanimous label, earliest review creation strictly after prediction event. Post-delivery excludes reviews generated before/on exact delivery time and includes records with a delivery timestamp regardless of final status; a stricter status-and-chronology sensitivity is required before production. Carrier counts likewise enforce stage ≥ purchase but do not enforce approval-to-carrier consistency; use stricter delivery-stage chronology for implementation. Earliest review creation is a conservative boundary; answer is when the rating is actually submitted.

Purchase uses pre-outcome cart/catalog/location/calendar features. Handoff can add elapsed fulfillment. Post-delivery can add known lateness/duration only while review is still unavailable. Never use review text, score, answer date, final status or later outcomes to predict a future review. Missing-response selection and delivered population shifts are major risks: low-rating prevalence changes substantially across scenarios. Lightweight purchase logistic evidence shows modest lift and low recall at 0.5; no claim of commercially useful prediction follows. Benchmark dummy/logistic/trees and tune a threshold on validation only. Chronological maturity rules and order grouping apply.

```json
{
  "carrier": {
    "n": 96285,
    "negative": 83511,
    "positive": 12774,
    "positive_pct": 13.2668639975074
  },
  "post_delivery": {
    "n": 87434,
    "negative": 79273,
    "positive": 8161,
    "positive_pct": 9.333897568451633
  },
  "purchase": {
    "n": 98400,
    "negative": 84018,
    "positive": 14382,
    "positive_pct": 14.615853658536585
  },
  "score_by_status_rows": {
    "1": {
      "approved": 1,
      "canceled": 422,
      "created": 2,
      "delivered": 9406,
      "invoiced": 230,
      "processing": 256,
      "shipped": 644,
      "unavailable": 463
    },
    "2": {
      "approved": 0,
      "canceled": 44,
      "created": 0,
      "delivered": 2941,
      "invoiced": 26,
      "processing": 18,
      "shipped": 79,
      "unavailable": 43
    },
    "3": {
      "approved": 0,
      "canceled": 48,
      "created": 0,
      "delivered": 7961,
      "invoiced": 16,
      "processing": 9,
      "shipped": 110,
      "unavailable": 35
    },
    "4": {
      "approved": 1,
      "canceled": 26,
      "created": 0,
      "delivered": 18987,
      "invoiced": 15,
      "processing": 6,
      "shipped": 87,
      "unavailable": 20
    },
    "5": {
      "approved": 0,
      "canceled": 69,
      "created": 1,
      "delivered": 57066,
      "invoiced": 26,
      "processing": 7,
      "shipped": 123,
      "unavailable": 36
    }
  },
  "score_rows": {
    "1": 11424,
    "2": 3151,
    "3": 8179,
    "4": 19142,
    "5": 57328
  },
  "unanimous_orders": {
    "n": 98471,
    "negative": 84042,
    "positive": 14429,
    "positive_pct": 14.653045058951367
  }
}
```
